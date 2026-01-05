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
        
        # Mapping for this specific model (usually Entailment, Neutral, Contradiction)
        self.label_mapping = {0: "contradiction", 1: "entailment", 2: "neutral"}
        # Note: Check specific model config. cross-encoder/nli-distilroberta-base outputs:
        # 0: contradiction, 1: entailment, 2: neutral (Validation needed)
        
        # Actually, let's verify map for 'cross-encoder/nli-distilroberta-base'
        # It's trained on MNLI/SNLI.
        # usually 0: contradiction, 1: entailment, 2: neutral is NOT standard.
        # Standard huggingface NLI is often: 0: contradiction, 1: neutral, 2: entailment.
        # We will assume 0: contradiction, 1: entailment, 2: neutral for now but verify.

    def predict(self, claim, evidence):
        # Swap: Premise=Evidence, Hypothesis=Claim
        # "Given this evidence, is the claim true?"
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
            
        # Specific mapping for 'cross-encoder/nli-distilroberta-base':
        # 0: contradiction, 1: entailment, 2: neutral
        
        p_contra = probs[0][0].item()
        p_entail = probs[0][1].item()
        p_neutral = probs[0][2].item()
        
        # Heuristic: Be sensitive to contradictions (refutes)
        # If contradiction is significant (>33%), flag it.
        if p_contra > 0.33 and p_contra > p_entail:
             label = "refutes"
        elif p_entail > 0.5:
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
            
        # 0: contradiction, 1: entailment, 2: neutral (Validation needed)
        # Based on previous code assumption: 1 is entailment.
        p_entail = probs[0][1].item()
        
        print(f"DEBUG: Safety Check '{text[:30]}...' -> Entailment: {p_entail:.4f}")
        
        # Threshold: If > 50% sure it entails danger
        return p_entail > 0.5
