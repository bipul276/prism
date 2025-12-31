import requests
import xml.etree.ElementTree as ET
from urllib.parse import quote_plus

class NewsFetcher:
    def __init__(self):
        self.allowlist = [
            "bbc.com", "reuters.com", "apnews.com", "aljazeera.com", 
            "npr.org", "pbs.org", "who.int", "un.org", "nasa.gov",
            "nytimes.com", "washingtonpost.com", "guardian.com",
            "dw.com", "france24.com", "cbc.ca"
        ]

    def search_news(self, query):
        """
        Lane B: Access trusted news via Google News RSS (More stable than scraping).
        """
        print(f"NewsFetcher: Searching Google News RSS for '{query}'...")
        results = []
        
        try:
            # Use Google News RSS Match
            encoded_query = quote_plus(query)
            rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
            
            response = requests.get(rss_url, timeout=10)
            if response.status_code != 200:
                print(f"NewsFetcher: RSS Error {response.status_code}")
                return []
                
            # Parse XML
            root = ET.fromstring(response.content)
            
            # Iterate over items
            count = 0
            for item in root.findall('.//item'):
                if count >= 10: break
                
                title = item.find('title').text if item.find('title') is not None else ""
                link = item.find('link').text if item.find('link') is not None else ""
                pubDate = item.find('pubDate').text if item.find('pubDate') is not None else ""
                source = item.find('source').text if item.find('source') is not None else "Google News"
                
                # Basic cleaning
                # Title often looks like "Headline - Source Name"
                clean_text = title
                
                # Normalize simple object to match Google Fact Check API structure
                # This ensures ml/ingest.py can save it without modification.
                claims_obj = {
                    "text": clean_text,
                    "claimant": source,
                    "claimDate": pubDate,
                    "claimReview": [{"url": link, "title": title}],
                    "source": source, # NewsFetcher explicit source
                    "languageCode": "en"
                }
                results.append(claims_obj)
                count += 1
                    
            print(f"NewsFetcher: Found {len(results)} news items via RSS.")
            return results
            
        except Exception as e:
            print(f"NewsFetcher Error: {e}")
            import traceback
            traceback.print_exc()
            return []
