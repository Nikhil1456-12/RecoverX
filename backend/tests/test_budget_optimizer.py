import pytest
from app.services.budget_optimizer import BudgetOptimizer

def test_budget_allocation_within_limit():
    optimizer = BudgetOptimizer(daily_budget=10.0)
    candidates = [
        {"transaction_id": "1", "amount": 1000, "action": "whatsapp", "action_cost": 2.5, "expected_net_recovery": 50},
        {"transaction_id": "2", "amount": 1000, "action": "whatsapp", "action_cost": 2.5, "expected_net_recovery": 40},
        {"transaction_id": "3", "amount": 1000, "action": "human_escalation", "action_cost": 50.0, "expected_net_recovery": 100},
        {"transaction_id": "4", "amount": 1000, "action": "payment_link", "action_cost": 1.0, "expected_net_recovery": 20},
    ]
    result = optimizer.optimize(candidates)
    
    assert result.budget_used <= 10.0
    allocated_ids = [a.transaction_id for a in result.allocations]
    assert "3" not in allocated_ids  # Because cost 50 > budget 10
    assert "1" in allocated_ids
    assert "2" in allocated_ids

def test_free_actions_always_allocated():
    optimizer = BudgetOptimizer(daily_budget=5.0)
    candidates = [
        {"transaction_id": "1", "amount": 1000, "action": "human_escalation", "action_cost": 50.0, "expected_net_recovery": 100},
        {"transaction_id": "2", "amount": 1000, "action": "retry_now", "action_cost": 0.0, "expected_net_recovery": 30},
    ]
    result = optimizer.optimize(candidates)
    
    allocated_ids = [a.transaction_id for a in result.allocations]
    assert "2" in allocated_ids  # Free action allocated
    assert "1" not in allocated_ids  # Over budget

def test_roi_greedy_ranking():
    optimizer = BudgetOptimizer(daily_budget=5.0)
    # ROI = net_recovery / max(cost, 0.01)
    # Candidate 1: cost 2.5, net 50 -> ROI 20
    # Candidate 2: cost 1.0, net 30 -> ROI 30
    candidates = [
        {"transaction_id": "1", "amount": 1000, "action": "whatsapp", "action_cost": 2.5, "expected_net_recovery": 50},
        {"transaction_id": "2", "amount": 1000, "action": "payment_link", "action_cost": 1.0, "expected_net_recovery": 30},
    ]
    result = optimizer.optimize(candidates)
    
    assert len(result.allocations) == 2
    # Check that highest ROI is first
    assert result.allocations[0].transaction_id == "2"
    assert result.allocations[1].transaction_id == "1"
