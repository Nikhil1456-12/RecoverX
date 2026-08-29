"""ML API endpoints."""
from fastapi import APIRouter
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/train")
async def train_model():
    """Trigger ML model training."""
    # In production, this would trigger async training
    return {
        "status": "training_complete",
        "model": "recovery_probability",
        "version": "v1.0.0",
        "message": "Model training completed (using synthetic model in DEMO MODE)",
    }


@router.get("/status")
async def get_ml_status():
    """Get ML model status."""
    return {
        "models": [
            {
                "name": "recovery_probability",
                "version": "v1.0.0",
                "status": "active",
                "type": "synthetic_rule_based",
                "metrics": {
                    "accuracy": 0.82,
                    "auc_roc": 0.88,
                    "precision": 0.79,
                    "recall": 0.84,
                },
                "features": [
                    "amount", "payment_method", "failure_reason",
                    "customer_success_rate", "retry_count", "hour_of_day",
                    "customer_segment", "days_since_last_success",
                ],
            }
        ],
        "demo_mode": True,
    }
