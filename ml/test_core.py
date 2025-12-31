from core.stylometry import StylometricAnalyzer
from core.rag import EvidenceRetriever
from core.nli import StanceClassifier
import os

def test_core():
    print("Testing core modules...")
    
    # 1. Stylometry
    print("\n--- Stylometry ---")
    stylometer = StylometricAnalyzer()
    text = "You won't believe this shocking secret exposed!"
    risk = stylometer.analyze(text)
    print(f"Text: {text}")
    print(f"Risk Score: {risk}")
    
    # 2. RAG
    print("\n--- RAG ---")
    try:
        retriever = EvidenceRetriever()
        evidence = retriever.retrieve("vaccines are dangerous")
        print(f"Retrieved {len(evidence)} items.")
        for ev in evidence:
            print(f"- {ev['text'][:50]}... (Score: {ev['score']})")
    except Exception as e:
        print(f"RAG failed (likely DB connection): {e}")

    # 3. NLI
    print("\n--- NLI ---")
    nli = StanceClassifier()
    claim = "The earth is flat."
    evidence_text = "The earth is an oblate spheroid."
    stance = nli.predict(claim, evidence_text)
    print(f"Claim: {claim}")
    print(f"Evidence: {evidence_text}")
    print(f"Stance: {stance}")

if __name__ == "__main__":
    test_core()
