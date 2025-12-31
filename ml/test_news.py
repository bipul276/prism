from ml.core.router import EvidenceRouter
from ml.core.news_fetcher import NewsFetcher

def test_system():
    print("\n--- Testing Router ---")
    r = EvidenceRouter()
    print(f"Russia: {r.route('russia attacked ukraine')}")
    print(f"Vaccine: {r.route('vaccine is dangerous')}")
    
    print("\n--- Testing NewsFetcher ---")
    nf = NewsFetcher()
    try:
        res = nf.search_news("russia attacked ukraine")
        print(f"News Items Found: {len(res)}")
        if res:
            print(f"Sample: {res[0]['text'][:100]}...")
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")

if __name__ == "__main__":
    test_system()
