import asyncio
import os
import requests
from sqlalchemy.ext.asyncio import AsyncSession
from database import AsyncSessionLocal, engine, Base
from models import Claim
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

GOOGLE_FACT_CHECK_API_KEY = os.getenv("GOOGLE_FACT_CHECK_API_KEY")
API_URL = "https://factchecktools.googleapis.com/v1alpha1/claims:search"

async def fetch_claims(query="misinformation", max_age_days=30):
    if not GOOGLE_FACT_CHECK_API_KEY:
        print("❌ GOOGLE_FACT_CHECK_API_KEY not set.")
        return []

    params = {
        "key": GOOGLE_FACT_CHECK_API_KEY,
        "query": query,
        "pageSize": 50,  # User requested 50
        "maxAgeDays": max_age_days
    }
    
    try:
        # User requested timer: if 50 not found in time, use what we got (or fail gracefully)
        response = requests.get(API_URL, params=params, timeout=5) # 5 second timeout
        
        if response.status_code != 200:
            print(f"❌ Error fetching claims: {response.text}")
            return []
            
        data = response.json()
        return data.get("claims", [])
        
    except requests.exceptions.Timeout:
        print("⚠️ Google API Timed out (5s). Using whatever data we have.")
        return []
    except Exception as e:
        print(f"❌ API Request Failed: {e}")
        return []

def get_demo_claims():
    """Fallback claims for demo mode if no API key is present."""
    print("⚠️ No Google API Key found. Using DEMO DATASET.")
    return [
        {
            "text": "The Earth is an oblate spheroid, not flat. Satellite imagery and physics prove this.",
            "claimReview": [{"url": "https://www.nasa.gov/topics/earth/index.html", "title": "NASA Earth Facts"}],
            "source": "NASA"
        },
        {
            "text": "Fact Check: The Earth is not flat. Extensive evidence from space exploration and gravity confirms its round shape.",
            "claimReview": [{"url": "https://www.factcheck.org/2018/05/the-earth-is-not-flat/", "title": "FactCheck.org"}],
            "source": "FactCheck.org"
        },
        {
            "text": "There is no evidence that 5G networks cause COVID-19. Viruses cannot travel on radio waves.",
            "claimReview": [{"url": "https://www.who.int/emergencies/diseases/novel-coronavirus-2019/advice-for-public/myth-busters", "title": "WHO Myth Busters"}],
            "source": "WHO"
        },
        {
            "text": "Vaccines differ from gene therapy and do not alter human DNA. mRNA vaccines teach cells to make protein.",
            "claimReview": [{"url": "https://www.cdc.gov/coronavirus/2019-ncov/vaccines/facts.html", "title": "CDC Vaccine Facts"}],
            "source": "CDC"
        },
        {
            "text": "Climate change is real and primarily caused by human activities like burning fossil fuels.",
            "claimReview": [{"url": "https://climate.nasa.gov/evidence/", "title": "NASA Climate Evidence"}],
            "source": "NASA"
        },
        # Expanded Earth is Flat Claims
        {
            "text": "The curvature of the Earth is visible from high altitudes and space. Photographs from the ISS clearly show a round Earth.",
            "claimReview": [{"url": "https://www.nasa.gov/audience/forstudents/5-8/features/nasa-knows/what-is-earth-58.html", "title": "NASA: What is Earth?"}],
            "source": "NASA"
        },
        {
            "text": "Ships disappear bottom-first over the horizon because the Earth is curved.",
            "claimReview": [{"url": "https://www.britannica.com/demystified/is-the-earth-round", "title": "Britannica: Is Earth Round?"}],
            "source": "Britannica"
        },
        {
            "text": "Gravity pulls matter toward the center of mass, forming spheres. A flat Earth would be scientifically impossible.",
            "claimReview": [{"url": "https://www.scientificamerican.com/article/what-would-happen-if-the-earth-were-actually-flat/", "title": "Scientific American: Flat Earth Physics"}],
            "source": "Scientific American"
        },
        {
            "text": "Historical circumnavigation by Magellan and modern air travel routes prove the Earth is a sphere.",
            "claimReview": [{"url": "https://www.nationalgeographic.org/encyclopedia/circumnavigation/", "title": "National Geographic: Circumnavigation"}],
            "source": "National Geographic"
        },
        {
            "text": "Lunar eclipses cast a round shadow on the Moon, which is only possible if the Earth is round.",
            "claimReview": [{"url": "https://www.space.com/15684-lunar-eclipses.html", "title": "Space.com: Lunar Eclipses"}],
            "source": "Space.com"
        }
    ]

async def save_claims(claims):
    # 1. Save to Postgres
    async with AsyncSessionLocal() as session:
        count = 0
        accepted_claims = []
        for item in claims:
            text = item.get("text")
            claim_review = item.get("claimReview", [])
            url = claim_review[0].get("url") if claim_review else None
            
            if text:
                new_claim = Claim(
                    content=text,
                    source_url=url,
                    status="pending"
                )
                session.add(new_claim)
                count += 1
                accepted_claims.append({"text": text, "url": url, "source": item.get("source", "Google FactCheck")})
        
        await session.commit()
        print(f"✅ Saved {count} claims to Postgres.")

    # 2. Sync to ChromaDB
    try:
        import chromadb
        from sentence_transformers import SentenceTransformer
        
        host = os.getenv("CHROMA_HOST", "chromadb")
        port = int(os.getenv("CHROMA_PORT", 8000))
        
        print(f"Connecting to ChromaDB at {host}:{port}...")
        client = chromadb.HttpClient(host=host, port=port)
        
        # FIX: Ensure collection exists before upserting
        try:
             # Try to get existing one
            collection = client.get_or_create_collection("claims")
            print(f"DEBUG: Collection 'claims' retrieved/created. Count: {collection.count()}")
        except Exception as e:
            print(f"WARN: Could not get/create collection: {e}. Trying simple create_collection...")
            # Fallback for some chroma versions
            collection = client.create_collection("claims")

        print("Loading embedding model for ingestion...")
        model = SentenceTransformer('all-MiniLM-L6-v2')
        
        if accepted_claims:
            documents = [c["text"] for c in accepted_claims]
            embeddings = model.encode(documents).tolist()
            metadatas = [{"source_url": c["url"], "source": c["source"]} for c in accepted_claims]
            ids = [f"claim_{hash(c['text'])}" for c in accepted_claims]
            
            collection.upsert(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas
            )
            print(f"✅ Synced {len(accepted_claims)} claims to ChromaDB.")
            
    except Exception as e:
        import traceback
        print(f"❌ Failed to sync to ChromaDB: {e}")
        traceback.print_exc()

async def main():
    print("Starting ingestion...")
    # Ensure tables exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    topics = ["misinformation", "ukraine war", "gaza", "climate change", "vaccines", "economy"]
    
    all_claims = []
    if not GOOGLE_FACT_CHECK_API_KEY:
         print("⚠️ No API Key. Using Demo Data.")
         all_claims = get_demo_claims()
    else:
        for topic in topics:
            print(f"Fetching claims for topic: {topic}...")
            claims = await fetch_claims(query=topic)
            if claims:
                all_claims.extend(claims)
            
    if not all_claims and not GOOGLE_FACT_CHECK_API_KEY:
        # Fallback only if absolutely nothing found
        all_claims = get_demo_claims()
        
    if all_claims:
        await save_claims(all_claims)
    else:
        print("❌ Still no claims found after fallback.")

if __name__ == "__main__":
    asyncio.run(main())
