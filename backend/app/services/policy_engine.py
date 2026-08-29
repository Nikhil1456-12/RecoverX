"""Policy Engine — Deterministic safety and policy enforcement.

This engine MUST run before every external recovery action.
It enforces rules that the AI/ML layer cannot override.

All policy decisions are deterministic and auditable.
"""
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class PolicyConfig:
    """Merchant-configurable policy rules."""
    max_retries_per_transaction: int = 3
    retry_cooldown_minutes: int = 15
    max_recovery_attempts_per_customer: int = 5
    daily_recovery_budget: float = 5000.0
    max_auto_recovery_amount: float = 50000.0
    allowed_channels: list[str] = field(default_factory=lambda: [
        'retry_now', 'retry_15m', 'retry_45m',
        'whatsapp', 'payment_link', 'sms', 'email',
        'human_escalation', 'stop'
    ])
    dnd_enabled: bool = True
    auto_recovery_enabled: bool = True
    min_confidence_threshold: float = 0.5
    max_repeated_failures: int = 5


@dataclass
class PolicyContext:
    """Context for policy evaluation."""
    transaction_id: str
    customer_id: str
    amount: float
    action: str
    action_cost: float
    retry_count: int = 0
    customer_recovery_attempts: int = 0
    customer_is_dnd: bool = False
    last_action_at: Optional[datetime] = None
    budget_used_today: float = 0.0
    confidence: float = 0.8
    previous_failures: int = 0
    idempotency_key: Optional[str] = None
    existing_idempotency_keys: list[str] = field(default_factory=list)


@dataclass
class PolicyDecisionResult:
    """Result of policy evaluation."""
    approved: bool
    reason: str
    policies_evaluated: list[str] = field(default_factory=list)
    violated_policy: Optional[str] = None
    details: dict = field(default_factory=dict)


