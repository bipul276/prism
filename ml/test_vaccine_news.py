from ml.core.news_fetcher import NewsFetcher
import json

def test():
    print("Testing NewsFetcher for 'Vaccines are dangerous'...")
    nf = NewsFetcher()
    results = nf.search_news("Vaccines are dangerous")
    print(f"Items found: {len(results)}")
    if results:
        print("Sample Item:")
        print(json.dumps(results[0], indent=2))
    else:
        print("❌ No results found!")

if __name__ == "__main__":
    test()
