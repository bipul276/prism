class ReputationChecker:
    def __init__(self):
        # Simple allow/block list for prototype
        self.high_credibility = [
            "reuters.com", "apnews.com", "bbc.com", "npr.org", "pbs.org",
            "who.int", "cdc.gov", "nature.com", "sciencemag.org"
        ]
        self.low_credibility = [
            "infowars.com", "newsmax.com", "dailymail.co.uk", "rt.com", 
            "sputniknews.com", "breitbart.com", "beforeitsnews.com"
        ]

    def check(self, url):
        if not url:
            return "unknown"
            
        domain = url.lower()
        # Simple substring check (improvements: use tldextract)
        for d in self.high_credibility:
            if d in domain:
                return "high"
        
        for d in self.low_credibility:
            if d in domain:
                return "low"
                
        return "neutral"
