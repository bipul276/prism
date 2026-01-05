import sys
import os

# Ensure we can import from core
sys.path.append("/app")

try:
    from ml.core.nli import StanceClassifier
except ImportError:
    # Fallback if path is different
    sys.path.append("/app/ml")
    from core.nli import StanceClassifier

def test_semantic_safety():
    print("Initializing NLI Model...")
    nli = StanceClassifier()
    
    print("\n--- Semantic Safety Test ---")
    
    danger_claims = [
        "Drinking this water results in mortality.",  # "mortality" synonym for death
        "The virus causes severe cardiac arrest.",    # Medical danger
        "Ingesting bleach is fatal.",                 # "fatal"
        "This activity leads to loss of life."        # "loss of life"
    ]
    
    benign_claims = [
        "The economy is slowing down.",
        "Cats are cute animals.",
        "The water is cold."
    ]
    
    failed = False
    
    for c in danger_claims:
        is_safe = nli.check_safety(c)
        print(f"Claim: '{c}' -> Dangerous? {is_safe}")
        if not is_safe:
            print("❌ FAILED: Should be dangerous.")
            failed = True
        else:
            print("✅ PASS")
            
    for c in benign_claims:
        is_safe = nli.check_safety(c)
        print(f"Claim: '{c}' -> Dangerous? {is_safe}")
        if is_safe:
            print("❌ FAILED: Should be benign.")
            failed = True
        else:
            print("✅ PASS")
            
    if failed:
        sys.exit(1)
    else:
        print("\n🎉 ALL TESTS PASSED: Future-Proof Safety Logic Verified.")

if __name__ == "__main__":
    test_semantic_safety()
