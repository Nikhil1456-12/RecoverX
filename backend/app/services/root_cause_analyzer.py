"""Root Cause Analyzer — Categorizes and diagnoses payment failure causes."""
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


FAILURE_TAXONOMY = {
    'insufficient_funds': {
        'category': 'bank',
        'severity': 'medium',
        'description': 'Customer account has insufficient balance',
        'typical_resolution': 'Wait and retry, or notify customer',
    },
    'bank_timeout': {
        'category': 'bank',
        'severity': 'low',
        'description': 'Bank did not respond within timeout period',
        'typical_resolution': 'Delayed retry usually successful',
    },
    'bank_decline': {
        'category': 'bank',
        'severity': 'high',
        'description': 'Bank actively declined the transaction',
        'typical_resolution': 'Customer needs to contact bank',
    },
    'expired_card': {
        'category': 'card',
        'severity': 'high',
        'description': 'Payment card has expired',
        'typical_resolution': 'Customer must update payment method',
    },
    'incorrect_details': {
        'category': 'card',
        'severity': 'medium',
        'description': 'Incorrect card details provided',
        'typical_resolution': 'Customer needs to re-enter details',
    },
    'network_error': {
        'category': 'network',
        'severity': 'low',
        'description': 'Network connectivity issue during transaction',
        'typical_resolution': 'Immediate retry usually works',
    },
    'authentication_failure': {
        'category': 'authentication',
        'severity': 'medium',
        'description': 'OTP or 2FA authentication failed',
        'typical_resolution': 'Customer needs to retry authentication',
    },
    'checkout_abandonment': {
        'category': 'checkout',
        'severity': 'medium',
        'description': 'Customer abandoned checkout process',
        'typical_resolution': 'Send reminder with saved cart',
    },
    'subscription_failure': {
        'category': 'subscription',
        'severity': 'medium',
        'description': 'Recurring subscription payment failed',
        'typical_resolution': 'Retry with notification to update payment',
    },
    'invoice_overdue': {
        'category': 'invoice',
        'severity': 'low',
        'description': 'Invoice payment is overdue',
        'typical_resolution': 'Send payment reminder',
    },
}


@dataclass
class RootCauseResult:
    failure_reason: str
    category: str
    severity: str
    description: str
    typical_resolution: str
    confidence: float
    supporting_signals: dict


class RootCauseAnalyzer:
    """Analyzes and categorizes payment failure root causes."""
    
    def analyze(self, failure_reason: str, payment_method: str = '', 
                amount: float = 0, hour: int = 12, **kwargs) -> RootCauseResult:
        """Analyze root cause of a payment failure."""
        taxonomy = FAILURE_TAXONOMY.get(failure_reason, {
            'category': 'unknown',
            'severity': 'medium',
            'description': f'Unknown failure: {failure_reason}',
            'typical_resolution': 'Manual investigation required',
        })
        
        # Calculate confidence based on available signals
        confidence = 0.85
        signals = {'failure_reason': failure_reason}
        
        if payment_method:
            signals['payment_method'] = payment_method
            confidence += 0.05
        
        if amount > 0:
            signals['amount'] = amount
            confidence += 0.02
        
        if failure_reason in FAILURE_TAXONOMY:
            confidence += 0.05
        
        return RootCauseResult(
            failure_reason=failure_reason,
            category=taxonomy['category'],
            severity=taxonomy['severity'],
            description=taxonomy['description'],
            typical_resolution=taxonomy['typical_resolution'],
            confidence=min(confidence, 0.99),
            supporting_signals=signals,
        )
