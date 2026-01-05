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



    def detect_signals(self, text):
        signals = []
        text_lower = text.lower()
        
        # 1. Causal Absolutes
        causal_kw = ["cause", "causes", "cure", "cures", "leads to", "results in", "inevitable", "undeniable", "must be", "proven", "kills", "destroys"]
        if any(w in text_lower for w in causal_kw):
            signals.append({
                "name": "Causal Absolutes",
                "trigger": "Absolute causal verbs",
                "explanation": "Uses absolute causal language that oversimplifies complex relationships."
            })

        # 2. Emotional Loading
        emotional_kw = ["shocking", "terrifying", "unbelievable", "devastating", "exposed", "horror", "deadly", "poison", "bleach", "dangerous", "toxic"]
        if any(w in text_lower for w in emotional_kw):
             signals.append({
                "name": "Emotional Loading",
                "trigger": "Emotionally charged terms",
                "explanation": "Emotionally loaded terms increase persuasive impact without adding evidence."
            })

        # 3. Attribution Gap
        attribution_kw = ["according to", "reported by", "stated by", "sources say", "experts say", "study shows"]
        has_attribution = any(w in text_lower for w in attribution_kw)
        if not has_attribution and len(text.split()) > 10: # Only flag if text is decent length
             signals.append({
                "name": "Attribution Gap",
                "trigger": "Lack of citation",
                "explanation": "Lacks attribution to verifiable sources or reporting entities."
            })
            
        # 4. Conspiracy Framing
        consp_kw = ["they don't want you to know", "hidden", "suppressed", "secret agenda", "truth about", "wake up", "mainstream media"]
        if any(w in text_lower for w in consp_kw):
             signals.append({
                "name": "Conspiracy Framing",
                "trigger": "Suppression narratives",
                "explanation": "Implicitly frames information as suppressed or hidden by powerful actors."
            })
            
        return signals

    def generate_verdict(self, signals, risk_score):
        if not signals:
            if risk_score > 0.5:
                # High risk but no specific signals caught? 
                return "This claim uses subtle linguistic patterns often found in high-engagement content, though specific markers were not isolated."
            return "This claim uses generally neutral language, facilitating objective verification."
        
        # Construct dynamic verdict
        names = [s["name"] for s in signals]
        
        if "Conspiracy Framing" in names:
            return "This claim employs conspiracy framing and suppression narratives to discourage critical verification."
        
        if "Causal Absolutes" in names and "Attribution Gap" in names:
            return "This claim makes definitive causal assertions without citing sources, which obscures the basis of the argument."
            
        if "Emotional Loading" in names:
            return "This claim relies on emotionally charged language to bypass critical analysis."
            
        # Fallback
        return f"This claim contains indicators of {names[0].lower()} which may influence interpretation independent of the facts."

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
            
        # NEW: Linguistic Signals & Verdict
        signals = self.detect_signals(text)
        
        # Boost risk score based on signals
        for signal in signals:
            if signal["name"] == "Conspiracy Framing":
                risk_score += 0.25
            elif signal["name"] == "Emotional Loading":
                risk_score += 0.15
            elif signal["name"] == "Causal Absolutes":
                risk_score += 0.15
            elif signal["name"] == "Attribution Gap":
                risk_score += 0.10
        
        final_risk = min(risk_score, 0.99)
        verdict = self.generate_verdict(signals, final_risk)
        
        return {
            "score": final_risk,
            "signals": signals,
            "verdict": verdict
        }
