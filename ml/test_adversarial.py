import requests
import time
import json

API_URL = "http://127.0.0.1:8000/api"

# Adversarial Test Suite
TEST_CASES = [
    {
        "name": "Emotional Manipulation (Caps/Imperative)",
        "text": "THE GOVERNMENT IS HIDING THE TRUTH! WAKE UP SHEEPLE! THEY ARE POISONING THE WATER SUPPLY TO CONTROL YOUR MIND! SHARE THIS NOW BEFORE IT'S DELETED!!!",
        "expected_risk_min": 0.7,
        "desc": "High stylometric risk expected due to caps and urgency."
    },
    {
        "name": "Pseudoscience (Jargon-heavy)",
        "text": "Recent bio-resonance studies indicate that 5G millimeter waves interact with the voltage-gated calcium channels in cellular membranes, causing widespread mitochondrial dysfunction and viral replication.",
        "expected_risk_min": 0.4,
        "desc": "Medium/High risk. Logic sounds technical but might trigger 'fake news' linguistic patterns."
    },
    {
        "name": "Known Fact (Flat Earth)",
        "text": "The earth is flat and there is a giant ice wall guarding the edge.",
        "expected_evidence_count": 1,
        "desc": "Should retrieve evidence refuting this."
    },
    {
        "name": "Benign Text (Wiki-style)",
        "text": "The mitochondrion is a double-membrane-bound organelle found in most eukaryotic organisms. It generates most of the cell's supply of adenosine triphosphate (ATP), used as a source of chemical energy.",
        "expected_risk_max": 0.3,
        "desc": "Low risk expected."
    }
]

def run_test(case):
    print(f"\n--- Running: {case['name']} ---")
    try:
        # Submit
        resp = requests.post(f"{API_URL}/analyze", json={"text": case["text"]})
        if resp.status_code != 200:
            print(f"❌ Submission Failed: {resp.text}")
            return False
            
        job_id = resp.json()["job_id"]
        print(f"Job ID: {job_id}. Polling...")
        
        # Poll
        for _ in range(30): # 60s timeout
            time.sleep(2)
            resp = requests.get(f"{API_URL}/status/{job_id}")
            data = resp.json()
            
            if data["status"] == "completed":
                result = data["result"]
                score = result.get("style_risk_score", 0)
                evidence = result.get("evidence", [])
                
                print(f"✅ Completed. Risk Score: {score}")
                print(f"   Evidence Found: {len(evidence)}")
                
                # Assertions
                success = True
                if "expected_risk_min" in case and score < case["expected_risk_min"]:
                    print(f"❌ Risk Score too low (Expected > {case['expected_risk_min']})")
                    success = False
                
                if "expected_risk_max" in case and score > case["expected_risk_max"]:
                    print(f"❌ Risk Score too high (Expected < {case['expected_risk_max']})")
                    success = False
                    
                if "expected_evidence_count" in case and len(evidence) < case["expected_evidence_count"]:
                    print(f"❌ Not enough evidence (Expected >= {case['expected_evidence_count']})")
                    success = False
                    
                return success
            
            if data["status"] == "failed":
                print(f"❌ Job Failed: {data.get('error')}")
                return False
                
        print("❌ Timeout polling job.")
        return False
        
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

if __name__ == "__main__":
    passed = 0
    for case in TEST_CASES:
        if run_test(case):
            print("✅ TEST PASSED")
            passed += 1
        else:
            print("❌ TEST FAILED")
            
    print(f"\nSummary: {passed}/{len(TEST_CASES)} Tests Passed.")
