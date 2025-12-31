import os
import torch
import numpy as np
from transformers import (
    AutoTokenizer, 
    AutoModelForSequenceClassification, 
    Trainer, 
    TrainingArguments
)
from datasets import load_dataset, Dataset

# Configuration
MODEL_NAME = "roberta-base"
OUTPUT_DIR = "./ml/models/fine_tuned_roberta"
NUM_LABELS = 3 # Low, Medium, High Risk
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

def compute_metrics(eval_pred):
    from sklearn.metrics import accuracy_score, f1_score
    predictions, labels = eval_pred
    predictions = np.argmax(predictions, axis=1)
    return {
        "accuracy": accuracy_score(labels, predictions),
        "f1": f1_score(labels, predictions, average="macro")
    }

def train_model():
    print(f"Starting training on {DEVICE}...")
    
    # 1. Load Data (Placeholder: In real usage, load 'liar' or 'fakenewsnet')
    # For prototype, we'll create a synthetic dummy dataset
    print("Loading synthetic dataset (Replace with real data)...")
    data = {
        "text": [
            "The earth is flat and nasa lies.", 
            "Breaking: Aliens found in Area 51!",
            "Water boils at 100 degrees Celsius.",
            "The president signed the new bill today."
        ] * 50,
        "label": [2, 2, 0, 0] * 50 # 0=Low, 1=Medium, 2=High
    }
    dataset = Dataset.from_dict(data)
    dataset = dataset.train_test_split(test_size=0.2)
    
    # 2. Tokenize
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    
    def tokenize_function(examples):
        return tokenizer(examples["text"], padding="max_length", truncation=True)
    
    tokenized_datasets = dataset.map(tokenize_function, batched=True)
    
    # 3. Model
    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME, num_labels=NUM_LABELS
    ).to(DEVICE)
    
    # 4. Training
    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        evaluation_strategy="epoch",
        save_strategy="epoch",
        learning_rate=2e-5,
        per_device_train_batch_size=8,
        per_device_eval_batch_size=8,
        num_train_epochs=3,
        weight_decay=0.01,
        logging_dir='./logs',
        load_best_model_at_end=True,
    )
    
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_datasets["train"],
        eval_dataset=tokenized_datasets["test"],
        compute_metrics=compute_metrics,
    )
    
    trainer.train()
    
    # 5. Save
    print(f"Saving model to {OUTPUT_DIR}")
    model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)

if __name__ == "__main__":
    train_model()
