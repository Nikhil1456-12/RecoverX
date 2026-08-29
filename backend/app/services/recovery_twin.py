"""Recovery Twin — Creates structured digital representations of at-risk transactions.

The Recovery Twin captures all relevant context about a failed transaction
and its customer, enabling the Counterfactual Engine to simulate recovery scenarios.
"""
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Any

from app.services.counterfactual_engine import (
    CounterfactualEngine, TransactionContext, ScenarioResult, ALL_ACTIONS
)
from app.services.policy_engine import PolicyEngine, PolicyContext, PolicyConfig

logger = logging.getLogger(__name__)


@dataclass
class TwinResult:
    """Complete recovery twin with scenarios and recommendation."""
    transaction_id: str
    customer_id: str
    amount: float
    payment_method: str
    failure_reason: str
    customer_context: dict
    time_context: dict
    risk_context: dict
    scenarios: list[ScenarioResult]
    recommended_action: str
    recommended_action_label: str
    explanation: str
    recovery_probability: float
    expected_net_recovery: float
    policy_decisions: dict[str, dict]


class RecoveryTwinService:
    """Builds recovery twins and orchestrates counterfactual simulation."""
    
    def __init__(self, counterfactual_engine: CounterfactualEngine | None = None, policy_engine: PolicyEngine | None = None):
        self.cf_engine = counterfactual_engine or CounterfactualEngine()
        self.policy_engine = policy_engine or PolicyEngine()
    
    def build_twin(
        self,
        transaction_id: str,
        customer_id: str,
        amount: float,
        payment_method: str,
        failure_reason: str,
        retry_count: int = 0,
        hour_of_day: int = 12,
        day_of_week: int = 0,
        customer_segment: str = 'returning',
        customer_success_rate: float = 0.8,
        customer_lifetime_value: float = 0.0,
        days_since_last_success: float = 5.0,
        customer_is_dnd: bool = False,
        budget_remaining: float = 5000.0,
        transaction_type: str = 'payment',
        previous_recovery_attempts: int = 0,
        actions: list[str] | None = None,
    ) -> TwinResult:
        """Build a recovery twin with full counterfactual analysis."""
        
        # Build transaction context
        context = TransactionContext(
            transaction_id=transaction_id,
            customer_id=customer_id,
            amount=amount,
            payment_method=payment_method,
            failure_reason=failure_reason,
            retry_count=retry_count,
            hour_of_day=hour_of_day,
            day_of_week=day_of_week,
            is_weekend=day_of_week >= 5,
            customer_segment=customer_segment,
            customer_success_rate=customer_success_rate,
            customer_lifetime_value=customer_lifetime_value,
            days_since_last_success=days_since_last_success,
            previous_recovery_attempts=previous_recovery_attempts,
            merchant_budget_remaining=budget_remaining,
            transaction_type=transaction_type,
        )
        
        # Run counterfactual simulation
        scenarios = self.cf_engine.simulate(context, actions)
        
        # Apply policy checks to each scenario
        policy_decisions = {}
        for scenario in scenarios:
            policy_ctx = PolicyContext(
                transaction_id=transaction_id,
                customer_id=customer_id,
                amount=amount,
                action=scenario.action,
                action_cost=scenario.intervention_cost,
                retry_count=retry_count,
                customer_recovery_attempts=previous_recovery_attempts,
                customer_is_dnd=customer_is_dnd,
                budget_used_today=5000.0 - budget_remaining,
                confidence=scenario.confidence,
            )
            decision = self.policy_engine.evaluate(policy_ctx)
            policy_decisions[scenario.action] = {
                'approved': decision.approved,
                'reason': decision.reason,
            }
        
        # Find best approved action
        recommended = None
        for scenario in scenarios:
            if scenario.action == 'stop':
                continue
            if policy_decisions.get(scenario.action, {}).get('approved', False):
                recommended = scenario
                break
        
        if recommended is None:
            # All actions rejected or only stop available
            recommended = next((s for s in scenarios if s.action == 'stop'), scenarios[-1])
        
        return TwinResult(
            transaction_id=transaction_id,
            customer_id=customer_id,
            amount=amount,
            payment_method=payment_method,
            failure_reason=failure_reason,
            customer_context={
                'segment': customer_segment,
                'success_rate': customer_success_rate,
                'lifetime_value': customer_lifetime_value,
                'is_dnd': customer_is_dnd,
            },
            time_context={
                'hour_of_day': hour_of_day,
                'day_of_week': day_of_week,
                'is_weekend': day_of_week >= 5,
            },
            risk_context={
                'retry_count': retry_count,
                'days_since_last_success': days_since_last_success,
                'previous_recovery_attempts': previous_recovery_attempts,
            },
            scenarios=scenarios,
            recommended_action=recommended.action,
            recommended_action_label=recommended.action_label,
            explanation=recommended.explanation,
            recovery_probability=recommended.recovery_probability,
            expected_net_recovery=recommended.expected_net_recovery,
            policy_decisions=policy_decisions,
        )
