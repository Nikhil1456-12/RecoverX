import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_and_metrics():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"
    
    response = client.get("/metrics")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_dashboard_summary():
    response = client.get("/api/dashboard/summary")
    assert response.status_code == 200

def test_dashboard_trends():
    response = client.get("/api/dashboard/trends?days=30")
    assert response.status_code == 200

def test_revenue_leakage():
    response = client.get("/api/dashboard/leakage")
    assert response.status_code == 200
    
    response2 = client.get("/api/revenue-leakage/leakage")
    assert response2.status_code == 200

def test_transactions_list():
    response = client.get("/api/transactions")
    assert response.status_code == 200
    assert "transactions" in response.json()

def test_transaction_detail():
    response = client.get("/api/transactions/TXN_000001")
    # Could be 404 if not seeded, but endpoint exists
    assert response.status_code in [200, 404]

def test_simulate_endpoint():
    response = client.post("/api/transactions/TXN_000001/simulate")
    assert response.status_code in [200, 404]

def test_recover_endpoint():
    response = client.post("/api/transactions/TXN_000001/recover")
    assert response.status_code in [200, 404]

def test_experiments():
    response = client.get("/api/experiments")
    assert response.status_code == 200
    
    # Optional test run
    # response2 = client.post("/api/experiments/run")
    # assert response2.status_code in [200, 422]

def test_audit_logs():
    response = client.get("/api/audit")
    assert response.status_code == 200

def test_recovery_actions():
    response = client.get("/api/recovery-actions")
    assert response.status_code == 200

def test_razorpay_webhook_demo():
    payload = {
        "event": "payment.failed",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_123",
                    "amount": 1000,
                    "currency": "INR",
                    "status": "failed",
                    "error_code": "BAD_REQUEST_ERROR",
                    "error_description": "Payment failed"
                }
            }
        }
    }
    response = client.post("/api/webhooks/razorpay", json=payload)
    assert response.status_code in [200, 422]
