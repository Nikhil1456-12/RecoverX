"""Transaction API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_
from sqlalchemy.orm import selectinload
from typing import Optional
from datetime import datetime
import json

from app.core.database import get_db
from app.models.transaction import PaymentTransaction
from app.models.customer import Customer
from app.models.recovery import RecoveryTwin, RecoveryScenario, RecoveryAction, RecoveryOutcome
from app.models.audit import AuditLog
from app.services.counterfactual_engine import CounterfactualEngine, TransactionContext
from app.services.policy_engine import PolicyEngine, PolicyContext
from app.services.recovery_twin import RecoveryTwinService
from app.services.action_executor import ActionExecutor
from app.core.config import settings

router = APIRouter()


@router.get("")
async def list_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    payment_method: Optional[str] = None,
    failure_reason: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    db: AsyncSession = Depends(get_db),
):
    """List transactions with pagination and filters."""
    query = select(PaymentTransaction).order_by(desc(PaymentTransaction.created_at))
    count_query = select(func.count(PaymentTransaction.id))
    
    # Apply filters
    conditions = []
    if status:
        conditions.append(PaymentTransaction.status == status)
    if payment_method:
        conditions.append(PaymentTransaction.payment_method == payment_method)
    if failure_reason:
        conditions.append(PaymentTransaction.failure_reason == failure_reason)
    if min_amount is not None:
        conditions.append(PaymentTransaction.amount >= min_amount)
    if max_amount is not None:
        conditions.append(PaymentTransaction.amount <= max_amount)
    
    if conditions:
        query = query.where(and_(*conditions))
        count_query = count_query.where(and_(*conditions))
    
    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Paginate
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    result = await db.execute(query)
    transactions = result.scalars().all()
    
    # Enrich with customer data
    txn_list = []
    for txn in transactions:
        cust_q = await db.execute(select(Customer).where(Customer.id == txn.customer_id))
        customer = cust_q.scalar_one_or_none()
        
        txn_dict = {
            "id": txn.id,
            "merchant_id": txn.merchant_id,
            "customer_id": txn.customer_id,
            "amount": txn.amount,
            "currency": txn.currency,
            "payment_method": txn.payment_method,
            "status": txn.status,
            "failure_reason": txn.failure_reason,
            "transaction_type": txn.transaction_type,
            "retry_count": txn.retry_count,
            "is_recoverable": txn.is_recoverable,
            "recovery_status": txn.recovery_status,
            "recovery_priority": txn.recovery_priority,
            "created_at": txn.created_at.isoformat(),
            "updated_at": txn.updated_at.isoformat() if txn.updated_at else None,
            "customer_name": customer.name if customer else None,
            "customer_segment": customer.segment if customer else None,
            "customer_success_rate": customer.payment_success_rate if customer else None,
        }
        txn_list.append(txn_dict)
    
    return {
        "transactions": txn_list,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{transaction_id}")
async def get_transaction(transaction_id: str, db: AsyncSession = Depends(get_db)):
    """Get transaction detail with customer info."""
    result = await db.execute(
        select(PaymentTransaction).where(PaymentTransaction.id == transaction_id)
    )
    txn = result.scalar_one_or_none()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Get customer
    cust_q = await db.execute(select(Customer).where(Customer.id == txn.customer_id))
    customer = cust_q.scalar_one_or_none()
    
    # Get recovery twin
    twin_q = await db.execute(
        select(RecoveryTwin).where(RecoveryTwin.transaction_id == transaction_id)
    )
    twin = twin_q.scalar_one_or_none()
    
    # Get recovery actions
    actions_q = await db.execute(
        select(RecoveryAction).where(RecoveryAction.transaction_id == transaction_id)
        .order_by(RecoveryAction.created_at)
    )
    actions = actions_q.scalars().all()
    
    # Build response
    response = {
        "id": txn.id,
        "merchant_id": txn.merchant_id,
        "customer_id": txn.customer_id,
        "amount": txn.amount,
        "currency": txn.currency,
        "payment_method": txn.payment_method,
        "status": txn.status,
        "failure_reason": txn.failure_reason,
        "transaction_type": txn.transaction_type,
        "retry_count": txn.retry_count,
        "is_recoverable": txn.is_recoverable,
        "recovery_status": txn.recovery_status,
        "recovery_priority": txn.recovery_priority,
        "created_at": txn.created_at.isoformat(),
        "updated_at": txn.updated_at.isoformat() if txn.updated_at else None,
    }
    
    if customer:
        response["customer"] = {
            "id": customer.id,
            "name": customer.name,
            "email": customer.email,
            "segment": customer.segment,
            "payment_success_rate": customer.payment_success_rate,
            "total_transactions": customer.total_transactions,
            "lifetime_value": customer.lifetime_value,
            "preferred_payment_method": customer.preferred_payment_method,
            "is_dnd": customer.is_dnd,
            "last_payment_at": customer.last_payment_at.isoformat() if customer.last_payment_at else None,
        }
    
    if twin:
        # Get scenarios
        scenarios_q = await db.execute(
            select(RecoveryScenario).where(RecoveryScenario.twin_id == twin.id)
            .order_by(desc(RecoveryScenario.expected_net_recovery))
        )
        scenarios = scenarios_q.scalars().all()
        
        response["recovery_twin"] = {
            "id": twin.id,
            "recovery_probability": twin.recovery_probability,
            "recommended_action": twin.recommended_action,
            "explanation": twin.explanation,
            "status": twin.status,
            "customer_history": json.loads(twin.customer_history) if twin.customer_history else None,
            "payment_history": json.loads(twin.payment_history) if twin.payment_history else None,
            "time_features": json.loads(twin.time_features) if twin.time_features else None,
            "risk_features": json.loads(twin.risk_features) if twin.risk_features else None,
            "scenarios": [
                {
                    "id": s.id,
                    "action": s.action,
                    "recovery_probability": s.recovery_probability,
                    "expected_revenue": s.expected_revenue,
                    "intervention_cost": s.intervention_cost,
                    "friction_score": s.friction_score,
                    "expected_net_recovery": s.expected_net_recovery,
                    "confidence": s.confidence,
                    "explanation": s.explanation,
                    "is_selected": s.is_selected,
                    "is_policy_approved": s.is_policy_approved,
                    "policy_rejection_reason": s.policy_rejection_reason,
                }
                for s in scenarios
            ]
        }
    
    if actions:
        response["recovery_actions"] = [
            {
                "id": a.id,
                "action_type": a.action_type,
                "status": a.status,
                "executed_at": a.executed_at.isoformat() if a.executed_at else None,
                "result": a.result,
                "cost": a.cost,
            }
            for a in actions
        ]
    
    return response


@router.get("/{transaction_id}/recovery-twin")
async def get_recovery_twin(transaction_id: str, db: AsyncSession = Depends(get_db)):
    """Get or create recovery twin for a transaction."""
    # Check for existing twin with scenarios
    twin_q = await db.execute(
        select(RecoveryTwin).where(RecoveryTwin.transaction_id == transaction_id)
    )
    twin = twin_q.scalar_one_or_none()
    
    if twin:
        scenarios_q = await db.execute(
            select(RecoveryScenario).where(RecoveryScenario.twin_id == twin.id)
            .order_by(desc(RecoveryScenario.expected_net_recovery))
        )
        scenarios = scenarios_q.scalars().all()
        
        return {
            "id": twin.id,
            "transaction_id": twin.transaction_id,
            "customer_id": twin.customer_id,
            "amount": twin.amount,
            "payment_method": twin.payment_method,
            "failure_reason": twin.failure_reason,
            "customer_history": json.loads(twin.customer_history) if twin.customer_history else None,
            "payment_history": json.loads(twin.payment_history) if twin.payment_history else None,
            "time_features": json.loads(twin.time_features) if twin.time_features else None,
            "risk_features": json.loads(twin.risk_features) if twin.risk_features else None,
            "recovery_probability": twin.recovery_probability,
            "recommended_action": twin.recommended_action,
            "explanation": twin.explanation,
            "scenarios": [
                {
                    "id": s.id,
                    "action": s.action,
                    "recovery_probability": s.recovery_probability,
                    "expected_revenue": s.expected_revenue,
                    "intervention_cost": s.intervention_cost,
                    "friction_score": s.friction_score,
                    "expected_net_recovery": s.expected_net_recovery,
                    "confidence": s.confidence,
                    "explanation": s.explanation,
                    "is_selected": s.is_selected,
                    "is_policy_approved": s.is_policy_approved,
                }
                for s in scenarios
            ],
            "status": twin.status,
        }
    
    raise HTTPException(status_code=404, detail="Recovery twin not found")


@router.post("/{transaction_id}/simulate")
async def simulate_recovery(transaction_id: str, db: AsyncSession = Depends(get_db)):
    """Run counterfactual simulation for a transaction."""
    # Get transaction
    txn_q = await db.execute(
        select(PaymentTransaction).where(PaymentTransaction.id == transaction_id)
    )
    txn = txn_q.scalar_one_or_none()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Get customer
    cust_q = await db.execute(select(Customer).where(Customer.id == txn.customer_id))
    customer = cust_q.scalar_one_or_none()
    
    # Build twin using the service
    twin_service = RecoveryTwinService()
    result = twin_service.build_twin(
        transaction_id=txn.id,
        customer_id=txn.customer_id,
        amount=txn.amount,
        payment_method=txn.payment_method,
        failure_reason=txn.failure_reason or 'unknown',
        retry_count=txn.retry_count,
        hour_of_day=txn.created_at.hour,
        day_of_week=txn.created_at.weekday(),
        customer_segment=customer.segment if customer else 'returning',
        customer_success_rate=customer.payment_success_rate if customer else 0.8,
        customer_lifetime_value=customer.lifetime_value if customer else 0,
        customer_is_dnd=customer.is_dnd if customer else False,
    )
    
    return {
        "transaction_id": transaction_id,
        "scenarios": [
            {
                "action": s.action,
                "action_label": s.action_label,
                "recovery_probability": s.recovery_probability,
                "expected_revenue": s.expected_revenue,
                "intervention_cost": s.intervention_cost,
                "friction_score": s.friction_score,
                "expected_net_recovery": s.expected_net_recovery,
                "confidence": s.confidence,
                "explanation": s.explanation,
                "is_recommended": s.is_recommended,
            }
            for s in result.scenarios
        ],
        "recommended_action": result.recommended_action,
        "recommended_action_label": result.recommended_action_label,
        "explanation": result.explanation,
        "policy_decisions": result.policy_decisions,
    }


@router.post("/{transaction_id}/recover")
async def execute_recovery(transaction_id: str, db: AsyncSession = Depends(get_db)):
    """Execute recovery action for a transaction."""
    # Get transaction
    txn_q = await db.execute(
        select(PaymentTransaction).where(PaymentTransaction.id == transaction_id)
    )
    txn = txn_q.scalar_one_or_none()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Get customer
    cust_q = await db.execute(select(Customer).where(Customer.id == txn.customer_id))
    customer = cust_q.scalar_one_or_none()
    
    # Build twin and simulate
    twin_service = RecoveryTwinService()
    result = twin_service.build_twin(
        transaction_id=txn.id,
        customer_id=txn.customer_id,
        amount=txn.amount,
        payment_method=txn.payment_method,
        failure_reason=txn.failure_reason or 'unknown',
        retry_count=txn.retry_count,
        hour_of_day=txn.created_at.hour,
        day_of_week=txn.created_at.weekday(),
        customer_segment=customer.segment if customer else 'returning',
        customer_success_rate=customer.payment_success_rate if customer else 0.8,
        customer_lifetime_value=customer.lifetime_value if customer else 0,
        customer_is_dnd=customer.is_dnd if customer else False,
    )
    
    # Check policy
    policy_decision = result.policy_decisions.get(result.recommended_action, {})
    if not policy_decision.get('approved', False):
        return {
            "transaction_id": transaction_id,
            "action": result.recommended_action,
            "status": "rejected",
            "policy_approved": False,
            "policy_reason": policy_decision.get('reason', 'Policy rejected'),
            "message": f"Action {result.recommended_action} rejected by policy engine",
        }
    
    # Execute action
    executor = ActionExecutor(demo_mode=settings.is_demo_mode)
    rec_scenario = next((s for s in result.scenarios if s.action == result.recommended_action), None)
    action_result = await executor.execute(
        result.recommended_action,
        txn.id,
        txn.amount,
        recovery_probability=rec_scenario.recovery_probability if rec_scenario else 0.5,
    )
    
    # Update transaction status
    if action_result.success:
        txn.status = 'recovered'
        txn.recovery_status = 'recovered'
    else:
        txn.recovery_status = 'failed'
    txn.retry_count += 1
    
    # Create audit log
    from app.models.audit import AuditLog as AuditLogModel
    audit = AuditLogModel(
        transaction_id=txn.id,
        agent='action_executor',
        decision_type='execution',
        action=result.recommended_action,
        reasoning=result.explanation,
        model_version='v1.0.0',
        confidence=rec_scenario.confidence if rec_scenario else None,
        policy_result=json.dumps(policy_decision),
        previous_state=txn.recovery_status,
        new_state='recovered' if action_result.success else 'failed',
        execution_result=json.dumps({'success': action_result.success, 'message': action_result.message}),
    )
    db.add(audit)
    
    return {
        "transaction_id": transaction_id,
        "action": result.recommended_action,
        "status": "recovered" if action_result.success else "failed",
        "policy_approved": True,
        "execution_result": action_result.message,
        "message": f"Recovery {'successful' if action_result.success else 'attempted but failed'} (DEMO MODE)",
        "recovered_amount": txn.amount if action_result.success else 0,
        "cost": action_result.cost,
    }


@router.get("/{transaction_id}/timeline")
async def get_timeline(transaction_id: str, db: AsyncSession = Depends(get_db)):
    """Get audit timeline for a transaction."""
    result = await db.execute(
        select(AuditLog).where(AuditLog.transaction_id == transaction_id)
        .order_by(AuditLog.created_at)
    )
    logs = result.scalars().all()
    
    timeline = [
        {
            "timestamp": log.created_at.isoformat(),
            "time": log.created_at.strftime("%H:%M"),
            "agent": log.agent,
            "decision_type": log.decision_type,
            "action": log.action,
            "reasoning": log.reasoning,
            "previous_state": log.previous_state,
            "new_state": log.new_state,
            "confidence": log.confidence,
        }
        for log in logs
    ]
    
    return {"transaction_id": transaction_id, "timeline": timeline}
