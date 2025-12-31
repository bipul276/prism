import time
import requests
import sys

API_URL = "http://localhost:8000"

def wait_for_health():
    print("Waiting for API health...")
    for i in range(30):
        try:
            resp = requests.get(f"{API_URL}/health")
            if resp.status_code == 200:
                print("✅ API is healthy!")
                return True
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(1)
        sys.stdout.write(".")
        sys.stdout.flush()
    print("\n❌ API timed out.")
    return False

def smoke_test():
    if not wait_for_health():
        sys.exit(1)
        
    print("\n🚀 Submitting Smoke Test Job...")
    claim = "Smoke test claim: The sun is cold."
    
    try:
        # Submit
        resp = requests.post(f"{API_URL}/api/analyze", json={"text": claim})
        if resp.status_code != 200:
            print(f"❌ Submit failed: {resp.text}")
            sys.exit(1)
            
        job_id = resp.json()["job_id"]
        print(f"✅ Submitted. Job ID: {job_id}")
        
        # Poll
        for i in range(180):
            time.sleep(1)
            resp = requests.get(f"{API_URL}/api/status/{job_id}")
            data = resp.json()
            status = data.get("status")
            
            if status == "completed":
                print("✅ Job Completed!")
                print(f"   Risk Score: {data['result']['style_risk_score']}")
                print(f"   Meta: {data['result'].get('meta')}")
                
                # Verify report page accessible (simulated)
                report_url = f"http://localhost:3001/report/{job_id}"
                print(f"✅ Report available at: {report_url}")
                return
            elif status == "failed":
                print(f"❌ Job Failed: {data.get('error')}")
                sys.exit(1)
                
            sys.stdout.write(".")
            sys.stdout.flush()
            
        print("\n❌ Job timed out.")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    smoke_test()
