"""Action Executor — Executes recovery actions through adapters.

Provides an abstract execution layer that decouples business logic
from payment gateway implementations. Supports mock/demo mode.
"""
import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class ActionResult:
    """Result of executing a recovery action."""
    success: bool
    action_type: str
    transaction_id: str
    message: str
    execution_time: datetime
    details: dict | None = None
    cost: float = 0.0
    idempotency_key: str = ""


class ActionAdapter(ABC):
    """Abstract base class for action adapters."""
    
    @abstractmethod
    async def execute(self, transaction_id: str, amount: float, **kwargs) -> ActionResult:
        pass


class MockRetryAdapter(ActionAdapter):
    """Mock adapter for payment retries in demo mode."""
    
    async def execute(self, transaction_id: str, amount: float, **kwargs) -> ActionResult:
        delay = kwargs.get('delay_minutes', 0)
        # In demo mode, simulate success based on probability
        import random
        success = random.random() < kwargs.get('recovery_probability', 0.5)
        
        return ActionResult(
            success=success,
            action_type=f'retry_{delay}m' if delay > 0 else 'retry_now',
            transaction_id=transaction_id,
            message=f"{'Payment recovered' if success else 'Retry failed'} (DEMO)",
            execution_time=datetime.utcnow(),
            details={'delay_minutes': delay, 'demo_mode': True},
            idempotency_key=f"retry_{transaction_id}_{uuid.uuid4().hex[:8]}",
        )


class MockNotificationAdapter(ActionAdapter):
    """Mock adapter for notifications (WhatsApp, SMS, Email) in demo mode."""
    
    async def execute(self, transaction_id: str, amount: float, **kwargs) -> ActionResult:
        channel = kwargs.get('channel', 'email')
        import random
        success = random.random() < kwargs.get('recovery_probability', 0.5)
        
        costs = {'whatsapp': 2.5, 'sms': 0.5, 'email': 0.2}
        
        return ActionResult(
            success=success,
            action_type=channel,
            transaction_id=transaction_id,
            message=f"{channel.title()} notification {'sent and payment recovered' if success else 'sent but no response'} (DEMO)",
            execution_time=datetime.utcnow(),
            details={'channel': channel, 'demo_mode': True},
            cost=costs.get(channel, 0),
            idempotency_key=f"{channel}_{transaction_id}_{uuid.uuid4().hex[:8]}",
        )


class MockPaymentLinkAdapter(ActionAdapter):
    """Mock adapter for payment link generation in demo mode."""
    
    async def execute(self, transaction_id: str, amount: float, **kwargs) -> ActionResult:
        import random
        success = random.random() < kwargs.get('recovery_probability', 0.5)
        link_id = uuid.uuid4().hex[:12]
        
        return ActionResult(
            success=success,
            action_type='payment_link',
            transaction_id=transaction_id,
            message=f"Payment link {'used and payment completed' if success else 'generated but unused'} (DEMO)",
            execution_time=datetime.utcnow(),
            details={'link_id': link_id, 'link_url': f'https://rzp.io/demo/{link_id}', 'demo_mode': True},
            cost=1.0,
            idempotency_key=f"plink_{transaction_id}_{uuid.uuid4().hex[:8]}",
        )


class MockEscalationAdapter(ActionAdapter):
    """Mock adapter for human escalation in demo mode."""
    
    async def execute(self, transaction_id: str, amount: float, **kwargs) -> ActionResult:
        import random
        success = random.random() < kwargs.get('recovery_probability', 0.7)
        
        return ActionResult(
            success=success,
            action_type='human_escalation',
            transaction_id=transaction_id,
            message=f"Human escalation {'resolved — payment recovered' if success else 'attempted — customer unresponsive'} (DEMO)",
            execution_time=datetime.utcnow(),
            details={'agent_id': f'AGENT_{random.randint(100, 999)}', 'demo_mode': True},
            cost=50.0,
            idempotency_key=f"escalation_{transaction_id}_{uuid.uuid4().hex[:8]}",
        )


class ActionExecutor:
    """Orchestrates action execution through the appropriate adapter."""
    
    def __init__(self, demo_mode: bool = True):
        self.demo_mode = demo_mode
        self._adapters = self._initialize_adapters()
    
    def _initialize_adapters(self) -> dict[str, ActionAdapter]:
        """Initialize action adapters based on mode."""
        if self.demo_mode:
            return {
                'retry_now': MockRetryAdapter(),
                'retry_15m': MockRetryAdapter(),
                'retry_45m': MockRetryAdapter(),
                'whatsapp': MockNotificationAdapter(),
                'sms': MockNotificationAdapter(),
                'email': MockNotificationAdapter(),
                'payment_link': MockPaymentLinkAdapter(),
                'human_escalation': MockEscalationAdapter(),
            }
        else:
            # Production adapters would be initialized here
            # e.g., RazorpayRetryAdapter, TwilioWhatsAppAdapter, etc.
            logger.warning("Production adapters not configured, falling back to mock")
            return self._initialize_adapters.__wrapped__(self)  # type: ignore
    
    async def execute(self, action: str, transaction_id: str, amount: float, **kwargs) -> ActionResult:
        """Execute a recovery action."""
        adapter = self._adapters.get(action)
        if adapter is None:
            return ActionResult(
                success=False,
                action_type=action,
                transaction_id=transaction_id,
                message=f"No adapter configured for action: {action}",
                execution_time=datetime.utcnow(),
            )
        
        try:
            # Add action-specific kwargs
            if action == 'retry_15m':
                kwargs['delay_minutes'] = 15
            elif action == 'retry_45m':
                kwargs['delay_minutes'] = 45
            elif action in ('whatsapp', 'sms', 'email'):
                kwargs['channel'] = action
            
            result = await adapter.execute(transaction_id, amount, **kwargs)
            logger.info(
                f"Action executed | action={action} | txn={transaction_id} | "
                f"success={result.success} | cost={result.cost}"
            )
            return result
        except Exception as e:
            logger.error(f"Action execution failed | action={action} | txn={transaction_id} | error={e}")
            return ActionResult(
                success=False,
                action_type=action,
                transaction_id=transaction_id,
                message=f"Execution error: {str(e)}",
                execution_time=datetime.utcnow(),
            )
