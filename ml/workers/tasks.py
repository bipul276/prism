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
    
    # Trust Gating: TIGHTENED from 1.4 → 1.0
    # Cosine distance > 1.0 means the evidence is barely related to the claim.
    # Accepting 1.2-1.6 pulled in articles about completely different events
    # (e.g., Iran/Israel articles for a Russia/Ukraine query).
    STRICT_THRESHOLD = 1.0
    original_count = len(evidence_list)
    evidence_list = [e for e in evidence_list if e['score'] < STRICT_THRESHOLD] 
    print(f"Worker: Initial retrieval: {original_count} raw → {len(evidence_list)} after threshold {STRICT_THRESHOLD}")
    
    # REACTIVE RAG & 3-LANE ROUTER
    should_fetch = False
    
    # SAFETY OVERRIDE: Semantic Check
    is_safety_critical = nli.check_safety(text)
    
    if is_safety_critical:
         print(f"Worker: Semantic Safety Check TRIGGERED. FORCING FETCH.")
         should_fetch = True
         
    elif not evidence_list:
        should_fetch = True
        print(f"Worker: No relevant internal evidence. Triggering Smart Fetch.")
    else:
        best_score = min([e['score'] for e in evidence_list])
        if best_score > 0.7:
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
                        news_data = nf.search_news(text, max_results=30)
                        if news_data: new_data.extend(news_data)

                # Lane B: General News (Events)
                elif route == "lane_b" or (is_safety_critical and not new_data):
                    print("Worker: Running Lane B (Trusted News)...")
                    nf = NewsFetcher()
                    news_data = nf.search_news(text, max_results=30)
                    if news_data: 
                        print(f"Worker: Lane B found {len(news_data)} items.")
                        new_data.extend(news_data)
                    else:
                        print("Worker: Lane B found 0 items.")
                
                if new_data:
                    print(f"Worker: Ingesting {len(new_data)} items...")
                    await save_claims(new_data)
                    # Wait for ChromaDB to index the new vectors
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
                
                # Dynamic Relaxation Loop — TIGHTENED thresholds
                # Previous: [1.2, 1.4, 1.6] — way too loose, pulled unrelated articles
                # Now: [0.8, 1.0, 1.2] — only accept genuinely related evidence
                thresholds = [0.8, 1.0, 1.2]
                final_evidence = []
                quality_note = "Verified"
                used_threshold = 0.8
                
                for t in thresholds:
                    filtered = [e for e in raw_evidence if e['score'] < t]
                    if len(filtered) >= 3:
                        final_evidence = filtered
                        used_threshold = t
                        break
                    final_evidence = filtered
                    used_threshold = t
                
                # INCREASED cap from 8 → 15 to show more evidence for well-covered topics
                evidence_list = final_evidence[:15]
                
                if used_threshold >= 1.2:
                    print(f"Worker: Used broad threshold {used_threshold}. Adding disclaimer.")
                    quality_note = "Weak Evidence Match (View with Caution)"

        except Exception as e:
            print(f"Worker: Smart Fetch failed: {e}")
            import traceback
            traceback.print_exc() 
    
    insufficient_evidence = False
    
    if not evidence_list:
        print("Worker: Still no evidence after Live Fetch.")
        insufficient_evidence = True
        quality_note = "Insufficient Evidence"

    # 4. NLI Stance & Reputation — NOW WITH TOPICAL RELEVANCE GATING
    stance_results = []
    supports_count = 0
    refutes_count = 0
    neutral_count = 0
    skipped_irrelevant = 0
    
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
        # NEW: Topical relevance check BEFORE stance classification
        # This prevents "Iran attacked Israel" from being used as evidence 
        # for/against "Russia attacked Ukraine"
        is_relevant, relevance_score = nli.is_topically_relevant(text, ev['text'])
        ev['relevance_score'] = relevance_score
        
        if not is_relevant:
            print(f"Worker: SKIPPING irrelevant evidence (score={relevance_score:.2f}): '{ev['text'][:60]}...'")
            skipped_irrelevant += 1
            continue
        
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
    
    if skipped_irrelevant > 0:
        print(f"Worker: Skipped {skipped_irrelevant} irrelevant evidence items.")
            
    # STANCE-BASED REACTIVE FETCH
    # If we have evidence, but it's ALL Neutral, force a deeper search
    if len(stance_results) > 0 and refutes_count == 0 and supports_count == 0:
        print(f"Worker: Evidence found but ALL NEUTRAL. Triggering Deep Search for Stance.")
        
        try:
            from ml.core.router import EvidenceRouter
            from ml.ingest import fetch_claims, save_claims
            from ml.core.news_fetcher import NewsFetcher
            
            async def run_deep_fetch():
                print("Worker: Deep Fetch running...")
                new_data = []
                
                # 1. Try Fact Checks (Targeted)
                fc = await fetch_claims(query=text)
                if fc: new_data.extend(fc)
                
                # 2. Try News (Broad) — now fetches 30 instead of 10
                nf = NewsFetcher()
                news = nf.search_news(text, max_results=30)
                if news: new_data.extend(news)
                
                if new_data:
                    await save_claims(new_data)
                    return True
                return False
                
            got_new = asyncio.run(run_deep_fetch())
            
            if got_new:
                print("Worker: Deep Fetch complete. Re-ranking...")
                new_evidence = retriever.retrieve(text)
                 
                for ev in new_evidence:
                    if ev.get('url') in seen_urls: continue
                    
                    # Apply relevance gating to deep-fetched evidence too
                    is_relevant, relevance_score = nli.is_topically_relevant(text, ev['text'])
                    if not is_relevant:
                        continue
                    
                    ev['relevance_score'] = relevance_score
                    stance = nli.predict(text, ev['text'])
                    ev['stance'] = stance
                    ev['credibility'] = reputation.check(ev.get('url'))
                    
                    stance_results.append(ev)
                    if ev.get('url'): seen_urls.add(ev['url'])
                    
                    if stance['label'] == 'supports': supports_count += 1
                    elif stance['label'] == 'refutes': refutes_count += 1
                    else: neutral_count += 1
        except Exception as e:
            print(f"Worker: Deep Fetch failed: {e}")

    # 4b. Diversity Re-ranking
    supports_list = [e for e in stance_results if e['stance']['label'] == 'supports']
    refutes_list = [e for e in stance_results if e['stance']['label'] == 'refutes']
    neutral_list = [e for e in stance_results if e['stance']['label'] == 'neutral']
    
    # Sort buckets by relevance score (higher = better) then by retrieval score (lower = better)
    supports_list.sort(key=lambda x: (-x.get('relevance_score', 0), x.get('score', 100)))
    refutes_list.sort(key=lambda x: (-x.get('relevance_score', 0), x.get('score', 100)))
    neutral_list.sort(key=lambda x: (-x.get('relevance_score', 0), x.get('score', 100)))
    
    diversified_results = []
    
    # Pick top 2 from each category if available (was 1, increased)
    for item in refutes_list[:2]: diversified_results.append(item)
    for item in supports_list[:2]: diversified_results.append(item)
    for item in neutral_list[:1]: diversified_results.append(item)
    
    # Add the rest
    remaining = refutes_list[2:] + supports_list[2:] + neutral_list[1:]
    remaining.sort(key=lambda x: (-x.get('relevance_score', 0), x.get('score', 100)))
    
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
        "quality_note": quality_note if not insufficient_evidence else "Insufficient Evidence",
    }
    
    # 5. Unified Risk Calculation — IMPROVED with evidence confidence weighting
    final_risk = style_risk
    
    # Calculate evidence confidence: how strong are the stance signals?
    total_stance = supports_count + refutes_count + neutral_count
    
    if total_stance > 0:
        # Weight by count AND by average confidence
        avg_refute_conf = 0
        avg_support_conf = 0
        
        if refutes_count > 0:
            avg_refute_conf = sum(
                e['stance']['confidence'] for e in stance_results 
                if e['stance']['label'] == 'refutes'
            ) / refutes_count
        
        if supports_count > 0:
            avg_support_conf = sum(
                e['stance']['confidence'] for e in stance_results 
                if e['stance']['label'] == 'supports'
            ) / supports_count
    
        if refutes_count > 0 and supports_count > 0:
            # Conflicting evidence = Contested
            final_risk = 65
            quality_note = "Contested - Conflicting Evidence"
        elif refutes_count > 0 and supports_count == 0:
            # FIXED: Scale risk by evidence strength instead of jumping to 95
            # Only go to 95 if we have STRONG, HIGH-CONFIDENCE refutations
            if refutes_count >= 3 and avg_refute_conf > 0.7:
                final_risk = max(final_risk, 95)  # Strong refutation
            elif refutes_count >= 2 and avg_refute_conf > 0.6:
                final_risk = max(final_risk, 85)  # Moderate refutation
            else:
                final_risk = max(final_risk, 70)  # Weak/single refutation
        elif supports_count > 0 and refutes_count == 0:
            # Verified sources support it
            if supports_count >= 3 and avg_support_conf > 0.7:
                final_risk = min(final_risk, 5)   # Strongly supported
            elif supports_count >= 2 and avg_support_conf > 0.6:
                final_risk = min(final_risk, 15)  # Moderately supported
            else:
                final_risk = min(final_risk, 25)  # Weakly supported
        elif is_safety_critical:
            if insufficient_evidence:
                print("Worker: Safety Critical query with NO evidence. Elevating Risk.")
                final_risk = max(final_risk, 80)
                quality_note = "Unverified - High Risk Topic"
            elif neutral_count > 0 and final_risk < 50:
                print("Worker: Safety Critical query with only Neutral evidence. Elevating Risk.")
                final_risk = 70
                quality_note = "Unverified - Exercise Caution"
    else:
        # No stance results at all
        if is_safety_critical:
            final_risk = max(final_risk, 80)
            quality_note = "Unverified - High Risk Topic"
        
    result["risk_score"] = final_risk
    result["style_risk_score"] = final_risk  # Overwrite for UI
    result["quality_note"] = quality_note if not insufficient_evidence else "Insufficient Evidence"
    
    # Add linguistic fields
    result["linguistic_signals"] = style_analysis.get("signals", [])
    result["linguistic_verdict"] = style_analysis.get("verdict", "")

    result["meta"] = {
        "app_version": "v1.0.0-beta",
        "model_type": "roberta-base+heuristics",
        "index_version": "chroma-v1",
        "evidence_stats": {
            "total_retrieved": original_count,
            "after_threshold": len(evidence_list),
            "skipped_irrelevant": skipped_irrelevant,
            "final_with_stance": len(stance_results)
        }
    }
    
    # Cache result (TTL 1 hour)
    r.setex(cache_key, 3600, json.dumps(result))
    
    return result
