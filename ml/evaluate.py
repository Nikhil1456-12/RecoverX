import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend'))

from app.ml.evaluate import evaluate

if __name__ == "__main__":
    evaluate()
