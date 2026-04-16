import requests
import xml.etree.ElementTree as ET
from urllib.parse import quote_plus

class NewsFetcher:
    def __init__(self):
        self.allowlist = [
            "bbc.com", "reuters.com", "apnews.com", "aljazeera.com", 
            "npr.org", "pbs.org", "who.int", "un.org", "nasa.gov",
            "nytimes.com", "washingtonpost.com", "guardian.com",
            "dw.com", "france24.com", "cbc.ca", "factcheck.afp.com",
            "politifact.com", "snopes.com", "indiatoday.in",
            "ndtv.com", "thehindu.com", "hindustantimes.com"
        ]

    def _extract_key_terms(self, query):
        """
        Generate multiple search queries from the original claim for broader coverage.
        For 'Russia attacked Ukraine' → ['Russia attacked Ukraine', 'Russia Ukraine war', 'Russia Ukraine conflict']
        """
        queries = [query]  # Always include the original
        
        # Simple term extraction: split into meaningful words
        stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
                      'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
                      'would', 'could', 'should', 'may', 'might', 'can', 'shall',
                      'this', 'that', 'these', 'those', 'it', 'its', 'of', 'in',
                      'on', 'at', 'to', 'for', 'with', 'by', 'from', 'about',
                      'not', 'no', 'nor', 'and', 'or', 'but', 'if', 'then',
                      'so', 'very', 'just', 'also', 'only'}
        
        words = [w for w in query.split() if w.lower() not in stop_words and len(w) > 2]
        
        if len(words) >= 2:
            # Add a "key terms + fact check" query for better results
            key_phrase = ' '.join(words[:4])  # Max 4 key words
            queries.append(f"{key_phrase} fact check")
            queries.append(f"{key_phrase} latest news")
        
        return queries[:3]  # Max 3 search queries

    def search_news(self, query, max_results=30):
        """
        Lane B: Access trusted news via Google News RSS.
        Now uses multi-query expansion for broader coverage.
        """
        print(f"NewsFetcher: Searching Google News RSS for '{query}' (max {max_results})...")
        all_results = []
        seen_links = set()  # Dedup across queries
        
        search_queries = self._extract_key_terms(query)
        per_query_limit = max(10, max_results // len(search_queries))
        
        for sq in search_queries:
            try:
                encoded_query = quote_plus(sq)
                rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
                
                response = requests.get(rss_url, timeout=10)
                if response.status_code != 200:
                    print(f"NewsFetcher: RSS Error {response.status_code} for query '{sq}'")
                    continue
                    
                # Parse XML
                root = ET.fromstring(response.content)
                
                count = 0
                for item in root.findall('.//item'):
                    if count >= per_query_limit: 
                        break
                    
                    title = item.find('title').text if item.find('title') is not None else ""
                    link = item.find('link').text if item.find('link') is not None else ""
                    pubDate = item.find('pubDate').text if item.find('pubDate') is not None else ""
                    source = item.find('source').text if item.find('source') is not None else "Google News"
                    
                    # Dedup by link
                    if link in seen_links:
                        continue
                    seen_links.add(link)
                    
                    clean_text = title
                    
                    claims_obj = {
                        "text": clean_text,
                        "claimant": source,
                        "claimDate": pubDate,
                        "claimReview": [{"url": link, "title": title}],
                        "source": source,
                        "languageCode": "en"
                    }
                    all_results.append(claims_obj)
                    count += 1
                    
                print(f"NewsFetcher: Found {count} items for sub-query '{sq}'")
                        
            except Exception as e:
                print(f"NewsFetcher Error for query '{sq}': {e}")
                import traceback
                traceback.print_exc()
        
        print(f"NewsFetcher: Total unique results: {len(all_results)}")
        return all_results
