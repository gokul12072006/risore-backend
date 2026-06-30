import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.web_search import get_realtime_context

print("Testing steam sale query...")
context = get_realtime_context("steam sale")
print("RESULT:")
print(context)

print("\nTesting cache (should be instant)...")
import time
start = time.time()
context2 = get_realtime_context("steam sale")
print(f"Time taken: {time.time() - start:.4f} seconds")
print("Cache matched:", context == context2)
