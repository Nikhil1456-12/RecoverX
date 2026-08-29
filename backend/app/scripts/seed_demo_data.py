"""Synthetic data generator for RecoverX demo.

Generates realistic payment transaction data with controlled patterns
that enable the ML model to learn meaningful recovery relationships.

Usage:
    python -m app.scripts.seed_demo_data
    python -m app.scripts.seed_demo_data --large
"""
import asyncio
import argparse
import random
import uuid
import json
import logging
import sys
import os
from datetime import datetime, timedelta
from typing import Optional
import math

# Add parent to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

# ============================================================
# CONFIGURATION
# ============================================================

PAYMENT_METHODS = ['upi', 'card', 'netbanking', 'wallet']
PAYMENT_METHOD_WEIGHTS = [0.45, 0.30, 0.15, 0.10]

FAILURE_REASONS = {
    'bank_timeout': {'weight': 0.25, 'category': 'bank', 'base_recovery': 0.65},
    'insufficient_funds': {'weight': 0.18, 'category': 'bank', 'base_recovery': 0.35},
    'bank_decline': {'weight': 0.12, 'category': 'bank', 'base_recovery': 0.25},
    'expired_card': {'weight': 0.10, 'category': 'card', 'base_recovery': 0.20},
    'incorrect_details': {'weight': 0.05, 'category': 'card', 'base_recovery': 0.15},
    'network_error': {'weight': 0.08, 'category': 'network', 'base_recovery': 0.70},
    'authentication_failure': {'weight': 0.07, 'category': 'authentication', 'base_recovery': 0.40},
    'checkout_abandonment': {'weight': 0.08, 'category': 'checkout', 'base_recovery': 0.30},
    'subscription_failure': {'weight': 0.04, 'category': 'subscription', 'base_recovery': 0.55},
    'invoice_overdue': {'weight': 0.03, 'category': 'invoice', 'base_recovery': 0.45},
}

CUSTOMER_SEGMENTS = ['new', 'returning', 'premium', 'high_value']
SEGMENT_WEIGHTS = [0.30, 0.40, 0.20, 0.10]

TRANSACTION_TYPES = ['payment', 'subscription', 'invoice']
TYPE_WEIGHTS = [0.70, 0.20, 0.10]

ACTION_TYPES = [
    'retry_now', 'retry_15m', 'retry_45m', 
    'whatsapp', 'payment_link', 'sms', 'email', 
    'human_escalation', 'stop'
]

ACTION_COSTS = {
    'retry_now': 0,
    'retry_15m': 0,
    'retry_45m': 0,
    'whatsapp': 2.5,
    'payment_link': 1.0,
    'sms': 0.5,
    'email': 0.2,
    'human_escalation': 50.0,
    'stop': 0,
}

ACTION_FRICTION = {
    'retry_now': 0.02,
    'retry_15m': 0.05,
    'retry_45m': 0.08,
    'whatsapp': 0.15,
    'payment_link': 0.12,
    'sms': 0.18,
    'email': 0.10,
    'human_escalation': 0.25,
    'stop': 0,
}

# ============================================================
# CONTROLLED PATTERNS (for ML to learn)
# ============================================================

def compute_recovery_probability(
    failure_reason: str,
    payment_method: str,
    action: str,
    customer_segment: str,
    amount: float,
    hour: int,
    customer_success_rate: float,
    retry_count: int,
    days_since_last_success: float,
) -> float:
    """Compute recovery probability with realistic controlled patterns.
    
    This function creates deterministic patterns that ML can learn:
    1. UPI bank timeouts recover better with delayed retries
    2. Expired cards respond to payment method update messages
    3. High-value returning customers justify escalation
    4. Low-value first-time customers have low recovery
    5. Repeated retries eventually reduce recovery probability
    6. Evening hours (7-10 PM) have specific patterns
    7. Customer history strongly predicts recovery
    """
    base = FAILURE_REASONS.get(failure_reason, {}).get('base_recovery', 0.3)
    
    # Pattern 1: UPI bank timeout — delayed retry is much better
    if failure_reason == 'bank_timeout' and payment_method == 'upi':
        if action == 'retry_now':
            base *= 0.55
        elif action == 'retry_15m':
            base *= 1.15
        elif action == 'retry_45m':
            base *= 1.35
        elif action == 'whatsapp':
            base *= 1.10
    
    # Pattern 2: Expired card — needs payment method update
    if failure_reason == 'expired_card':
        if action in ('retry_now', 'retry_15m', 'retry_45m'):
            base *= 0.15  # retrying won't help
        elif action in ('whatsapp', 'payment_link', 'email'):
            base *= 1.8  # notification to update card works
        elif action == 'human_escalation':
            base *= 2.0
    
    # Pattern 3: Network errors — immediate retry works well
    if failure_reason == 'network_error':
        if action == 'retry_now':
            base *= 1.5
        elif action == 'retry_15m':
            base *= 1.3
        elif action == 'retry_45m':
            base *= 1.1
    
    # Pattern 4: Customer segment effects
    segment_multiplier = {
        'new': 0.7,
        'returning': 1.1,
        'premium': 1.2,
        'high_value': 1.15,
    }
    base *= segment_multiplier.get(customer_segment, 1.0)
    
    # Pattern 5: Customer history — strong predictor
    if customer_success_rate > 0.9:
        base *= 1.25
    elif customer_success_rate > 0.7:
        base *= 1.1
    elif customer_success_rate < 0.3:
        base *= 0.6
    
    # Pattern 6: Amount effects
    if amount < 500:
        base *= 0.85  # low-value less worthwhile
    elif amount > 20000:
        base *= 1.05  # high-value slight boost (customer motivated)
    
    # Pattern 7: Retry fatigue
    if retry_count >= 3:
        base *= 0.4
    elif retry_count >= 2:
        base *= 0.65
    elif retry_count >= 1:
        base *= 0.85
    
    # Pattern 8: Time-of-day effects
    if 19 <= hour <= 22:  # peak hours
        if failure_reason == 'bank_timeout':
            base *= 0.9  # banks busier
        if action in ('retry_15m', 'retry_45m'):
            base *= 1.1  # delayed retry better during peak
    elif 0 <= hour <= 6:  # late night
        base *= 0.75
    
    # Pattern 9: Days since last success
    if days_since_last_success < 3:
        base *= 1.1
    elif days_since_last_success > 30:
        base *= 0.7
    
    # Pattern 10: Human escalation is effective but expensive
    if action == 'human_escalation':
        base = min(base * 1.4, 0.95)
    
    # Pattern 11: Stop action
    if action == 'stop':
        base = 0.0
    
    # Clamp and add small noise
    noise = random.gauss(0, 0.03)
    return max(0.01, min(0.98, base + noise))


