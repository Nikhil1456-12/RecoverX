import os
import joblib
import pandas as pd
import numpy as np

MODELS_DIR = os.path.join(os.path.dirname(__file__), 'models')
LATEST_MODEL_PATH = os.path.join(MODELS_DIR, 'recovery_model_latest.joblib')

class FallbackModel:
    def predict_proba(self, X):
        # A simple rule-based fallback
        probs = []
        for _, row in X.iterrows():
            prob = 0.5
            if row.get('action') == 'whatsapp_message':
                prob += 0.1
            if row.get('retry_count', 0) > 3:
                prob -= 0.2
            probs.append([1-prob, prob])
        return np.array(probs)

def load_model():
    if os.path.exists(LATEST_MODEL_PATH):
        try:
            return joblib.load(LATEST_MODEL_PATH)
        except Exception:
            pass
    return FallbackModel()

def predict_batch(features_list: list[dict]) -> list[float]:
    if not features_list:
        return []
    model = load_model()
    df = pd.DataFrame(features_list)
    # Handle missing features
    expected_cols = [
        'payment_method', 'failure_reason', 'action', 'customer_segment',
        'amount', 'retry_count', 'hour', 'day_of_week', 'is_weekend',
        'customer_success_rate', 'customer_ltv', 'days_since_last_success',
        'action_cost', 'action_friction'
    ]
    for col in expected_cols:
        if col not in df.columns:
            if col in ['payment_method', 'failure_reason', 'action', 'customer_segment']:
                df[col] = 'unknown'
            else:
                df[col] = 0.0
                
    try:
        probs = model.predict_proba(df)[:, 1]
    except Exception:
        # If pipeline fails, use fallback
        probs = FallbackModel().predict_proba(df)[:, 1]
        
    return [float(max(0.01, min(0.98, p))) for p in probs]

def predict_recovery_probability(features_dict: dict) -> float:
    return predict_batch([features_dict])[0]
