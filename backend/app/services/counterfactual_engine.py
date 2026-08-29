"""Counterfactual Engine — Simulates recovery outcomes for different actions.

This is the core intelligence of RecoverX. For a given transaction and customer,
it predicts the recovery probability, expected revenue, cost, and friction
for each possible recovery action.

Architecture: Designed so the synthetic model can be replaced by real
causal/counterfactual models (e.g., uplift models, causal forests) in production.
"""
import json
import logging
import math
import random
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


# Action definitions with costs and friction scores
ACTION_DEFINITIONS = {
    'retry_now': {'cost': 0, 'friction': 0.02, 'label': 'Retry Immediately', 'description': 'Retry the payment immediately'},
    'retry_15m': {'cost': 0, 'friction': 0.05, 'label': 'Retry in 15 min', 'description': 'Retry payment after 15 minute cooldown'},
    'retry_45m': {'cost': 0, 'friction': 0.08, 'label': 'Retry in 45 min', 'description': 'Retry payment after 45 minute delay'},
    'whatsapp': {'cost': 2.5, 'friction': 0.15, 'label': 'WhatsApp', 'description': 'Send WhatsApp payment link'},
    'payment_link': {'cost': 1.0, 'friction': 0.12, 'label': 'Payment Link', 'description': 'Generate and share payment link'},
    'sms': {'cost': 0.5, 'friction': 0.18, 'label': 'SMS', 'description': 'Send SMS reminder with payment link'},
    'email': {'cost': 0.2, 'friction': 0.10, 'label': 'Email', 'description': 'Send email with payment details'},
    'human_escalation': {'cost': 50.0, 'friction': 0.25, 'label': 'Human Escalation', 'description': 'Escalate to human recovery agent'},
    'stop': {'cost': 0, 'friction': 0, 'label': 'Stop Recovery', 'description': 'Stop recovery attempts'},
}

ALL_ACTIONS = list(ACTION_DEFINITIONS.keys())


@dataclass
class TransactionContext:
    """Structured context for counterfactual simulation."""
    transaction_id: str
    customer_id: str
    amount: float
    payment_method: str
    failure_reason: str
    retry_count: int = 0
    hour_of_day: int = 12
    day_of_week: int = 0
    is_weekend: bool = False
    customer_segment: str = 'returning'
    customer_success_rate: float = 0.8
    customer_lifetime_value: float = 0.0
    days_since_last_success: float = 5.0
    previous_recovery_attempts: int = 0
    merchant_budget_remaining: float = 5000.0
    transaction_type: str = 'payment'


@dataclass
class ScenarioResult:
    """Result of a counterfactual scenario simulation."""
    action: str
    action_label: str
    recovery_probability: float
    expected_revenue: float
    intervention_cost: float
    friction_score: float
    friction_cost: float
    expected_net_recovery: float
    confidence: float
    explanation: str
    is_recommended: bool = False


