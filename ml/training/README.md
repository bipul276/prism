# ML Training Pipeline

## Overview
This directory contains scripts to fine-tune the PRISM stylized risk model.

## Datasets
Please download the following datasets and place them in `data/`:
1. **LIAR**: [Link](https://cs.ucsb.edu/~william/data/liar_dataset.zip) - For claim veracity.
2. **FakeNewsNet**: [Link](https://github.com/KaiDMML/FakeNewsNet) - For news article content.

## Commands

### 1. Train
Fine-tune RoBERTa on your dataset:
```bash
python train.py
```
Outputs: `../models/fine_tuned_roberta/`

### 2. Calibrate
Calibrate probabilities using temperature scaling:
```bash
python calibrate.py
```
Outputs: `../models/calibration.json`

### 3. Evaluate
Run metrics on a validation set:
```bash
python evaluate.py
```

## Structure
- `train.py`: Main training loop (HuggingFace Trainer).
- `calibrate.py`: Post-hoc calibration.
- `evaluate.py`: Generates confusion matrix and F1 scores.
