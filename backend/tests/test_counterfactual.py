import pytest
from app.services.counterfactual_engine import CounterfactualEngine, TransactionContext, ALL_ACTIONS

def test_simulate_all_actions():
    engine = CounterfactualEngine()
    context = TransactionContext(
        transaction_id="tx_1",
        customer_id="cust_1",
        amount=1000.0,
        payment_method="card",
        failure_reason="insufficient_funds"
    )
    results = engine.simulate(context)
    assert len(results) == len(ALL_ACTIONS)
    
    # Check that they are sorted by expected_net_recovery descending
    net_recoveries = [r.expected_net_recovery for r in results]
    assert net_recoveries == sorted(net_recoveries, reverse=True)

def test_upi_bank_timeout_prefers_delayed_retry():
    engine = CounterfactualEngine()
    context = TransactionContext(
        transaction_id="tx_1",
        customer_id="cust_1",
        amount=1000.0,
        payment_method="upi",
        failure_reason="bank_timeout"
    )
    result_now = engine.simulate_single(context, "retry_now")
    result_15m = engine.simulate_single(context, "retry_15m")
    result_45m = engine.simulate_single(context, "retry_45m")
    
    assert result_15m.recovery_probability > result_now.recovery_probability
    assert result_45m.recovery_probability > result_now.recovery_probability

def test_expired_card_prefers_notification():
    engine = CounterfactualEngine()
    context = TransactionContext(
        transaction_id="tx_1",
        customer_id="cust_1",
        amount=1000.0,
        payment_method="card",
        failure_reason="expired_card"
    )
    result_retry = engine.simulate_single(context, "retry_now")
    result_whatsapp = engine.simulate_single(context, "whatsapp")
    
    assert result_whatsapp.recovery_probability > result_retry.recovery_probability

def test_net_recovery_calculation():
    engine = CounterfactualEngine()
    context = TransactionContext(
        transaction_id="tx_1",
        customer_id="cust_1",
        amount=1000.0,
        payment_method="card",
        failure_reason="network_error"
    )
    result = engine.simulate_single(context, "whatsapp")
    
    # Expected Revenue = probability * amount
    expected_revenue = result.recovery_probability * 1000.0
    # Cost = 2.5
    cost = 2.5
    # Friction cost = friction_score (0.15) * 1000.0 * 0.1
    friction_cost = 0.15 * 1000.0 * 0.1
    
    expected_net = expected_revenue - cost - friction_cost
    assert round(result.expected_net_recovery, 2) == round(expected_net, 2)

def test_explanation_generation():
    engine = CounterfactualEngine()
    context = TransactionContext(
        transaction_id="tx_1",
        customer_id="cust_1",
        amount=1000.0,
        payment_method="card",
        failure_reason="network_error"
    )
    result = engine.simulate_single(context, "retry_now")
    assert isinstance(result.explanation, str)
    assert len(result.explanation) > 0
    assert "Network error" in result.explanation or "probability" in result.explanation