class CounterfactualEngine:
    """Simulates counterfactual recovery scenarios.
    
    For each candidate action, estimates:
    - Recovery probability
    - Expected recovered revenue
    - Intervention cost
    - Customer friction cost
    - Expected net recovery
    - Confidence score
    - Explanation
    
    The current implementation uses a rule-based model with controlled patterns.
    This can be replaced by real ML models (XGBoost, causal forests, etc.)
    by overriding the predict_recovery_probability method.
    """
    
    def __init__(self, ml_model=None):
        """Initialize with optional ML model for predictions."""
        self.ml_model = ml_model
        self._model_version = "v1.0.0-synthetic"
    
    def simulate(self, context: TransactionContext, actions: list[str] | None = None) -> list[ScenarioResult]:
        """Simulate all candidate actions for a transaction.
        
        Args:
            context: Transaction context with all features
            actions: Optional list of actions to simulate. Defaults to all.
            
        Returns:
            List of ScenarioResult, sorted by expected_net_recovery descending
        """
        if actions is None:
            actions = ALL_ACTIONS
        
        results = []
        for action in actions:
            result = self._simulate_action(context, action)
            results.append(result)
        
        # Sort by expected net recovery (descending)
        results.sort(key=lambda r: r.expected_net_recovery, reverse=True)
        
        # Mark the best action as recommended (excluding 'stop')
        non_stop = [r for r in results if r.action != 'stop']
        if non_stop:
            non_stop[0].is_recommended = True
        
        return results
    
    def simulate_single(self, context: TransactionContext, action: str) -> ScenarioResult:
        """Simulate a single action for a transaction."""
        return self._simulate_action(context, action)
    
    def _simulate_action(self, context: TransactionContext, action: str) -> ScenarioResult:
        """Simulate a single action and return the result."""
        action_def = ACTION_DEFINITIONS.get(action, ACTION_DEFINITIONS['retry_now'])
        
        # Predict recovery probability
        if self.ml_model is not None:
            recovery_prob = self._predict_with_model(context, action)
        else:
            recovery_prob = self._predict_synthetic(context, action)
        
        # Calculate economics
        expected_revenue = recovery_prob * context.amount
        intervention_cost = action_def['cost']
        friction_score = action_def['friction']
        friction_cost = friction_score * context.amount * 0.1  # 10% of amount weighted by friction
        expected_net_recovery = expected_revenue - intervention_cost - friction_cost
        
        # Confidence based on data availability
        confidence = self._calculate_confidence(context, action)
        
        # Generate explanation
        explanation = self._generate_explanation(context, action, recovery_prob, expected_net_recovery)
        
        return ScenarioResult(
            action=action,
            action_label=action_def['label'],
            recovery_probability=round(recovery_prob, 4),
            expected_revenue=round(expected_revenue, 2),
            intervention_cost=intervention_cost,
            friction_score=round(friction_score, 3),
            friction_cost=round(friction_cost, 2),
            expected_net_recovery=round(expected_net_recovery, 2),
            confidence=round(confidence, 3),
            explanation=explanation,
        )
    
    def _predict_with_model(self, context: TransactionContext, action: str) -> float:
        """Use ML model for prediction. Override for production."""
        # TODO: Implement actual ML model prediction
        # features = self._extract_features(context, action)
        # return self.ml_model.predict_proba(features)[0][1]
        return self._predict_synthetic(context, action)
    
    def _predict_synthetic(self, context: TransactionContext, action: str) -> float:
        """Rule-based synthetic prediction with controlled patterns."""
        # Base recovery rate by failure reason
        base_rates = {
            'bank_timeout': 0.65,
            'insufficient_funds': 0.35,
            'bank_decline': 0.25,
            'expired_card': 0.20,
            'incorrect_details': 0.15,
            'network_error': 0.70,
            'authentication_failure': 0.40,
            'checkout_abandonment': 0.30,
            'subscription_failure': 0.55,
            'invoice_overdue': 0.45,
        }
        
        base = base_rates.get(context.failure_reason, 0.3)
        
        # Pattern 1: UPI bank timeout — delayed retry is much better
        if context.failure_reason == 'bank_timeout' and context.payment_method == 'upi':
            if action == 'retry_now':
                base *= 0.55
            elif action == 'retry_15m':
                base *= 1.15
            elif action == 'retry_45m':
                base *= 1.35
            elif action == 'whatsapp':
                base *= 1.10
        
        # Pattern 2: Expired card needs card update, not retry
        if context.failure_reason == 'expired_card':
            if action in ('retry_now', 'retry_15m', 'retry_45m'):
                base *= 0.15
            elif action in ('whatsapp', 'payment_link', 'email'):
                base *= 1.8
            elif action == 'human_escalation':
                base *= 2.0
        
        # Pattern 3: Network errors — immediate retry works well
        if context.failure_reason == 'network_error':
            if action == 'retry_now':
                base *= 1.5
            elif action == 'retry_15m':
                base *= 1.3
        
        # Pattern 4: Customer segment
        segment_mult = {'new': 0.7, 'returning': 1.1, 'premium': 1.2, 'high_value': 1.15}
        base *= segment_mult.get(context.customer_segment, 1.0)
        
        # Pattern 5: Customer history
        if context.customer_success_rate > 0.9:
            base *= 1.25
        elif context.customer_success_rate > 0.7:
            base *= 1.1
        elif context.customer_success_rate < 0.3:
            base *= 0.6
        
        # Pattern 6: Amount effects
        if context.amount < 500:
            base *= 0.85
        elif context.amount > 20000:
            base *= 1.05
        
        # Pattern 7: Retry fatigue
        if context.retry_count >= 3:
            base *= 0.4
        elif context.retry_count >= 2:
            base *= 0.65
        elif context.retry_count >= 1:
            base *= 0.85
        
        # Pattern 8: Time-of-day effects
        if 19 <= context.hour_of_day <= 22:
            if context.failure_reason == 'bank_timeout':
                base *= 0.9
            if action in ('retry_15m', 'retry_45m'):
                base *= 1.1
        elif 0 <= context.hour_of_day <= 6:
            base *= 0.75
        
        # Pattern 9: Recency
        if context.days_since_last_success < 3:
            base *= 1.1
        elif context.days_since_last_success > 30:
            base *= 0.7
        
        # Pattern 10: Human escalation boost
        if action == 'human_escalation':
            base = min(base * 1.4, 0.95)
        
        # Pattern 11: Stop
        if action == 'stop':
            return 0.0
        
        return max(0.01, min(0.98, base))
    
    def _calculate_confidence(self, context: TransactionContext, action: str) -> float:
        """Calculate confidence score based on data quality."""
        confidence = 0.7
        
        # Higher confidence for customers with more history
        if context.customer_success_rate > 0:
            confidence += 0.1
        
        # Lower confidence for new customers
        if context.customer_segment == 'new':
            confidence -= 0.1
        
        # Higher confidence for common failure reasons
        common_failures = ['bank_timeout', 'insufficient_funds', 'network_error']
        if context.failure_reason in common_failures:
            confidence += 0.05
        
        # Lower confidence for high retry counts (less data)
        if context.retry_count > 2:
            confidence -= 0.1
        
        return max(0.5, min(0.95, confidence))
    
    def _generate_explanation(self, context: TransactionContext, action: str, prob: float, net_recovery: float) -> str:
        """Generate human-readable explanation for the prediction."""
        parts = []
        
        # Action-specific reasoning
        if action == 'retry_now':
            if context.failure_reason == 'network_error':
                parts.append(f"Network errors typically resolve quickly; immediate retry has {prob*100:.0f}% success rate.")
            elif context.failure_reason == 'bank_timeout' and context.payment_method == 'upi':
                parts.append(f"Immediate retry for UPI bank timeouts has lower success ({prob*100:.0f}%) — bank may still be congested.")
            else:
                parts.append(f"Immediate retry predicted {prob*100:.0f}% recovery probability.")
        
        elif action in ('retry_15m', 'retry_45m'):
            delay = '15 minutes' if action == 'retry_15m' else '45 minutes'
            if context.failure_reason == 'bank_timeout':
                parts.append(f"Delayed retry ({delay}) allows bank timeout to resolve. {prob*100:.0f}% predicted success.")
            else:
                parts.append(f"Retry after {delay}: {prob*100:.0f}% recovery probability.")
        
        elif action == 'whatsapp':
            parts.append(f"WhatsApp notification with payment link: {prob*100:.0f}% recovery rate.")
            if context.failure_reason == 'expired_card':
                parts.append("Customer can update payment method via link.")
        
        elif action == 'payment_link':
            parts.append(f"Fresh payment link enables customer-initiated recovery: {prob*100:.0f}%.")
        
        elif action == 'human_escalation':
            parts.append(f"Human escalation: {prob*100:.0f}% success but higher cost (₹{ACTION_DEFINITIONS['human_escalation']['cost']}).")
            if context.amount > 10000:
                parts.append(f"Justified for high-value transaction (₹{context.amount:,.0f}).")
        
        elif action == 'stop':
            parts.append("Stop recovery: further attempts unlikely to succeed or cost exceeds expected value.")
        
        else:
            parts.append(f"{action}: {prob*100:.0f}% recovery probability.")
        
        # Customer context
        if context.customer_success_rate > 0.9:
            parts.append(f"Customer has strong payment history ({context.customer_success_rate*100:.0f}% success rate).")
        elif context.customer_success_rate < 0.5:
            parts.append(f"Customer has low payment reliability ({context.customer_success_rate*100:.0f}% success rate).")
        
        # Net recovery context
        if net_recovery > 0:
            parts.append(f"Expected net recovery: ₹{net_recovery:,.0f}.")
        else:
            parts.append(f"Negative expected net recovery (₹{net_recovery:,.0f}).")
        
        return ' '.join(parts)
    
    @property
    def model_version(self) -> str:
        return self._model_version
