import pytest
from datetime import datetime, timedelta
from app.services.policy_engine import PolicyEngine, PolicyConfig, PolicyContext

def test_policy_approved_normal_case():
    engine = PolicyEngine()
    context = PolicyContext(
        transaction_id="tx_123",
        customer_id="cust_123",
        amount=1000.0,
        action="retry_now",
        action_cost=0.0
    )
    result = engine.evaluate(context)
    assert result.approved is True
    assert result.violated_policy is None

def test_policy_max_retry_exceeded():
    engine = PolicyEngine(PolicyConfig(max_retries_per_transaction=3))
    context = PolicyContext(
        transaction_id="tx_123",
        customer_id="cust_123",
        amount=1000.0,
        action="retry_now",
        action_cost=0.0,
        retry_count=3
    )
    result = engine.evaluate(context)
    assert result.approved is False
    assert result.violated_policy == 'max_retry'

def test_policy_retry_cooldown():
    engine = PolicyEngine(PolicyConfig(retry_cooldown_minutes=15))
    last_action = datetime.utcnow() - timedelta(minutes=5)
    context = PolicyContext(
        transaction_id="tx_123",
        customer_id="cust_123",
        amount=1000.0,
        action="retry_15m",
        action_cost=0.0,
        last_action_at=last_action
    )
    result = engine.evaluate(context)
    assert result.approved is False
    assert result.violated_policy == 'retry_cooldown'

def test_policy_dnd_customer():
    engine = PolicyEngine(PolicyConfig(dnd_enabled=True))
    context = PolicyContext(
        transaction_id="tx_123",
        customer_id="cust_123",
        amount=1000.0,
        action="whatsapp",
        action_cost=2.5,
        customer_is_dnd=True
    )
    result = engine.evaluate(context)
    assert result.approved is False
    assert result.violated_policy == 'dnd_check'

def test_policy_budget_exceeded():
    engine = PolicyEngine(PolicyConfig(daily_recovery_budget=5000.0))
    context = PolicyContext(
        transaction_id="tx_123",
        customer_id="cust_123",
        amount=1000.0,
        action="human_escalation",
        action_cost=50.0,
        budget_used_today=4980.0
    )
    result = engine.evaluate(context)
    assert result.approved is False
    assert result.violated_policy == 'budget_check'

def test_policy_amount_limit():
    engine = PolicyEngine(PolicyConfig(max_auto_recovery_amount=50000.0))
    context = PolicyContext(
        transaction_id="tx_123",
        customer_id="cust_123",
        amount=60000.0,
        action="whatsapp",
        action_cost=2.5
    )
    result = engine.evaluate(context)
    assert result.approved is False
    assert result.violated_policy == 'amount_limit'

def test_policy_duplicate_idempotency():
    engine = PolicyEngine()
    context = PolicyContext(
        transaction_id="tx_123",
        customer_id="cust_123",
        amount=1000.0,
        action="whatsapp",
        action_cost=2.5,
        idempotency_key="idemp_1",
        existing_idempotency_keys=["idemp_1"]
    )
    result = engine.evaluate(context)
    assert result.approved is False
    assert result.violated_policy == 'idempotency_check'

def test_policy_stopping_rules():
    engine = PolicyEngine(PolicyConfig(max_retries_per_transaction=3))
    
    # Check max retries
    context = PolicyContext(transaction_id="1", customer_id="1", amount=100, action="retry_now", action_cost=0, retry_count=3)
    stop, reason = engine.check_stopping_rules(context, recovery_probability=0.5, expected_net_recovery=50)
    assert stop is True
    assert "retries" in reason.lower()
    
    # Check probability
    context.retry_count = 1
    stop, reason = engine.check_stopping_rules(context, recovery_probability=0.04, expected_net_recovery=50)
    assert stop is True
    assert "probability" in reason.lower()
    
    # Check negative expected net recovery
    stop, reason = engine.check_stopping_rules(context, recovery_probability=0.5, expected_net_recovery=-10)
    assert stop is True
    assert "negative" in reason.lower()
    
    # Check DND
    context.customer_is_dnd = True
    stop, reason = engine.check_stopping_rules(context, recovery_probability=0.5, expected_net_recovery=50)
    assert stop is True
    assert "dnd" in reason.lower()
