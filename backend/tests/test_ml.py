import pytest
from app.services.counterfactual_engine import CounterfactualEngine, TransactionContext

def test_ml_predict_single():
    engine = CounterfactualEngine()
    context = TransactionContext(
        transaction_id="tx_1",
        customer_id="cust_1",
        amount=1000.0,
        payment_method="card",
        failure_reason="bank_timeout"
    )
    prob = engine._predict_synthetic(context, "retry_now")
    assert 0.01 <= prob <= 0.98

def test_ml_predict_batch():
    engine = CounterfactualEngine()
    context = TransactionContext(
        transaction_id="tx_1",
        customer_id="cust_1",
        amount=1000.0,
        payment_method="card",
        failure_reason="bank_timeout"
    )
    actions = ["retry_now", "retry_15m", "whatsapp"]
    results = engine.simulate(context, actions=actions)
    assert len(results) == len(actions)

def test_ml_feature_consistency():
    engine = CounterfactualEngine()
    context1 = TransactionContext(
        transaction_id="tx_1", customer_id="c_1", amount=500, payment_method="upi", failure_reason="bank_timeout"
    )
    context2 = TransactionContext(
        transaction_id="tx_1", customer_id="c_1", amount=500, payment_method="upi", failure_reason="bank_timeout"
    )
    
    prob1 = engine._predict_synthetic(context1, "whatsapp")
    prob2 = engine._predict_synthetic(context2, "whatsapp")
    
    assert prob1 == prob2

def test_ml_model_service_integration():
    engine = CounterfactualEngine()
    assert engine.model_version == "v1.0.0-synthetic"
    
    # Just checking it returns a list of scenario results
    context = TransactionContext(
        transaction_id="tx_test",
        customer_id="c_test",
        amount=2500,
        payment_method="upi",
        failure_reason="network_error"
    )
    scenarios = engine.simulate(context)
    assert len(scenarios) > 0
    assert hasattr(scenarios[0], "expected_net_recovery")