# ============================================================
# DATA GENERATION
# ============================================================

class DataGenerator:
    def __init__(self, num_transactions: int = 10000):
        self.num_transactions = num_transactions
        self.merchant_id = "MERCH_DEMO0001"
        self.num_customers = max(500, num_transactions // 20)
        self.customers = []
        self.transactions = []
        self.start_date = datetime.utcnow() - timedelta(days=90)
        self.end_date = datetime.utcnow()
        
    def _random_date(self) -> datetime:
        delta = self.end_date - self.start_date
        random_seconds = random.randint(0, int(delta.total_seconds()))
        dt = self.start_date + timedelta(seconds=random_seconds)
        # Bias toward business hours
        hour = random.choices(
            range(24),
            weights=[1,1,1,1,1,1,2,3,5,7,8,8,7,6,5,5,6,7,8,9,8,6,3,2],
            k=1
        )[0]
        return dt.replace(hour=hour, minute=random.randint(0, 59), second=random.randint(0, 59))
    
    def generate_customers(self) -> list[dict]:
        """Generate customer profiles."""
        customers = []
        for i in range(self.num_customers):
            segment = random.choices(CUSTOMER_SEGMENTS, weights=SEGMENT_WEIGHTS, k=1)[0]
            
            # Segment-based profile generation
            if segment == 'new':
                total_txns = random.randint(1, 5)
                success_rate = random.uniform(0.5, 0.9)
                avg_amount = random.uniform(200, 3000)
                ltv = avg_amount * total_txns * success_rate
            elif segment == 'returning':
                total_txns = random.randint(10, 50)
                success_rate = random.uniform(0.75, 0.97)
                avg_amount = random.uniform(500, 10000)
                ltv = avg_amount * total_txns * success_rate
            elif segment == 'premium':
                total_txns = random.randint(20, 100)
                success_rate = random.uniform(0.85, 0.99)
                avg_amount = random.uniform(2000, 25000)
                ltv = avg_amount * total_txns * success_rate
            else:  # high_value
                total_txns = random.randint(5, 30)
                success_rate = random.uniform(0.80, 0.98)
                avg_amount = random.uniform(10000, 100000)
                ltv = avg_amount * total_txns * success_rate
            
            successful = int(total_txns * success_rate)
            failed = total_txns - successful
            
            customer = {
                'id': f'CUST_{i+1:04d}',
                'merchant_id': self.merchant_id,
                'email': f'customer{i+1}@example.com',
                'phone': f'+91{random.randint(7000000000, 9999999999)}',
                'name': f'Customer {i+1}',
                'segment': segment,
                'total_transactions': total_txns,
                'successful_transactions': successful,
                'failed_transactions': failed,
                'total_amount_paid': avg_amount * successful,
                'average_transaction_amount': avg_amount,
                'lifetime_value': ltv,
                'payment_success_rate': success_rate,
                'preferred_payment_method': random.choices(PAYMENT_METHODS, weights=PAYMENT_METHOD_WEIGHTS, k=1)[0],
                'preferred_payment_hour': random.choices(range(24), weights=[1,1,1,1,1,1,2,3,5,7,8,8,7,6,5,5,6,7,8,9,8,6,3,2], k=1)[0],
                'is_dnd': random.random() < 0.03,  # 3% DND
                'last_payment_at': self._random_date(),
                'created_at': self.start_date - timedelta(days=random.randint(0, 365)),
            }
            customers.append(customer)
        
        self.customers = customers
        return customers
    
    def generate_transactions(self) -> list[dict]:
        """Generate payment transactions with realistic patterns."""
        transactions = []
        
        # Overall success rate ~78%
        # Failed ~22%, of which some get recovered
        success_rate = 0.78
        recovery_rate_of_failed = 0.45  # 45% of failed get recovery attempted
        
        for i in range(self.num_transactions):
            customer = random.choice(self.customers)
            is_success = random.random() < success_rate
            
            payment_method = random.choices(PAYMENT_METHODS, weights=PAYMENT_METHOD_WEIGHTS, k=1)[0]
            txn_type = random.choices(TRANSACTION_TYPES, weights=TYPE_WEIGHTS, k=1)[0]
            created_at = self._random_date()
            
            # Amount based on customer segment and type
            base_amount = customer['average_transaction_amount']
            amount = max(50, base_amount * random.uniform(0.3, 2.5))
            amount = round(amount, 2)
            
            if is_success:
                status = 'success'
                failure_reason = None
                recovery_status = None
            else:
                # Choose failure reason with weighted distribution
                reasons = list(FAILURE_REASONS.keys())
                weights = [FAILURE_REASONS[r]['weight'] for r in reasons]
                failure_reason = random.choices(reasons, weights=weights, k=1)[0]
                
                # Adjust failure reason based on payment method
                if payment_method == 'card' and random.random() < 0.3:
                    failure_reason = random.choice(['expired_card', 'incorrect_details'])
                elif payment_method == 'upi' and random.random() < 0.35:
                    failure_reason = 'bank_timeout'
                
                # Determine if recovery was attempted and successful
                recovery_attempted = random.random() < recovery_rate_of_failed
                if recovery_attempted:
                    # Use our pattern-based recovery probability
                    best_action = random.choice(['retry_15m', 'retry_45m', 'whatsapp', 'payment_link'])
                    rec_prob = compute_recovery_probability(
                        failure_reason=failure_reason,
                        payment_method=payment_method,
                        action=best_action,
                        customer_segment=customer['segment'],
                        amount=amount,
                        hour=created_at.hour,
                        customer_success_rate=customer['payment_success_rate'],
                        retry_count=0,
                        days_since_last_success=random.uniform(0, 30),
                    )
                    recovered = random.random() < rec_prob
                    if recovered:
                        status = 'recovered'
                        recovery_status = 'recovered'
                    else:
                        status = 'failed'
                        recovery_status = 'failed'
                else:
                    status = 'failed'
                    recovery_status = 'detected'
            
            retry_count = 0
            if status == 'failed' and recovery_status in ('failed', 'recovered'):
                retry_count = random.randint(1, 3)
            
            txn = {
                'id': f'TXN_{i+1:06d}',
                'merchant_id': self.merchant_id,
                'customer_id': customer['id'],
                'amount': amount,
                'currency': 'INR',
                'payment_method': payment_method,
                'status': status,
                'failure_reason': failure_reason,
                'transaction_type': txn_type,
                'retry_count': retry_count,
                'is_recoverable': status != 'success',
                'recovery_status': recovery_status,
                'recovery_priority': round(random.uniform(0, 1), 3) if status != 'success' else 0,
                'created_at': created_at,
                'updated_at': created_at + timedelta(minutes=random.randint(0, 120)),
            }
            transactions.append(txn)
        
        self.transactions = transactions
        return transactions
    
    def generate_failure_events(self) -> list[dict]:
        """Generate failure events for failed transactions."""
        events = []
        for txn in self.transactions:
            if txn['failure_reason']:
                fr = txn['failure_reason']
                cat = FAILURE_REASONS.get(fr, {}).get('category', 'unknown')
                event = {
                    'transaction_id': txn['id'],
                    'failure_reason': fr,
                    'failure_category': cat,
                    'root_cause': f'Root cause analysis: {fr.replace("_", " ")}',
                    'confidence': round(random.uniform(0.7, 0.98), 3),
                    'supporting_signals': json.dumps({
                        'payment_method': txn['payment_method'],
                        'hour': txn['created_at'].hour,
                        'amount': txn['amount'],
                    }),
                    'detected_at': txn['created_at'],
                }
                events.append(event)
        return events
    
    def generate_recovery_twins(self) -> list[dict]:
        """Generate recovery twins for failed transactions."""
        twins = []
        for txn in self.transactions:
            if txn['status'] in ('failed', 'recovered') and txn['recovery_status'] in ('recovered', 'failed', 'detected'):
                customer = next((c for c in self.customers if c['id'] == txn['customer_id']), None)
                if not customer:
                    continue
                
                twin = {
                    'id': f'TWIN_{txn["id"][4:]}',
                    'transaction_id': txn['id'],
                    'customer_id': txn['customer_id'],
                    'amount': txn['amount'],
                    'payment_method': txn['payment_method'],
                    'failure_reason': txn['failure_reason'],
                    'customer_history': json.dumps({
                        'segment': customer['segment'],
                        'total_transactions': customer['total_transactions'],
                        'success_rate': customer['payment_success_rate'],
                        'lifetime_value': customer['lifetime_value'],
                    }),
                    'payment_history': json.dumps({
                        'successful': customer['successful_transactions'],
                        'failed': customer['failed_transactions'],
                        'avg_amount': customer['average_transaction_amount'],
                    }),
                    'time_features': json.dumps({
                        'hour': txn['created_at'].hour,
                        'day_of_week': txn['created_at'].weekday(),
                        'is_weekend': txn['created_at'].weekday() >= 5,
                    }),
                    'risk_features': json.dumps({
                        'amount_vs_avg': txn['amount'] / max(customer['average_transaction_amount'], 1),
                        'retry_count': txn['retry_count'],
                    }),
                    'recovery_features': json.dumps({
                        'failure_category': FAILURE_REASONS.get(txn['failure_reason'], {}).get('category', 'unknown'),
                        'base_recovery': FAILURE_REASONS.get(txn['failure_reason'], {}).get('base_recovery', 0.3),
                    }),
                    'recovery_probability': round(random.uniform(0.2, 0.9), 3),
                    'recommended_action': random.choice(['retry_15m', 'retry_45m', 'whatsapp', 'payment_link']),
                    'explanation': f'Recovery analysis for {txn["failure_reason"].replace("_", " ")} failure on {txn["payment_method"]} payment.',
                    'status': 'completed' if txn['recovery_status'] in ('recovered', 'failed') else 'created',
                    'created_at': txn['created_at'] + timedelta(seconds=random.randint(1, 60)),
                }
                twins.append(twin)
        return twins
    
    def generate_recovery_scenarios(self, twins: list[dict]) -> list[dict]:
        """Generate counterfactual scenarios for each recovery twin."""
        scenarios = []
        scenario_id = 1
        
        for twin in twins:
            txn = next((t for t in self.transactions if t['id'] == twin['transaction_id']), None)
            customer = next((c for c in self.customers if c['id'] == twin['customer_id']), None)
            if not txn or not customer:
                continue
            
            best_action = None
            best_net_recovery = -1
            
            for action in ACTION_TYPES:
                prob = compute_recovery_probability(
                    failure_reason=twin['failure_reason'],
                    payment_method=twin['payment_method'],
                    action=action,
                    customer_segment=customer['segment'],
                    amount=twin['amount'],
                    hour=txn['created_at'].hour,
                    customer_success_rate=customer['payment_success_rate'],
                    retry_count=txn['retry_count'],
                    days_since_last_success=random.uniform(0, 30),
                )
                
                expected_revenue = prob * twin['amount']
                cost = ACTION_COSTS[action]
                friction = ACTION_FRICTION[action]
                friction_cost = friction * twin['amount'] * 0.1
                net_recovery = expected_revenue - cost - friction_cost
                
                is_selected = False
                if net_recovery > best_net_recovery and action != 'stop':
                    best_net_recovery = net_recovery
                    best_action = action
                
                scenario = {
                    'id': scenario_id,
                    'twin_id': twin['id'],
                    'action': action,
                    'recovery_probability': round(prob, 4),
                    'expected_revenue': round(expected_revenue, 2),
                    'intervention_cost': cost,
                    'friction_score': round(friction, 3),
                    'expected_net_recovery': round(net_recovery, 2),
                    'confidence': round(random.uniform(0.7, 0.95), 3),
                    'explanation': self._generate_explanation(action, twin, prob),
                    'is_selected': False,
                    'is_policy_approved': True,
                    'policy_rejection_reason': None,
                    'created_at': twin['created_at'] + timedelta(seconds=random.randint(1, 30)),
                }
                scenarios.append(scenario)
                scenario_id += 1
            
            # Mark the best action as selected
            for s in scenarios:
                if s['twin_id'] == twin['id'] and s['action'] == best_action:
                    s['is_selected'] = True
                    twin['recommended_action'] = best_action
                    break
        
        return scenarios
    
    def _generate_explanation(self, action: str, twin: dict, prob: float) -> str:
        explanations = {
            'retry_now': f'Immediate retry has {prob*100:.0f}% success probability for {twin["failure_reason"].replace("_", " ")} failures.',
            'retry_15m': f'Delayed retry (15 min) allows transient {twin["failure_reason"].replace("_", " ")} issues to resolve. Expected {prob*100:.0f}% recovery.',
            'retry_45m': f'Extended delay (45 min) shows strongest recovery for {twin["payment_method"]} {twin["failure_reason"].replace("_", " ")} patterns. {prob*100:.0f}% predicted.',
            'whatsapp': f'WhatsApp notification enables customer-initiated recovery via payment link. {prob*100:.0f}% expected.',
            'payment_link': f'Fresh payment link allows customer to retry with updated details. {prob*100:.0f}% recovery predicted.',
            'sms': f'SMS reminder with payment link. {prob*100:.0f}% recovery probability.',
            'email': f'Email with payment details and recovery link. {prob*100:.0f}% predicted recovery.',
            'human_escalation': f'Human agent intervention for high-value recovery. {prob*100:.0f}% success but higher cost.',
            'stop': f'Stop recovery: cost/friction exceeds expected value. No further action recommended.',
        }
        return explanations.get(action, f'{action}: {prob*100:.0f}% recovery probability.')
    
    def generate_recovery_actions(self, twins: list[dict], scenarios: list[dict]) -> list[dict]:
        """Generate recovery actions for twins that had actions executed."""
        actions = []
        for twin in twins:
            txn = next((t for t in self.transactions if t['id'] == twin['transaction_id']), None)
            if not txn or txn['recovery_status'] not in ('recovered', 'failed'):
                continue
            
            selected_scenario = next(
                (s for s in scenarios if s['twin_id'] == twin['id'] and s['is_selected']),
                None
            )
            if not selected_scenario:
                continue
            
            action_time = twin['created_at'] + timedelta(minutes=random.randint(1, 60))
            
            action = {
                'id': f'ACT_{twin["id"][5:]}',
                'transaction_id': txn['id'],
                'action_type': selected_scenario['action'],
                'status': 'completed',
                'scheduled_at': action_time - timedelta(minutes=random.randint(0, 15)),
                'executed_at': action_time,
                'result': 'success' if txn['status'] == 'recovered' else 'failure',
                'result_details': json.dumps({'scenario_id': selected_scenario['id']}),
                'cost': selected_scenario['intervention_cost'],
                'model_version': 'v1.0.0',
                'idempotency_key': f'idem_{txn["id"]}_{selected_scenario["action"]}',
                'created_at': action_time,
            }
            actions.append(action)
        return actions
    
    def generate_recovery_outcomes(self, actions_list: list[dict]) -> list[dict]:
        """Generate recovery outcomes."""
        outcomes = []
        for action in actions_list:
            txn = next((t for t in self.transactions if t['id'] == action['transaction_id']), None)
            if not txn:
                continue
            
            recovered = action['result'] == 'success'
            outcome = {
                'action_id': action['id'],
                'recovered': recovered,
                'recovered_amount': txn['amount'] if recovered else 0,
                'recovery_time_minutes': random.uniform(1, 120) if recovered else None,
                'intervention_cost': action['cost'],
                'net_recovered': (txn['amount'] - action['cost']) if recovered else -action['cost'],
                'customer_feedback': random.choice([None, 'positive', 'neutral']) if recovered else random.choice([None, 'negative', 'neutral']),
                'created_at': action['executed_at'] + timedelta(minutes=random.randint(1, 30)),
            }
            outcomes.append(outcome)
        return outcomes
    
    def generate_audit_logs(self, twins: list[dict], actions_list: list[dict]) -> list[dict]:
        """Generate audit trail entries."""
        logs = []
        
        for twin in twins:
            txn = next((t for t in self.transactions if t['id'] == twin['transaction_id']), None)
            if not txn:
                continue
            
            base_time = twin['created_at']
            
            # Detection log
            logs.append({
                'transaction_id': txn['id'],
                'agent': 'revenue_risk',
                'decision_type': 'detection',
                'action': 'revenue_at_risk_detected',
                'reasoning': f'Payment of INR {txn["amount"]:.2f} failed due to {txn["failure_reason"]}',
                'model_version': 'v1.0.0',
                'confidence': round(random.uniform(0.85, 0.99), 3),
                'policy_result': None,
                'previous_state': None,
                'new_state': 'detected',
                'execution_result': None,
                'created_at': base_time,
            })
            
            # Diagnosis log
            logs.append({
                'transaction_id': txn['id'],
                'agent': 'root_cause',
                'decision_type': 'diagnosis',
                'action': f'root_cause_{txn["failure_reason"]}',
                'reasoning': f'Root cause identified as {txn["failure_reason"].replace("_", " ")}',
                'model_version': 'v1.0.0',
                'confidence': round(random.uniform(0.8, 0.97), 3),
                'policy_result': None,
                'previous_state': 'detected',
                'new_state': 'diagnosed',
                'execution_result': None,
                'created_at': base_time + timedelta(seconds=1),
            })
            
            # Twin creation log
            logs.append({
                'transaction_id': txn['id'],
                'agent': 'recovery_twin',
                'decision_type': 'simulation',
                'action': 'recovery_twin_created',
                'reasoning': f'Recovery Twin created. Simulating {len(ACTION_TYPES)} recovery scenarios.',
                'model_version': 'v1.0.0',
                'confidence': None,
                'policy_result': None,
                'previous_state': 'diagnosed',
                'new_state': 'simulating',
                'execution_result': None,
                'created_at': base_time + timedelta(seconds=2),
            })
            
            # Check if action was executed
            action = next((a for a in actions_list if a['transaction_id'] == txn['id']), None)
            if action:
                # Policy check log
                logs.append({
                    'transaction_id': txn['id'],
                    'agent': 'policy_engine',
                    'decision_type': 'policy_check',
                    'action': f'approved_{action["action_type"]}',
                    'reasoning': f'Action {action["action_type"]} approved by policy engine.',
                    'model_version': None,
                    'confidence': None,
                    'policy_result': json.dumps({'approved': True, 'action': action['action_type']}),
                    'previous_state': 'simulating',
                    'new_state': 'policy_check',
                    'execution_result': None,
                    'created_at': base_time + timedelta(seconds=30),
                })
                
                # Action selection log
                logs.append({
                    'transaction_id': txn['id'],
                    'agent': 'recovery_policy',
                    'decision_type': 'action_selection',
                    'action': action['action_type'],
                    'reasoning': f'Selected {action["action_type"]} as optimal recovery action.',
                    'model_version': 'v1.0.0',
                    'confidence': round(random.uniform(0.75, 0.95), 3),
                    'policy_result': None,
                    'previous_state': 'policy_check',
                    'new_state': 'action_selected',
                    'execution_result': None,
                    'created_at': base_time + timedelta(seconds=31),
                })
                
                # Execution log
                logs.append({
                    'transaction_id': txn['id'],
                    'agent': 'action_executor',
                    'decision_type': 'execution',
                    'action': action['action_type'],
                    'reasoning': f'Executing {action["action_type"]}',
                    'model_version': None,
                    'confidence': None,
                    'policy_result': None,
                    'previous_state': 'action_selected',
                    'new_state': 'executing',
                    'execution_result': json.dumps({'result': action['result']}),
                    'created_at': action['executed_at'],
                })
                
                # Outcome log
                final_state = 'recovered' if action['result'] == 'success' else 'failed'
                logs.append({
                    'transaction_id': txn['id'],
                    'agent': 'evaluation',
                    'decision_type': 'observation',
                    'action': f'outcome_{final_state}',
                    'reasoning': f'Recovery {"successful" if final_state == "recovered" else "unsuccessful"}. Amount: INR {txn["amount"]:.2f}',
                    'model_version': 'v1.0.0',
                    'confidence': None,
                    'policy_result': None,
                    'previous_state': 'executing',
                    'new_state': final_state,
                    'execution_result': json.dumps({'recovered': final_state == 'recovered', 'amount': txn['amount']}),
                    'created_at': action['executed_at'] + timedelta(minutes=random.randint(1, 30)),
                })
        
        return logs
    
    def generate_experiments(self) -> tuple[list[dict], list[dict]]:
        """Generate pre-run experiments."""
        experiments = []
        results = []
        
        # Experiment 1: UPI bank timeout - control vs AI
        exp1_id = 'EXP_00000001'
        experiments.append({
            'id': exp1_id,
            'name': 'UPI Bank Timeout Recovery: Immediate vs Delayed Retry',
            'description': 'Compare immediate retry (control) vs AI-optimized delayed retry for UPI bank timeout failures.',
            'segment': None,
            'payment_method': 'upi',
            'failure_reason': 'bank_timeout',
            'amount_min': None,
            'amount_max': None,
            'control_strategy': 'retry_now',
            'ai_strategy': 'ai_optimal',
            'status': 'completed',
            'created_at': datetime.utcnow() - timedelta(days=7),
            'completed_at': datetime.utcnow() - timedelta(days=1),
        })
        
        # Control result
        upi_timeout_failed = [t for t in self.transactions if t['failure_reason'] == 'bank_timeout' and t['payment_method'] == 'upi']
        control_count = len(upi_timeout_failed) // 2
        control_recovered = int(control_count * 0.421)  # 42.1% control recovery
        control_revenue = sum(t['amount'] for t in upi_timeout_failed[:control_count])
        control_recovered_rev = control_revenue * 0.421
        
        results.append({
            'experiment_id': exp1_id,
            'group_name': 'control',
            'strategy': 'retry_now',
            'total_transactions': control_count,
            'recovered_count': control_recovered,
            'recovery_rate': 0.421,
            'total_revenue_at_risk': round(control_revenue, 2),
            'recovered_revenue': round(control_recovered_rev, 2),
            'intervention_cost': 0,
            'net_recovered': round(control_recovered_rev, 2),
            'avg_recovery_time': 2.3,
        })
        
        # AI result
        ai_count = len(upi_timeout_failed) - control_count
        ai_recovered = int(ai_count * 0.786)  # 78.6% AI recovery
        ai_revenue = sum(t['amount'] for t in upi_timeout_failed[control_count:])
        ai_recovered_rev = ai_revenue * 0.786
        ai_cost = ai_count * 0.5  # small cost from SMS/WhatsApp
        
        results.append({
            'experiment_id': exp1_id,
            'group_name': 'treatment',
            'strategy': 'ai_optimal',
            'total_transactions': ai_count,
            'recovered_count': ai_recovered,
            'recovery_rate': 0.786,
            'total_revenue_at_risk': round(ai_revenue, 2),
            'recovered_revenue': round(ai_recovered_rev, 2),
            'intervention_cost': round(ai_cost, 2),
            'net_recovered': round(ai_recovered_rev - ai_cost, 2),
            'avg_recovery_time': 48.5,
        })
        
        # Experiment 2: Expired card recovery
        exp2_id = 'EXP_00000002'
        experiments.append({
            'id': exp2_id,
            'name': 'Expired Card Recovery: Retry vs Payment Update Notification',
            'description': 'Compare retry (control) vs WhatsApp payment update request for expired card failures.',
            'segment': None,
            'payment_method': 'card',
            'failure_reason': 'expired_card',
            'amount_min': None,
            'amount_max': None,
            'control_strategy': 'retry_now',
            'ai_strategy': 'ai_optimal',
            'status': 'completed',
            'created_at': datetime.utcnow() - timedelta(days=14),
            'completed_at': datetime.utcnow() - timedelta(days=3),
        })
        
        expired_card_failed = [t for t in self.transactions if t['failure_reason'] == 'expired_card']
        ec_control = len(expired_card_failed) // 2
        ec_ai = len(expired_card_failed) - ec_control
        ec_control_rev = sum(t['amount'] for t in expired_card_failed[:ec_control])
        ec_ai_rev = sum(t['amount'] for t in expired_card_failed[ec_control:])
        
        results.append({
            'experiment_id': exp2_id,
            'group_name': 'control',
            'strategy': 'retry_now',
            'total_transactions': ec_control,
            'recovered_count': int(ec_control * 0.08),
            'recovery_rate': 0.08,
            'total_revenue_at_risk': round(ec_control_rev, 2),
            'recovered_revenue': round(ec_control_rev * 0.08, 2),
            'intervention_cost': 0,
            'net_recovered': round(ec_control_rev * 0.08, 2),
            'avg_recovery_time': 1.2,
        })
        
        results.append({
            'experiment_id': exp2_id,
            'group_name': 'treatment',
            'strategy': 'ai_optimal',
            'total_transactions': ec_ai,
            'recovered_count': int(ec_ai * 0.52),
            'recovery_rate': 0.52,
            'total_revenue_at_risk': round(ec_ai_rev, 2),
            'recovered_revenue': round(ec_ai_rev * 0.52, 2),
            'intervention_cost': round(ec_ai * 2.5, 2),
            'net_recovered': round(ec_ai_rev * 0.52 - ec_ai * 2.5, 2),
            'avg_recovery_time': 180.0,
        })
        
        # Experiment 3: High-value customer escalation
        exp3_id = 'EXP_00000003'
        experiments.append({
            'id': exp3_id,
            'name': 'High-Value Customer: AI Multi-Action vs Simple Retry',
            'description': 'Compare simple retry vs AI multi-step recovery for high-value customer segment.',
            'segment': 'high_value',
            'payment_method': None,
            'failure_reason': None,
            'amount_min': 10000,
            'amount_max': None,
            'control_strategy': 'retry_now',
            'ai_strategy': 'ai_optimal',
            'status': 'completed',
            'created_at': datetime.utcnow() - timedelta(days=10),
            'completed_at': datetime.utcnow() - timedelta(days=2),
        })
        
        hv_failed = [t for t in self.transactions if t['status'] in ('failed', 'recovered') and t['amount'] >= 10000]
        hv_control = len(hv_failed) // 2 or 50
        hv_ai = len(hv_failed) - hv_control or 50
        hv_control_rev = sum(t['amount'] for t in hv_failed[:hv_control]) or 500000
        hv_ai_rev = sum(t['amount'] for t in hv_failed[hv_control:]) or 500000
        
        results.append({
            'experiment_id': exp3_id,
            'group_name': 'control',
            'strategy': 'retry_now',
            'total_transactions': hv_control,
            'recovered_count': int(hv_control * 0.35),
            'recovery_rate': 0.35,
            'total_revenue_at_risk': round(hv_control_rev, 2),
            'recovered_revenue': round(hv_control_rev * 0.35, 2),
            'intervention_cost': 0,
            'net_recovered': round(hv_control_rev * 0.35, 2),
            'avg_recovery_time': 3.0,
        })
        
        results.append({
            'experiment_id': exp3_id,
            'group_name': 'treatment',
            'strategy': 'ai_optimal',
            'total_transactions': hv_ai,
            'recovered_count': int(hv_ai * 0.71),
            'recovery_rate': 0.71,
            'total_revenue_at_risk': round(hv_ai_rev, 2),
            'recovered_revenue': round(hv_ai_rev * 0.71, 2),
            'intervention_cost': round(hv_ai * 15, 2),
            'net_recovered': round(hv_ai_rev * 0.71 - hv_ai * 15, 2),
            'avg_recovery_time': 65.0,
        })
        
        return experiments, results
    
    def generate_policy_decisions(self, actions_list: list[dict]) -> list[dict]:
        """Generate policy decisions."""
        decisions = []
        for action in actions_list:
            decisions.append({
                'transaction_id': action['transaction_id'],
                'action_type': action['action_type'],
                'approved': True,
                'reason': f'Action {action["action_type"]} approved: within policy limits.',
                'policies_evaluated': json.dumps(['max_retry', 'cooldown', 'budget', 'amount_limit', 'dnd']),
                'decided_at': action['scheduled_at'],
            })
        return decisions


async def seed_database(num_transactions: int = 10000):
    """Seed the database with synthetic data."""
    from app.core.database import engine, Base, AsyncSessionLocal
    from app.models import (
        Merchant, MerchantSettings, Customer, PaymentTransaction,
        PaymentAttempt, FailureEvent, RecoveryTwin, RecoveryScenario,
        RecoveryAction, RecoveryOutcome, Policy, PolicyDecision,
        Experiment, ExperimentResult, AuditLog, ModelVersion, Notification
    )
    
    logger.info(f"Generating {num_transactions} synthetic transactions...")
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")
    
    # Generate data
    gen = DataGenerator(num_transactions=num_transactions)
    customers = gen.generate_customers()
    logger.info(f"Generated {len(customers)} customers")
    
    transactions = gen.generate_transactions()
    logger.info(f"Generated {len(transactions)} transactions")
    
    failure_events = gen.generate_failure_events()
    logger.info(f"Generated {len(failure_events)} failure events")
    
    twins = gen.generate_recovery_twins()
    logger.info(f"Generated {len(twins)} recovery twins")
    
    scenarios = gen.generate_recovery_scenarios(twins)
    logger.info(f"Generated {len(scenarios)} recovery scenarios")
    
    actions_list = gen.generate_recovery_actions(twins, scenarios)
    logger.info(f"Generated {len(actions_list)} recovery actions")
    
    outcomes = gen.generate_recovery_outcomes(actions_list)
    logger.info(f"Generated {len(outcomes)} recovery outcomes")
    
    audit_logs = gen.generate_audit_logs(twins, actions_list)
    logger.info(f"Generated {len(audit_logs)} audit logs")
    
    experiments, exp_results = gen.generate_experiments()
    logger.info(f"Generated {len(experiments)} experiments")
    
    policy_decisions = gen.generate_policy_decisions(actions_list)
    logger.info(f"Generated {len(policy_decisions)} policy decisions")
    
    # Insert into database
    async with AsyncSessionLocal() as session:
        try:
            # Merchant
            merchant = Merchant(
                id=gen.merchant_id,
                name='Demo Merchant',
                email='demo@recoverx.com',
                business_type='ecommerce',
            )
            session.add(merchant)
            await session.flush()
            
            # Merchant Settings
            ms = MerchantSettings(
                merchant_id=gen.merchant_id,
                daily_recovery_budget=5000.0,
            )
            session.add(ms)
            await session.flush()
            
            # Customers - batch insert
            logger.info("Inserting customers...")
            for c in customers:
                obj = Customer(**c)
                session.add(obj)
            await session.flush()
            logger.info("Customers inserted")
            
            # Transactions - batch insert
            logger.info("Inserting transactions...")
            batch_size = 1000
            for i in range(0, len(transactions), batch_size):
                batch = transactions[i:i+batch_size]
                for t in batch:
                    obj = PaymentTransaction(**t)
                    session.add(obj)
                await session.flush()
                logger.info(f"  Inserted {min(i+batch_size, len(transactions))}/{len(transactions)} transactions")
            
            # Failure Events
            logger.info("Inserting failure events...")
            for fe in failure_events:
                obj = FailureEvent(**fe)
                session.add(obj)
            await session.flush()
            
            # Recovery Twins
            logger.info("Inserting recovery twins...")
            for tw in twins:
                obj = RecoveryTwin(**tw)
                session.add(obj)
            await session.flush()
            
            # Recovery Scenarios
            logger.info("Inserting recovery scenarios...")
            for i in range(0, len(scenarios), batch_size):
                batch = scenarios[i:i+batch_size]
                for s in batch:
                    # Remove 'id' since it's autoincrement
                    s_copy = {k: v for k, v in s.items() if k != 'id'}
                    obj = RecoveryScenario(**s_copy)
                    session.add(obj)
                await session.flush()
                logger.info(f"  Inserted {min(i+batch_size, len(scenarios))}/{len(scenarios)} scenarios")
            
            # Recovery Actions
            logger.info("Inserting recovery actions...")
            for a in actions_list:
                obj = RecoveryAction(**a)
                session.add(obj)
            await session.flush()
            
            # Recovery Outcomes
            logger.info("Inserting recovery outcomes...")
            for o in outcomes:
                obj = RecoveryOutcome(**o)
                session.add(obj)
            await session.flush()
            
            # Policy Decisions
            logger.info("Inserting policy decisions...")
            for pd_item in policy_decisions:
                obj = PolicyDecision(**pd_item)
                session.add(obj)
            await session.flush()
            
            # Experiments
            logger.info("Inserting experiments...")
            for exp in experiments:
                obj = Experiment(**exp)
                session.add(obj)
            await session.flush()
            
            for er in exp_results:
                obj = ExperimentResult(**er)
                session.add(obj)
            await session.flush()
            
            # Audit Logs
            logger.info("Inserting audit logs...")
            for i in range(0, len(audit_logs), batch_size):
                batch = audit_logs[i:i+batch_size]
                for al in batch:
                    obj = AuditLog(**al)
                    session.add(obj)
                await session.flush()
                logger.info(f"  Inserted {min(i+batch_size, len(audit_logs))}/{len(audit_logs)} audit logs")
            
            # Model Version
            mv = ModelVersion(
                model_name='recovery_probability',
                version='v1.0.0',
                dataset_version='demo_v1',
                metrics=json.dumps({'accuracy': 0.82, 'auc_roc': 0.88, 'precision': 0.79, 'recall': 0.84}),
                features=json.dumps(['amount', 'payment_method', 'failure_reason', 'customer_success_rate', 'retry_count', 'hour', 'customer_segment']),
                artifact_path='ml/models/recovery_model_v1.joblib',
                is_active=True,
            )
            session.add(mv)
            
            await session.commit()
            logger.info("All data committed successfully!")
            
            # Print summary
            success_count = sum(1 for t in transactions if t['status'] == 'success')
            failed_count = sum(1 for t in transactions if t['status'] == 'failed')
            recovered_count = sum(1 for t in transactions if t['status'] == 'recovered')
            total_revenue = sum(t['amount'] for t in transactions)
            at_risk = sum(t['amount'] for t in transactions if t['status'] in ('failed', 'recovered'))
            recovered_rev = sum(t['amount'] for t in transactions if t['status'] == 'recovered')
            
            logger.info("\n" + "=" * 60)
            logger.info("SEED DATA SUMMARY")
            logger.info("=" * 60)
            logger.info(f"Customers:              {len(customers)}")
            logger.info(f"Total Transactions:     {len(transactions)}")
            logger.info(f"  Successful:           {success_count}")
            logger.info(f"  Failed:               {failed_count}")
            logger.info(f"  Recovered:            {recovered_count}")
            logger.info(f"Total Revenue:          INR {total_revenue:,.2f}")
            logger.info(f"Revenue at Risk:        INR {at_risk:,.2f}")
            logger.info(f"Revenue Recovered:      INR {recovered_rev:,.2f}")
            logger.info(f"Recovery Rate:          {recovered_count/(failed_count+recovered_count)*100:.1f}%" if (failed_count+recovered_count) > 0 else "N/A")
            logger.info(f"Recovery Twins:         {len(twins)}")
            logger.info(f"Recovery Scenarios:     {len(scenarios)}")
            logger.info(f"Recovery Actions:       {len(actions_list)}")
            logger.info(f"Audit Logs:             {len(audit_logs)}")
            logger.info(f"Experiments:            {len(experiments)}")
            logger.info("=" * 60)
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to seed database: {e}")
            raise


def main():
    parser = argparse.ArgumentParser(description='Seed RecoverX demo data')
    parser.add_argument('--large', action='store_true', help='Generate 100K transactions')
    parser.add_argument('--count', type=int, default=None, help='Custom transaction count')
    args = parser.parse_args()
    
    if args.count:
        num = args.count
    elif args.large:
        num = 100000
    else:
        num = 10000
    
    asyncio.run(seed_database(num))


if __name__ == '__main__':
    main()
