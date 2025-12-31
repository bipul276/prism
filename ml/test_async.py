import requests
import time
import json

def test_async_analysis():
    url = "http://127.0.0.1:8000/api/analyze"
    # A text with some "red flags" and potential evidence in our mock logic
    text = "The earth is flat and NASA is hiding the ice wall secrets!"
    
    print(f"Submitting text: {text}")
    try:
        response = requests.post(url, json={"text": text})
        print(f"Submit Response: {response.text}")
        if response.status_code != 200:
            return
            
        job_id = response.json().get("job_id")
        print(f"Job ID: {job_id}")
        
        # Poll
        status_url = f"http://127.0.0.1:8000/api/status/{job_id}"
        while True:
            res = requests.get(status_url)
            data = res.json()
            status = data.get("status")
            print(f"Status: {status}")
            
            if status in ["completed", "failed"]:
                if status == "completed":
                    print("\n--- Analysis Result ---")
                    result = data.get("result")
                    print(json.dumps(result, indent=2))
                    
                    # Verify heatmap exists
                    if "heatmap" in result:
                        print(f"\n✅ Heatmap generated with {len(result['heatmap'])} tokens.")
                    else:
                        print("\n❌ Heatmap missing.")
                        
                else:
                    print(f"❌ Failed: {data.get('error')}")
                break
            
            time.sleep(2)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_async_analysis()
