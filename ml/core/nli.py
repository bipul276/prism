from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import torch.nn.functional as F

class StanceClassifier:
    def __init__(self, model_name="cross-encoder/nli-distilroberta-base"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"NLI Stance Classifier loaded on {self.device}")
        
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name).to(self.device)
        self.model.eval()
        
        # Read label mapping from model config (ground truth)
        if hasattr(self.model.config, 'id2label') and self.model.config.id2label:
            raw_map = self.model.config.id2label
            self.label_mapping = {int(k): v.lower() for k, v in raw_map.items()}
            print(f"NLI Label Mapping (from model config): {self.label_mapping}")
        else:
            # Verified fallback for cross-encoder/nli-distilroberta-base
            self.label_mapping = {0: "contradiction", 1: "entailment", 2: "neutral"}
            print(f"NLI Label Mapping (hardcoded fallback): {self.label_mapping}")
        
        # Build reverse lookup: label_name -> index
        self.label_to_idx = {v: k for k, v in self.label_mapping.items()}
        
        # Validate we have the expected labels
        expected = {"contradiction", "entailment", "neutral"}
        actual = set(self.label_mapping.values())
        if not expected.issubset(actual):
            print(f"⚠️ NLI WARNING: Expected labels {expected}, got {actual}. Stance may be inaccurate.")

    def predict(self, claim, evidence):
        """
        Predict stance of evidence toward a claim.
        Premise=Evidence, Hypothesis=Claim → "Given this evidence, is the claim true?"
        """
        inputs = self.tokenizer(
            evidence, 
            claim, 
            return_tensors="pt", 
            truncation=True, 
            max_length=512
        ).to(self.device)
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            probs = F.softmax(outputs.logits, dim=-1)
        
        # Use the verified label mapping indices
        idx_contra = self.label_to_idx.get("contradiction", 0)
        idx_entail = self.label_to_idx.get("entailment", 1)
        idx_neutral = self.label_to_idx.get("neutral", 2)
            
        p_contra = probs[0][idx_contra].item()
        p_entail = probs[0][idx_entail].item()
        p_neutral = probs[0][idx_neutral].item()
        
        # FIX: Raised contradiction threshold from 0.33 → 0.50
        # 0.33 was too low — unrelated articles about different events (e.g. Iran/Israel 
        # vs Russia/Ukraine) often score 0.35-0.45 contradiction just because they describe
        # a DIFFERENT event with similar keywords ("attack", "war"), causing false "refutes".
        if p_contra > 0.50 and p_contra > p_entail:
             label = "refutes"
        elif p_entail > 0.50:
             label = "supports"
        else:
             label = "neutral"
             
        return {
            "label": label,
            "confidence": max(p_contra, p_entail, p_neutral),
            "distribution": {
                "refutes": p_contra,
                "supports": p_entail,
                "neutral": p_neutral
            }
        }

    def is_topically_relevant(self, claim, evidence):
        """
        Quick semantic check: does the evidence even relate to the same topic as the claim?
        Uses entailment as a proxy for topical overlap.
        Returns (is_relevant: bool, relevance_score: float)
        """
        # Check: "Given the claim, does the evidence discuss the same topic?"
        # Higher entailment + lower contradiction = topically aligned
        inputs = self.tokenizer(
            claim, 
            evidence, 
            return_tensors="pt", 
            truncation=True, 
            max_length=512
        ).to(self.device)
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            probs = F.softmax(outputs.logits, dim=-1)
        
        idx_contra = self.label_to_idx.get("contradiction", 0)
        idx_entail = self.label_to_idx.get("entailment", 1)
        idx_neutral = self.label_to_idx.get("neutral", 2)
        
        p_contra = probs[0][idx_contra].item()
        p_entail = probs[0][idx_entail].item()
        p_neutral = probs[0][idx_neutral].item()
        
        # Relevance = entailment + neutral (both indicate topical connection)
        # Contradiction alone isn't enough — it could mean "same topic, opposite claim" (relevant!)
        # OR "completely different topic" (irrelevant)
        relevance_score = p_entail + p_neutral * 0.5
        
        # If contradiction is very high AND entailment is very low, 
        # it's likely about a completely different event
        if p_contra > 0.7 and p_entail < 0.15:
            return False, relevance_score
        
        # Threshold: at least some topical overlap
        return relevance_score > 0.35, relevance_score

    def check_safety(self, text):
        """
        Zero-shot semantic check for safety-critical content.
        Hypothesis: "This text describes a situation involving physical danger, health risks, or death."
        """
        hypothesis = "This text describes a situation involving physical danger, health risks, or death."
        
        # Order: (Premise, Hypothesis)
        inputs = self.tokenizer(
            text, 
            hypothesis, 
            return_tensors="pt", 
            truncation=True, 
            max_length=512
        ).to(self.device)
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            probs = F.softmax(outputs.logits, dim=-1)
            
        idx_entail = self.label_to_idx.get("entailment", 1)
        p_entail = probs[0][idx_entail].item()
        
        print(f"DEBUG: Safety Check '{text[:30]}...' -> Entailment: {p_entail:.4f}")
        
        # Threshold: If > 50% sure it entails danger
        return p_entail > 0.5
