import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GOOGLE_FACT_CHECK_API_KEY")
API_URL = "https://factchecktools.googleapis.com/v1alpha1/claims:search"

def test_query(query):
    print(f"\n--- Testing Query: '{query}' ---")
    if not API_KEY:
        print("❌ No API Key found.")
        return

    params = {
        "key": API_KEY,
        "query": query,
        "pageSize": 10,
        "languageCode": "en"
    }

    try:
        response = requests.get(API_URL, params=params, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            claims = data.get("claims", [])
            print(f"✅ Found {len(claims)} claims.")
            for i, claim in enumerate(claims[:3]):
                print(f"  {i+1}. {claim.get('text')} (Claimant: {claim.get('claimant')})")
        else:
            print(f"❌ Error: {response.text}")

    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_query("Russia attacked Ukraine")
    test_query("Ukraine War")
    test_query("Earth is flat")
