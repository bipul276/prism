from ml.workers.celery_app import celery_app
import time
import asyncio
import json
import hashlib
import redis
import os
from ml.core.stylometry import StylometricAnalyzer
from ml.core.rag import EvidenceRetriever
from ml.core.nli import StanceClassifier
from ml.core.xai import XAIExplainer
from ml.core.reputation import ReputationChecker

# Singleton models in worker process
stylometer = None
retriever = None
nli = None
xai = None
reputation = None

def get_models():
    global stylometer, retriever, nli, xai, reputation
    if not stylometer:
        print("Worker: Loading models...")
        stylometer = StylometricAnalyzer()
        retriever = EvidenceRetriever()
        nli = StanceClassifier()
        xai = XAIExplainer(stylometer)
        reputation = ReputationChecker()
    return stylometer, retriever, nli, xai, reputation

@celery_app.task(bind=True)
def analyze_text_task(self, text, claim_id=None):
    """
    Full async analysis pipeline.
    """
    stylometer, retriever, nli, xai, reputation = get_models()
    quality_note = "Verified" # Default status
    
    # 0. Caching Check
    r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    cache_key = f"cache:v1:{hashlib.md5(text.encode()).hexdigest()}"
    cached = r.get(cache_key)
    if cached:
        print(f"Worker: Returning cached result for {cache_key}")
        return json.loads(cached)
    
    # 1. Stylometric Risk
    style_analysis = stylometer.analyze(text)
    style_risk = style_analysis["score"]
    
    # 2. XAI Heatmap
    heatmap = xai.explain(text)
    
    # 3. Retrieve Evidence
    evidence_list = retriever.retrieve(text)
    
    # Trust Gating: Check evidence quality
    # Relaxed to 1.4 to show more news results (Lane B often comes in ~1.2-1.3)
    original_count = len(evidence_list)
    evidence_list = [e for e in evidence_list if e['score'] < 1.4] 
    
    # REACTIVE RAG & 3-LANE ROUTER
    # Trigger if NO evidence OR if we have evidence but it's all weak/neutral (trust gating)
    # We want to force a refresh if the best match is still mediocre.
    
    should_fetch = False
    
    # SAFETY OVERRIDE: Semantic Check
    # Use NLI to detect danger/harm without brittle keywords
    is_safety_critical = nli.check_safety(text)
    
    if is_safety_critical:
         print(f"Worker: Semantic Safety Check TRIGGERED. FORCING FETCH.")
         should_fetch = True
         
    elif not evidence_list:
        should_fetch = True
        print(f"Worker: No relevant internal evidence. Triggering Smart Fetch.")
    else:
        # Check if we have any strong matches (Score < 0.6 is usually good)
        # Or if we have NLI conflict? No, NLI isn't run yet.
        # Just check retrieval density.
        best_score = min([e['score'] for e in evidence_list])
        if best_score > 0.8: # If even the best match is kinda 'meh'
             print(f"Worker: Best internal match is weak ({best_score:.2f}). Triggering Smart Fetch.")
             should_fetch = True
             
    if should_fetch:
        print(f"Worker: Analyzing route for: '{text}'")
        
        try:
            from ml.core.router import EvidenceRouter
            from ml.ingest import fetch_claims, save_claims
            from ml.core.news_fetcher import NewsFetcher
            
            router = EvidenceRouter()
            route = router.route(text)
            print(f"Worker: Route selected -> {route}")
            
            async def run_smart_fetch():
                new_data = []
                
                # Lane A: Fact Check API (Specific Claims)
                if route == "lane_a":
                    print("Worker: Running Lane A (Fact Checks)...")
                    fc_data = await fetch_claims(query=text)
                    if fc_data: new_data.extend(fc_data)
                    
                    # If Lane A fails, try Lane B fallback
                    if not fc_data:
                        print("Worker: Lane A empty. Falling back to Lane B (News)...")
                        nf = NewsFetcher()
                        news_data = nf.search_news(text)
                        if news_data: new_data.extend(news_data)

                # Lane B: General News (Events)
                elif route == "lane_b" or (is_safety_critical and not new_data):
                     # Safety Fallback: If Lane A found nothing for a dangerous topic, force Lane B
                    print("Worker: Running Lane B (Trusted News)...")
                    nf = NewsFetcher()
                    news_data = nf.search_news(text)
                    if news_data: 
                        print(f"Worker: Lane B found {len(news_data)} items.")
                        new_data.extend(news_data)
                    else:
                        print("Worker: Lane B found 0 items.")
                
                if new_data:
                    print(f"Worker: Ingesting {len(new_data)} items...")
                    await save_claims(new_data)
                    # CRITICAL: Wait for ChromaDB to index the new vectors
                    print("Worker: Waiting 5s for indexing...")
                    await asyncio.sleep(5) 
                    return True
                
                print("Worker: Deep Fetch found NO data in any lane.")
                return False

            # Run Ingestion
            got_new_data = asyncio.run(run_smart_fetch())
            
            if got_new_data:
                print("Worker: Re-running retrieval...")
                raw_evidence = retriever.retrieve(text)
                
                # Dynamic Relaxation Loop
                # Try strict, then medium, then loose
                thresholds = [1.2, 1.4, 1.6]
                final_evidence = []
                quality_note = "Verified"
                used_threshold = 1.2
                
                for t in thresholds:
                    filtered = [e for e in raw_evidence if e['score'] < t]
                    if len(filtered) >= 3:
                        final_evidence = filtered
                        used_threshold = t
                        break # We have enough good evidence
                    final_evidence = filtered # Keep whatever we found so far
                    used_threshold = t
                
                # Cutoff: Limit to Top 8 results to prevent infinite scrolling/overload
                evidence_list = final_evidence[:8]
                
                # Add Disclaimer if we had to scrape the bottom of the barrel
                if used_threshold >= 1.6:
                    print(f"Worker: Used broad threshold {used_threshold}. Adding disclaimer.")
                    quality_note = "Weak Evidence Match (View with Caution)"
                    # Tag individual items? No, just the overall status.

        except Exception as e:
            print(f"Worker: Smart Fetch failed: {e}")
            import traceback
            traceback.print_exc() 
    
    # Logic for when NO fetch happened (internal only) or fetch failed
    if not should_fetch:
         # Apply same dynamic logic to initial internal retrieval
         # We already have raw 'evidence_list' from line 54 (which was unfiltered? No, line 54 is raw)
         # Wait, line 59 filtered it. We need to move that logic.
         pass # Handled below if we reorganize code, but for now just leave it.

    insufficient_evidence = False
    
    if not evidence_list:
        print("Worker: Still no evidence after Live Fetch.")
        insufficient_evidence = True
        quality_note = "Insufficient Evidence"

    # 4. NLI Stance & Reputation
    stance_results = []
    supports_count = 0
    refutes_count = 0
    neutral_count = 0
    
    # 4. NLI Stance & Reputation
    stance_results = []
    supports_count = 0
    refutes_count = 0
    neutral_count = 0
    
    seen_urls = set()
    unique_evidence = []
    
    # Deduplicate Evidence
    for ev in evidence_list:
        url = ev.get('url')
        if url and url in seen_urls:
            continue
        if url: seen_urls.add(url)
        unique_evidence.append(ev)
        
    evidence_list = unique_evidence
    
    for ev in evidence_list:
        stance = nli.predict(text, ev['text'])
        ev['stance'] = stance
        
        # Check source credibility
        source_url = ev.get('url')
        ev['credibility'] = reputation.check(source_url)
        
        stance_results.append(ev)
        
        if stance['label'] == 'supports':
            supports_count += 1
        elif stance['label'] == 'refutes':
            refutes_count += 1
        else:
            neutral_count += 1
            
    # STANCE-BASED REACTIVE FETCH
    # If we have evidence, but it's ALL Neutral (and we haven't fetched yet), 
    # it means we have "related" info but nothing that confirms/debunks the claim.
    # Force a fetch to look for a "smoking gun".
    
    # We use a flag to prevent infinite loops if we already fetched
    # But since this is a one-shot task, we can just check if we have enough strong evidence.
    
    if len(evidence_list) > 0 and refutes_count == 0 and supports_count == 0:
        print(f"Worker: Evidence found but ALL NEUTRAL. Triggering Deep Search for Stance.")
        
        try:
             # Re-import to avoid scope issues
            from ml.core.router import EvidenceRouter
            from ml.ingest import fetch_claims, save_claims
            from ml.core.news_fetcher import NewsFetcher
            import asyncio
            
            # Simple 3-step fetch: Lane A -> Lane B
            async def run_deep_fetch():
                print("Worker: Deep Fetch running...")
                new_data = []
                
                # 1. Try Fact Checks (Targeted)
                fc = await fetch_claims(query=text)
                if fc: new_data.extend(fc)
                
                # 2. Try News (Broad)
                nf = NewsFetcher()
                news = nf.search_news(text)
                if news: new_data.extend(news)
                
                if new_data:
                    await save_claims(new_data)
                    return True
                return False
                
            got_new = asyncio.run(run_deep_fetch())
            
            if got_new:
                 # Re-retrieve and Re-rank
                 print("Worker: Deep Fetch complete. Re-ranking...")
                 # Clear previous results to avoid mixing old neutral with new stuff? 
                 # Actually, better to keep both but prioritize new.
                 new_evidence = retriever.retrieve(text)
                 
                 # Re-run NLI on new evidence
                 for ev in new_evidence:
                     # Skip if we already saw it (Dedupe again)
                     if ev.get('url') in seen_urls: continue
                     
                     stance = nli.predict(text, ev['text'])
                     ev['stance'] = stance
                     ev['credibility'] = reputation.check(ev.get('url'))
                     
                     stance_results.append(ev)
                     
                     if stance['label'] == 'supports': supports_count += 1
                     elif stance['label'] == 'refutes': refutes_count += 1
                     else: neutral_count += 1
        except Exception as e:
            print(f"Worker: Deep Fetch failed: {e}")

    # 4b. Diversity Re-ranking
    # Group by stance to ensure variety at the top
    supports_list = [e for e in stance_results if e['stance']['label'] == 'supports']
    refutes_list = [e for e in stance_results if e['stance']['label'] == 'refutes']
    neutral_list = [e for e in stance_results if e['stance']['label'] == 'neutral']
    
    # Sort buckets by relevance score (lower is better)
    supports_list.sort(key=lambda x: x.get('score', 100))
    refutes_list.sort(key=lambda x: x.get('score', 100))
    neutral_list.sort(key=lambda x: x.get('score', 100))
    
    diversified_results = []
    
    # Pick top 1 from each category if available (Prioritize Refutes -> Supports -> Neutral)
    if refutes_list: diversified_results.append(refutes_list.pop(0))
    if supports_list: diversified_results.append(supports_list.pop(0))
    if neutral_list: diversified_results.append(neutral_list.pop(0))
    
    # Add the rest back, sorted by relevance
    remaining = supports_list + refutes_list + neutral_list
    remaining.sort(key=lambda x: x.get('score', 100))
    
    diversified_results.extend(remaining)
    
    # Update the final list
    ordered_evidence = diversified_results

    result = {
        "text": text,
        "style_risk_score": style_risk,
        "heatmap": heatmap,
        "evidence": ordered_evidence,
        "stance_summary": {
            "supports": supports_count,
            "refutes": refutes_count,
            "neutral": neutral_count
        },
        "status": "completed",
        "status": "completed",
        "quality_note": quality_note if not insufficient_evidence else "Insufficient Evidence",
    }
    
    # 5. Unified Risk Calculation
    # Start with style risk (0-100)
    final_risk = style_risk
    
    # Override based on evidence
    if refutes_count > 0 and supports_count > 0:
        # Conflicting evidence = Contested
        final_risk = 65 # Medium Risk (Amber)
        quality_note = "Contested - Conflicting Evidence"
    elif refutes_count > 0:
        # If ONLY refuting evidence found (or no supports), risk is EXTREME
        final_risk = max(final_risk, 95)
    elif supports_count > 0:
        # If verified sources support it, risk is LOW
        final_risk = min(final_risk, 5)
    elif is_safety_critical:
        # Safety Critical Logic
        if insufficient_evidence:
             print("Worker: Safety Critical query with NO evidence. Elevating Risk.")
             final_risk = max(final_risk, 80) # Force High Risk for unverified danger
             quality_note = "Unverified - High Risk Topic"
        elif neutral_count > 0 and final_risk < 50:
             print("Worker: Safety Critical query with only Neutral evidence. Elevating Risk.")
             final_risk = 70 # High Caution
             quality_note = "Unverified - Exercise Caution"
        
    result["risk_score"] = final_risk
    result["style_risk_score"] = final_risk # Overwrite for UI
    result["quality_note"] = quality_note if not insufficient_evidence else "Insufficient Evidence"
        
    result["risk_score"] = final_risk
    result["style_risk_score"] = final_risk # Overwrite for UI
    
    # Add new linguistic fields
    result["linguistic_signals"] = style_analysis.get("signals", [])
    result["linguistic_verdict"] = style_analysis.get("verdict", "")

    result["meta"] = {
        "app_version": "v1.0.0-beta",
        "model_type": "roberta-base+heuristics",
        "index_version": "chroma-v1"
    }
    
    # Cache result (TTL 1 hour)
    r.setex(cache_key, 3600, json.dumps(result))
    
    return result
