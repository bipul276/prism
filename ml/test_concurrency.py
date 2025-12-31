import concurrent.futures
import requests
import time
import statistics
import json
import os

API_URL = "http://localhost:8000/api"
REPORT_DIR = "reports"
REPORT_FILE = os.path.join(REPORT_DIR, "concurrency_results.json")

if not os.path.exists(REPORT_DIR):
    os.makedirs(REPORT_DIR)

def submit_analysis(i):
    """Simulate user submitting a claim"""
    text = f"Concurrent test claim {i}: The moon is made of green cheese and 5G causes it."
    try:
        start = time.time()
        resp = requests.post(f"{API_URL}/analyze", json={"text": text}, timeout=10)
        duration = time.time() - start
        
        if resp.status_code == 200:
            return {"id": i, "status": "submitted", "job_id": resp.json().get("job_id"), "duration": duration}
        return {"id": i, "status": "failed", "code": resp.status_code, "duration": duration}
    except Exception as e:
        return {"id": i, "status": "error", "error": str(e), "duration": 0}

def run_stress_test(n_requests=20, max_workers=10):
    print(f"🚀 Starting Stress Test with {n_requests} concurrent requests (Workers: {max_workers})...")
    
    start_all = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(submit_analysis, i) for i in range(n_requests)]
        
        results = []
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())
    
    total_time = time.time() - start_all
    
    # Analyze
    successes = [r for r in results if r["status"] == "submitted"]
    failures = [r for r in results if r["status"] != "submitted"]
    durations = [r["duration"] for r in successes]
    
    metrics = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_requests": n_requests,
        "success_count": len(successes),
        "failure_count": len(failures),
        "total_wall_time_s": total_time,
        "throughput_req_per_s": n_requests / total_time if total_time > 0 else 0,
        "latency_p50_s": statistics.median(durations) if durations else 0,
        "latency_p95_s": statistics.quantiles(durations, n=20)[-1] if len(durations) >= 20 else max(durations) if durations else 0,
        "pass": len(failures) == 0 and (len(durations) > 0 and statistics.median(durations) < 2.0)
    }
    
    print("\n--- Concurrency Report ---")
    print(f"✅ Success Rate: {metrics['success_count']}/{metrics['total_requests']}")
    print(f"⏱️ p50 Latency: {metrics['latency_p50_s']:.4f}s")
    print(f"⏱️ p95 Latency: {metrics['latency_p95_s']:.4f}s")
    print(f"🚀 Throughput: {metrics['throughput_req_per_s']:.2f} req/s")
    
    if metrics["pass"]:
        print("✅ PASSED: System meets concurrency thresholds.")
    else:
        print("❌ FAILED: High latency or errors detected.")
        
    with open(REPORT_FILE, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"📄 Report saved to {REPORT_FILE}")

if __name__ == "__main__":
    run_stress_test()
