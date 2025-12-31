import torch
import json
import os
import numpy as np
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from torch.nn import functional as F

MODEL_DIR = "./ml/models/fine_tuned_roberta"
CALIBRATION_FILE = "./ml/models/calibration.json"

class ModelCalibrator:
    def __init__(self, model_path=MODEL_DIR):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = AutoModelForSequenceClassification.from_pretrained(model_path).to(self.device)
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.temperature = 1.0
        
    def calibrate(self, validation_texts, validation_labels):
        """
        Learn temperature scaling parameter T to minimize NLL on validation set.
        """
        print("Calibrating model probabilities...")
        self.model.eval()
        logits_list = []
        labels_list = []
        
        # Get logits
        with torch.no_grad():
            for text, label in zip(validation_texts, validation_labels):
                inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512).to(self.device)
                outputs = self.model(**inputs)
                logits_list.append(outputs.logits)
                labels_list.append(label)
                
        logits = torch.cat(logits_list).to(self.device)
        labels = torch.tensor(labels_list).to(self.device)
        
        # Optimize temperature
        # Simple search or LBFGS
        temperature = torch.nn.Parameter(torch.ones(1).to(self.device))
        optimizer = torch.optim.LBFGS([temperature], lr=0.01, max_iter=50)
        
        def eval():
            optimizer.zero_grad()
            loss = F.cross_entropy(logits / temperature, labels)
            loss.backward()
            return loss
            
        optimizer.step(eval)
        
        self.temperature = temperature.item()
        print(f"Calibrated Temperature: {self.temperature:.4f}")
        
        # Save
        with open(CALIBRATION_FILE, 'w') as f:
            json.dump({"temperature": self.temperature}, f)
            
    def predict_calibrated(self, text):
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True).to(self.device)
        with torch.no_grad():
            outputs = self.model(**inputs)
            scaled_logits = outputs.logits / self.temperature
            probs = F.softmax(scaled_logits, dim=-1)
        return probs.cpu().numpy()[0]

if __name__ == "__main__":
    # Dummy calibration
    calibrator = ModelCalibrator(model_path="roberta-base") # Use base if fine-tuned not exists
    texts = ["Test sentence 1", "Test sentence 2"]
    labels = [0, 1]
    # calibrator.calibrate(texts, labels) # Needs real data
    print("Calibration script ready.")
