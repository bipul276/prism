import os
import requests
from dotenv import load_dotenv

# Load env vars from the same directory
load_dotenv()

API_KEY = os.getenv("GOOGLE_FACT_CHECK_API_KEY")
URL = "https://factchecktools.googleapis.com/v1alpha1/claims:search"

if not API_KEY:
    print("❌ ERROR: GOOGLE_FACT_CHECK_API_KEY is not set in environment.")
    exit(1)

print(f"🔑 Testing API Key: {API_KEY[:5]}...{API_KEY[-5:]}")

params = {
    "key": API_KEY,
    "query": "earth", # Simple query
    "pageSize": 3
}

try:
    print(f"📡 Sending request to {URL}...")
    response = requests.get(URL, params=params)
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        claims = data.get("claims", [])
        print(f"✅ Success! Found {len(claims)} claims.")
        if len(claims) > 0:
            print(f"Sample: {claims[0].get('text')[:50]}...")
    else:
        print(f"❌ API Error Response:\n{response.text}")

except Exception as e:
    print(f"❌ Connection/Runtime Error: {e}")
