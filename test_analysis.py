import sys

# Mock Celery context to allow bind=True
class MockTask:
    def __init__(self):
        self.request = type('obj', (object,), {'id': 'mock_id'})()

try:
    from ml.workers.tasks import analyze_text_task
    import json
    
    # Analyze
    print("Starting analysis...")
    # Because it has bind=True, we have to pass a mock self if we don't call it via celery
    # But analyze_text_task in the code just uses self. So we can just call it with mock self
    result = analyze_text_task(MockTask(), text="Russia attacked Ukraine")
    
    print("\nFINAL RESULT:")
    print(json.dumps(result, indent=2))
except Exception as e:
    import traceback
    traceback.print_exc()
