import torch

class XAIExplainer:
    def __init__(self, stylometric_analyzer):
        self.analyzer = stylometric_analyzer
        self.device = self.analyzer.device
        self.model = self.analyzer.model
        print(f"XAI Explainer initialized (Custom Implementation)")

    def explain(self, text):
        # Lightweight gradient-based saliency (Input x Gradient)
        # This avoids 'captum' dependency issues on Windows/CPU
        
        inputs = self.analyzer.tokenizer(
            text, 
            return_tensors="pt", 
            truncation=True, 
            max_length=512
        ).to(self.device)
        
        # Enable gradients for embeddings
        # We need to find the embedding layer hook
        embeddings = None
        def hook_fn(module, input, output):
            nonlocal embeddings
            embeddings = output
            embeddings.retain_grad()

        # Hook into embeddings
        if hasattr(self.model, "roberta"):
            handle = self.model.roberta.embeddings.register_forward_hook(hook_fn)
        elif hasattr(self.model, "bert"):
            handle = self.model.bert.embeddings.register_forward_hook(hook_fn)
        else:
             # Fallback: cannot explain
            return []

        # Forward pass
        self.model.zero_grad()
        outputs = self.model(**inputs)
        logits = outputs.logits
        
        # Target class 1 (Risk/Fake)
        score = logits[0, 1]
        score.backward()
        
        # Input x Gradient
        grads = embeddings.grad
        # Sum across embedding dim
        # shape: [1, seq_len, hidden] -> [1, seq_len]
        # We use L2 norm or just sum * input?
        # Simpler: just norm of grads
        attr = grads.norm(dim=-1).squeeze(0)
        
        # Normalize
        attr = (attr - attr.min()) / (attr.max() - attr.min() + 1e-9)
        
        # Cleanup
        handle.remove()
        
        # Map tokens
        input_ids = inputs["input_ids"][0]
        tokens = self.analyzer.tokenizer.convert_ids_to_tokens(input_ids)
        
        sentiment_map = []
        for token, score in zip(tokens, attr):
            if token in ["<s>", "</s>", "<pad>", "[CLS]", "[SEP]", "[PAD]"]:
                continue
            sentiment_map.append({
                "token": token.replace("Ġ", ""),
                "score": score.item()
            })
            
        return sentiment_map
