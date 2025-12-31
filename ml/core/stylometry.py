from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import torch.nn.functional as F

class StylometricAnalyzer:
    def __init__(self, model_name="roberta-base"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Stylometry loaded on {self.device}")
        
        # In a real scenario, this would be a fine-tuned model for misinformation
        # For Phase 2 prototype, we use base RoBERTa and simulate a risk score or use zero-shot
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name).to(self.device)
        self.model.eval()

    def analyze(self, text):
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512).to(self.device)
        with torch.no_grad():
            outputs = self.model(**inputs)
            probs = F.softmax(outputs.logits, dim=-1)
            
        # Mock logic for "risk" until we fine-tune:
        # Use entropy or just a placeholder logic based on some keywords for demo
        # Real implementation: return probs[1].item() if class 1 is "fake"
        
        # Simple heuristic for demo: length and some keywords
        # Enhanced Heuristic Logic for Prototype
        risk_score = 0.1
        
        # 1. Keyword Detection
        red_flags = [
            "shocking", "you won't believe", "secret", "exposed", "truth", "wake up", 
            "sheeple", "poisoning", "control", "mind", "5g", "bio-resonance", 
            "mitochondrial", "vibration", "frequency", "quantum", "hidden", "censored",
            "bioweapon", "agenda", "reset", "flat earth", "ice wall"
        ]
        
        found_flags = 0
        text_lower = text.lower()
        for flag in red_flags:
            if flag in text_lower:
                found_flags += 1
        
        # Add 0.15 per flag, max 0.6 from flags
        risk_score += min(found_flags * 0.15, 0.6)

        # 2. Emotional/Shouting Detection (Caps Lock)
        caps_count = sum(1 for c in text if c.isupper())
        caps_ratio = caps_count / max(len(text), 1)
        
        if caps_ratio > 0.4: # More than 40% caps
            risk_score += 0.3
        elif caps_ratio > 0.15:
            risk_score += 0.1

        # 3. Punctuation Abuse
        exclamations = text.count("!")
        if exclamations > 2:
            risk_score += 0.2
            
        return min(risk_score, 0.99)
