import requests
import json

def test_api():
    url = "http://127.0.0.1:8000/api/analyze"
    payload = {"text": "The earth is flat and there is a secret ice wall."}
    try:
        response = requests.post(url, json=payload)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(json.dumps(response.json(), indent=2))
        else:
            print(response.text)
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_api()
