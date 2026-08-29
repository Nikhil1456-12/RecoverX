import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend'))

from app.ml.predict import predict_batch

if __name__ == "__main__":
    print(predict_batch([{"amount": 1000, "action": "email_reminder"}]))