class PolicyEngine:
    """Deterministic policy enforcement engine.
    
    Evaluates actions against a set of rules and returns
    an approve/deny decision with explanation.
    
    Rules are evaluated in priority order. First violation stops evaluation.
    """
    
    def __init__(self, config: PolicyConfig | None = None):
        self.config = config or PolicyConfig()
    
    def evaluate(self, context: PolicyContext) -> PolicyDecisionResult:
        """Evaluate a proposed recovery action against all policies.
        
        Returns:
            PolicyDecisionResult with approval status and reason
        """
        policies_evaluated = []
        
        # Rule 1: Check if action is in allowed channels
        policies_evaluated.append('channel_allowlist')
        if context.action not in self.config.allowed_channels:
            return PolicyDecisionResult(
                approved=False,
                reason=f"Action '{context.action}' is not in allowed channels",
                policies_evaluated=policies_evaluated,
                violated_policy='channel_allowlist',
            )
        
        # Rule 2: Maximum retries per transaction
        policies_evaluated.append('max_retry')
        if context.retry_count >= self.config.max_retries_per_transaction:
            return PolicyDecisionResult(
                approved=False,
                reason=f"Maximum retry count ({self.config.max_retries_per_transaction}) exceeded for transaction",
                policies_evaluated=policies_evaluated,
                violated_policy='max_retry',
            )
        
        # Rule 3: Cooldown between retries
        policies_evaluated.append('retry_cooldown')
        if context.last_action_at and context.action.startswith('retry'):
            cooldown = timedelta(minutes=self.config.retry_cooldown_minutes)
            if datetime.utcnow() - context.last_action_at < cooldown:
                return PolicyDecisionResult(
                    approved=False,
                    reason=f"Retry cooldown ({self.config.retry_cooldown_minutes} min) not elapsed",
                    policies_evaluated=policies_evaluated,
                    violated_policy='retry_cooldown',
                )
        
        # Rule 4: Maximum recovery attempts per customer
        policies_evaluated.append('max_customer_attempts')
        if context.customer_recovery_attempts >= self.config.max_recovery_attempts_per_customer:
            return PolicyDecisionResult(
                approved=False,
                reason=f"Maximum recovery attempts per customer ({self.config.max_recovery_attempts_per_customer}) exceeded",
                policies_evaluated=policies_evaluated,
                violated_policy='max_customer_attempts',
            )
        
        # Rule 5: DND / opt-out check
        policies_evaluated.append('dnd_check')
        if self.config.dnd_enabled and context.customer_is_dnd:
            if context.action in ('whatsapp', 'sms', 'email', 'human_escalation'):
                return PolicyDecisionResult(
                    approved=False,
                    reason="Customer is on DND/opt-out list",
                    policies_evaluated=policies_evaluated,
                    violated_policy='dnd_check',
                )
        
        # Rule 6: Daily recovery budget
        policies_evaluated.append('budget_check')
        if context.budget_used_today + context.action_cost > self.config.daily_recovery_budget:
            return PolicyDecisionResult(
                approved=False,
                reason=f"Daily recovery budget (₹{self.config.daily_recovery_budget:,.0f}) would be exceeded",
                policies_evaluated=policies_evaluated,
                violated_policy='budget_check',
            )
        
        # Rule 7: Maximum transaction amount for automation
        policies_evaluated.append('amount_limit')
        if context.amount > self.config.max_auto_recovery_amount:
            if context.action != 'human_escalation':
                return PolicyDecisionResult(
                    approved=False,
                    reason=f"Transaction amount (₹{context.amount:,.0f}) exceeds auto-recovery limit (₹{self.config.max_auto_recovery_amount:,.0f}). Requires human escalation.",
                    policies_evaluated=policies_evaluated,
                    violated_policy='amount_limit',
                )
        
        # Rule 8: Confidence threshold
        policies_evaluated.append('confidence_check')
        if context.confidence < self.config.min_confidence_threshold:
            return PolicyDecisionResult(
                approved=False,
                reason=f"Model confidence ({context.confidence:.2f}) below threshold ({self.config.min_confidence_threshold})",
                policies_evaluated=policies_evaluated,
                violated_policy='confidence_check',
            )
        
        # Rule 9: Duplicate action prevention (idempotency)
        policies_evaluated.append('idempotency_check')
        if context.idempotency_key and context.idempotency_key in context.existing_idempotency_keys:
            return PolicyDecisionResult(
                approved=False,
                reason="Duplicate action detected (idempotency key already exists)",
                policies_evaluated=policies_evaluated,
                violated_policy='idempotency_check',
            )
        
        # Rule 10: Stop after repeated failures
        policies_evaluated.append('repeated_failure_check')
        if context.previous_failures >= self.config.max_repeated_failures:
            return PolicyDecisionResult(
                approved=False,
                reason=f"Too many previous failures ({context.previous_failures}). Recovery stopped.",
                policies_evaluated=policies_evaluated,
                violated_policy='repeated_failure_check',
            )
        
        # All policies passed
        return PolicyDecisionResult(
            approved=True,
            reason="All policies passed. Action approved.",
            policies_evaluated=policies_evaluated,
        )
    
    def check_stopping_rules(self, context: PolicyContext, recovery_probability: float, expected_net_recovery: float) -> tuple[bool, str]:
        """Check if recovery should be stopped.
        
        Returns:
            (should_stop, reason)
        """
        # Stop if max retries reached
        if context.retry_count >= self.config.max_retries_per_transaction:
            return True, "Maximum retries reached"
        
        # Stop if recovery probability too low
        if recovery_probability < 0.05:
            return True, f"Recovery probability too low ({recovery_probability*100:.1f}%)"
        
        # Stop if expected net recovery is negative
        if expected_net_recovery < 0:
            return True, f"Expected net recovery is negative (₹{expected_net_recovery:,.0f})"
        
        # Stop if customer opted out
        if context.customer_is_dnd:
            return True, "Customer has opted out (DND)"
        
        # Stop if budget exhausted
        if context.budget_used_today >= self.config.daily_recovery_budget:
            return True, "Daily recovery budget exhausted"
        
        # Stop if too many failures
        if context.previous_failures >= self.config.max_repeated_failures:
            return True, "Too many previous recovery failures"
        
        return False, "Continue recovery"
