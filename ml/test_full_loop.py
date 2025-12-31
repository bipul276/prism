import asyncio
import os
import sys

# Ensure we can import from ml.
sys.path.append(os.getcwd())

from ml.core.news_fetcher import NewsFetcher
from ml.ingest import save_claims
from ml.core.rag import EvidenceRetriever

async def test():
    query = "russia attacked ukraine"
    
    # 1. Fetch
    print(f"\n--- 1. FETCHING '{query}' ---")
    nf = NewsFetcher()
    news = nf.search_news(query)
    print(f"✅ Found {len(news)} items.")
    if not news: 
        print("❌ Fetch failed.")
        return
        
    print(f"DEBUG: First item: {news[0]}")


    # 2. Save
    print(f"\n--- 2. SAVING {len(news)} items to ChromaDB ---")
    try:
        await save_claims(news)
    except Exception as e:
        print(f"❌ Save failed: {e}")
        return
    
    print("Sleeping 5s to allow indexing...")
    import time
    time.sleep(5)
    
    # 3. Retrieve
    print("\n--- 3. RETRIEVING from ChromaDB ---")
    try:
        retriever = EvidenceRetriever()
        results = retriever.retrieve(query)
        print(f"✅ Retrieved {len(results)} raw candidates.")
        
        print("\n--- SCORES (Lower is Better) ---")
        for r in results:
            pass_threshold = r['score'] < 1.3
            icon = "✅" if pass_threshold else "❌"
            print(f"{icon} [{r['score']:.4f}] {r['text'][:60]}...")
            
    except Exception as e:
        print(f"❌ Retrieve failed: {e}")

if __name__ == "__main__":
    asyncio.run(test())
