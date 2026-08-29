import os
import sqlite3
import pandas as pd
import numpy as np
import json
import joblib
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import (
    accuracy_score, roc_auc_score, precision_score, 
    recall_score, f1_score, brier_score_loss, log_loss
)
from xgboost import XGBClassifier

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'recoverx.db')
MODELS_DIR = os.path.join(os.path.dirname(__file__), 'models')

def load_or_generate_data():
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql_query("SELECT * FROM recovery_events", conn)
        if len(df) < 100:
            raise ValueError("Not enough data in DB")
    except Exception:
        print("Generating synthetic data...")
        # Generate dummy data
        np.random.seed(42)
        n = 50000
        payment_methods = ['credit_card', 'debit_card', 'upi', 'netbanking']
        failure_reasons = ['insufficient_funds', 'network_error', 'authentication_failed']
        actions = ['email_reminder', 'sms_alert', 'whatsapp_message', 'in_app_notification']
        segments = ['high_value', 'medium_value', 'low_value']
        
        df = pd.DataFrame({
            'payment_method': np.random.choice(payment_methods, n),
            'failure_reason': np.random.choice(failure_reasons, n),
            'action': np.random.choice(actions, n),
            'customer_segment': np.random.choice(segments, n),
            'amount': np.random.exponential(100, n),
            'retry_count': np.random.randint(0, 5, n),
            'hour': np.random.randint(0, 24, n),
            'day_of_week': np.random.randint(0, 7, n),
            'is_weekend': np.random.randint(0, 2, n),
            'customer_success_rate': np.random.beta(5, 2, n),
            'customer_ltv': np.random.exponential(500, n),
            'days_since_last_success': np.random.exponential(10, n),
            'action_cost': np.random.uniform(0.1, 5.0, n),
            'action_friction': np.random.uniform(0.1, 1.0, n),
            'is_success': np.random.binomial(1, 0.3, n) # target
        })
    finally:
        conn.close()
    return df

def train():
    os.makedirs(MODELS_DIR, exist_ok=True)
    df = load_or_generate_data()
    
    categorical_features = ['payment_method', 'failure_reason', 'action', 'customer_segment']
    numeric_features = [
        'amount', 'retry_count', 'hour', 'day_of_week', 'is_weekend',
        'customer_success_rate', 'customer_ltv', 'days_since_last_success',
        'action_cost', 'action_friction'
    ]
    
    X = df[categorical_features + numeric_features]
    y = df['is_success']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), numeric_features),
            ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
        ])
    
    xgb = XGBClassifier(
        n_estimators=100,
        learning_rate=0.1,
        max_depth=5,
        random_state=42,
    )
    
    model = Pipeline(steps=[('preprocessor', preprocessor),
                            ('classifier', xgb)])
    
    calibrated_model = CalibratedClassifierCV(model, method='sigmoid', cv=5)
    calibrated_model.fit(X_train, y_train)
    
    y_pred = calibrated_model.predict(X_test)
    y_prob = calibrated_model.predict_proba(X_test)[:, 1]
    
    metrics = {
        'accuracy': accuracy_score(y_test, y_pred),
        'roc_auc': roc_auc_score(y_test, y_prob),
        'precision': precision_score(y_test, y_pred),
        'recall': recall_score(y_test, y_pred),
        'f1': f1_score(y_test, y_pred),
        'brier_score': brier_score_loss(y_test, y_prob),
        'log_loss': log_loss(y_test, y_prob),
        'trained_at': datetime.utcnow().isoformat()
    }
    
    model_path = os.path.join(MODELS_DIR, 'recovery_model_v1.joblib')
    latest_path = os.path.join(MODELS_DIR, 'recovery_model_latest.joblib')
    metadata_path = os.path.join(MODELS_DIR, 'model_metadata.json')
    
    joblib.dump(calibrated_model, model_path)
    joblib.dump(calibrated_model, latest_path)
    
    with open(metadata_path, 'w') as f:
        json.dump(metrics, f, indent=4)
        
    print(f"Model trained successfully! Metrics: {metrics}")

if __name__ == "__main__":
    train()
