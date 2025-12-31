import re

class EvidenceRouter:
    def __init__(self):
        # Heuristics for "Disputable Claims" (Lane A)
        self.claim_patterns = [
            r"\bcure\b", r"\bprevent\b", r"\bsecret\b", r"\bhoax\b", 
            r"\bfake\b", r"\bconspiracy\b", r"\breal\b", r"\btruth about\b",
            r"\bviral\b", r"\bvideo shows\b", r"\bdied\b", r"\balive\b",
            r"\bdangerous\b", r"\bunsafe\b", r"\bkill\b", r"\bpoison\b", r"\brisk\b"
        ]
        
        # Heuristics for "General Events" (Lane B)
        self.event_patterns = [
            r"\battacked\b", r"\binvaded\b", r"\bwar\b", r"\belection\b",
            r"\bwon\b", r"\blost\b", r"\bhappened\b", r"\bearthquake\b",
            r"\bhurricane\b", r"\bprotest\b", r"\bsummit\b", r"\bmeeting\b"
        ]

    def route(self, text):
        """
        Returns 'lane_a' (Claim), 'lane_b' (Event), or 'hybrid'.
        """
        text_lower = text.lower()
        
        # Check Claim Signals
        claim_score = sum(1 for p in self.claim_patterns if re.search(p, text_lower))
        
        # Check Event Signals
        event_score = sum(1 for p in self.event_patterns if re.search(p, text_lower))
        
        print(f"Router: ClaimScore={claim_score}, EventScore={event_score}")
        
        if claim_score > 0:
            return "lane_a"  # Prioritize specific rumors
        elif event_score > 0:
            return "lane_b"
        else:
            return "lane_a" # Default to Fact Check for safety, falling back later
