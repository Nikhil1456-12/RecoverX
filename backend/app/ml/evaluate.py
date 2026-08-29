import os
import json
from sklearn.metrics import classification_report, confusion_matrix, roc_curve
from sklearn.calibration import calibration_curve
from app.ml.train import load_or_generate_data, DB_PATH
from app.ml.predict import load_model
from sklearn.model_selection import train_test_split

EVAL_DIR = os.path.join(os.path.dirname(__file__), 'evaluation')

def evaluate():
    os.makedirs(EVAL_DIR, exist_ok=True)
    df = load_or_generate_data()
    _, test_df = train_test_split(df, test_size=0.2, random_state=42)
    
    y_test = test_df['is_success'].tolist()
    
    features = test_df.drop('is_success', axis=1).to_dict('records')
    model = load_model()
    
    from app.ml.predict import predict_batch
    y_prob = predict_batch(features)
    y_pred = [1 if p > 0.5 else 0 for p in y_prob]
    
    fpr, tpr, _ = roc_curve(y_test, y_prob)
    prob_true, prob_pred = calibration_curve(y_test, y_prob, n_bins=10)
    
    report = {
        'confusion_matrix': confusion_matrix(y_test, y_pred).tolist(),
        'classification_report': classification_report(y_test, y_pred, output_dict=True),
        'roc_curve': {'fpr': fpr.tolist(), 'tpr': tpr.tolist()},
        'calibration_curve': {'prob_true': prob_true.tolist(), 'prob_pred': prob_pred.tolist()},
        'uplift_estimates': {'estimated_uplift_vs_random': sum(y_prob)/len(y_prob) - sum(y_test)/len(y_test)}
    }
    
    report_path = os.path.join(EVAL_DIR, 'eval_report.json')
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=4)
        
    print(f"Evaluation completed. Report saved to {report_path}")

if __name__ == "__main__":
    evaluate()
