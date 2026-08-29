"""Budget Optimizer — Optimizes recovery action allocation within a budget.

Given a set of at-risk transactions and a recovery budget,
finds the allocation that maximizes expected net recovery.
"""
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class AllocationItem:
    """A single allocation decision."""
    transaction_id: str
    amount: float
    action: str
    action_cost: float
    expected_recovery: float
    expected_net_recovery: float
    recovery_probability: float
    roi: float  # return on investment


@dataclass
class BudgetAllocation:
    """Complete budget allocation result."""
    total_budget: float
    budget_used: float
    budget_remaining: float
    total_expected_recovery: float
    total_expected_cost: float
    total_expected_net_recovery: float
    allocations: list[AllocationItem]
    unallocated_transactions: int
    allocation_by_action: dict[str, dict]


class BudgetOptimizer:
    """Optimizes recovery action allocation under budget constraints.
    
    Uses a greedy knapsack-style approach:
    1. For each transaction, compute the best action's ROI
    2. Sort by ROI descending
    3. Greedily allocate until budget is exhausted
    """
    
    def __init__(self, daily_budget: float = 5000.0):
        self.daily_budget = daily_budget
    
    def optimize(
        self,
        candidates: list[dict],
    ) -> BudgetAllocation:
        """Optimize budget allocation across candidate transactions.
        
        Args:
            candidates: List of dicts with:
                - transaction_id
                - amount
                - action (recommended action)
                - action_cost
                - expected_revenue
                - expected_net_recovery
                - recovery_probability
        """
        # Calculate ROI for each candidate
        items = []
        for c in candidates:
            cost = c.get('action_cost', 0)
            net = c.get('expected_net_recovery', 0)
            roi = net / max(cost, 0.01)  # avoid division by zero
            
            items.append(AllocationItem(
                transaction_id=c['transaction_id'],
                amount=c['amount'],
                action=c['action'],
                action_cost=cost,
                expected_recovery=c.get('expected_revenue', 0),
                expected_net_recovery=net,
                recovery_probability=c.get('recovery_probability', 0),
                roi=roi,
            ))
        
        # Sort by ROI descending (best bang for buck first)
        items.sort(key=lambda x: x.roi, reverse=True)
        
        # Greedy allocation
        allocated = []
        budget_used = 0.0
        unallocated = 0
        
        for item in items:
            if budget_used + item.action_cost <= self.daily_budget:
                allocated.append(item)
                budget_used += item.action_cost
            else:
                # If action is free (retries), still allocate
                if item.action_cost == 0:
                    allocated.append(item)
                else:
                    unallocated += 1
        
        # Summarize by action
        action_summary: dict[str, dict] = {}
        for item in allocated:
            if item.action not in action_summary:
                action_summary[item.action] = {
                    'count': 0,
                    'total_cost': 0,
                    'total_expected_recovery': 0,
                }
            action_summary[item.action]['count'] += 1
            action_summary[item.action]['total_cost'] += item.action_cost
            action_summary[item.action]['total_expected_recovery'] += item.expected_recovery
        
        total_expected_recovery = sum(a.expected_recovery for a in allocated)
        total_expected_cost = sum(a.action_cost for a in allocated)
        
        return BudgetAllocation(
            total_budget=self.daily_budget,
            budget_used=round(budget_used, 2),
            budget_remaining=round(self.daily_budget - budget_used, 2),
            total_expected_recovery=round(total_expected_recovery, 2),
            total_expected_cost=round(total_expected_cost, 2),
            total_expected_net_recovery=round(total_expected_recovery - total_expected_cost, 2),
            allocations=allocated,
            unallocated_transactions=unallocated,
            allocation_by_action=action_summary,
        )
