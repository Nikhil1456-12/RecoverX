"""Experiment API endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_
from datetime import datetime
import json

from app.core.database import get_db
from app.models.experiment import Experiment, ExperimentResult
from app.models.transaction import PaymentTransaction
from app.models.customer import Customer

router = APIRouter()


@router.get("")
async def list_experiments(db: AsyncSession = Depends(get_db)):
    """List all experiments."""
    result = await db.execute(
        select(Experiment).order_by(desc(Experiment.created_at))
    )
    experiments = result.scalars().all()
    
    exp_list = []
    for exp in experiments:
        # Get results
        results_q = await db.execute(
            select(ExperimentResult).where(ExperimentResult.experiment_id == exp.id)
        )
        results = results_q.scalars().all()
        
        control = next((r for r in results if r.group_name == 'control'), None)
        treatment = next((r for r in results if r.group_name == 'treatment'), None)
        
        incremental_rate = None
        incremental_rev = None
        if control and treatment:
            incremental_rate = treatment.recovery_rate - control.recovery_rate
            incremental_rev = treatment.net_recovered - control.net_recovered
        
        exp_list.append({
            "id": exp.id,
            "name": exp.name,
            "description": exp.description,
            "segment": exp.segment,
            "payment_method": exp.payment_method,
            "failure_reason": exp.failure_reason,
            "control_strategy": exp.control_strategy,
            "ai_strategy": exp.ai_strategy,
            "status": exp.status,
            "results": [
                {
                    "group_name": r.group_name,
                    "strategy": r.strategy,
                    "total_transactions": r.total_transactions,
                    "recovered_count": r.recovered_count,
                    "recovery_rate": r.recovery_rate,
                    "total_revenue_at_risk": r.total_revenue_at_risk,
                    "recovered_revenue": r.recovered_revenue,
                    "intervention_cost": r.intervention_cost,
                    "net_recovered": r.net_recovered,
                    "avg_recovery_time": r.avg_recovery_time,
                }
                for r in results
            ],
            "incremental_recovery_rate": round(incremental_rate, 4) if incremental_rate is not None else None,
            "incremental_revenue": round(incremental_rev, 2) if incremental_rev is not None else None,
            "created_at": exp.created_at.isoformat(),
            "completed_at": exp.completed_at.isoformat() if exp.completed_at else None,
        })
    
    return {"experiments": exp_list, "total": len(exp_list)}


@router.get("/{experiment_id}")
async def get_experiment(experiment_id: str, db: AsyncSession = Depends(get_db)):
    """Get experiment details."""
    result = await db.execute(
        select(Experiment).where(Experiment.id == experiment_id)
    )
    exp = result.scalar_one_or_none()
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    results_q = await db.execute(
        select(ExperimentResult).where(ExperimentResult.experiment_id == exp.id)
    )
    results = results_q.scalars().all()
    
    control = next((r for r in results if r.group_name == 'control'), None)
    treatment = next((r for r in results if r.group_name == 'treatment'), None)
    
    return {
        "id": exp.id,
        "name": exp.name,
        "description": exp.description,
        "segment": exp.segment,
        "payment_method": exp.payment_method,
        "failure_reason": exp.failure_reason,
        "control_strategy": exp.control_strategy,
        "ai_strategy": exp.ai_strategy,
        "status": exp.status,
        "results": [
            {
                "group_name": r.group_name,
                "strategy": r.strategy,
                "total_transactions": r.total_transactions,
                "recovered_count": r.recovered_count,
                "recovery_rate": r.recovery_rate,
                "total_revenue_at_risk": r.total_revenue_at_risk,
                "recovered_revenue": r.recovered_revenue,
                "intervention_cost": r.intervention_cost,
                "net_recovered": r.net_recovered,
                "avg_recovery_time": r.avg_recovery_time,
            }
            for r in results
        ],
        "incremental_recovery_rate": round(treatment.recovery_rate - control.recovery_rate, 4) if control and treatment else None,
        "incremental_revenue": round(treatment.net_recovered - control.net_recovered, 2) if control and treatment else None,
        "created_at": exp.created_at.isoformat(),
        "completed_at": exp.completed_at.isoformat() if exp.completed_at else None,
    }


@router.post("/run")
async def run_experiment(data: dict, db: AsyncSession = Depends(get_db)):
    """Create and run a new experiment."""
    import uuid
    from app.services.counterfactual_engine import CounterfactualEngine, TransactionContext
    
    exp_id = f"EXP_{uuid.uuid4().hex[:8].upper()}"
    
    # Build query for matching transactions
    query = select(PaymentTransaction).where(
        PaymentTransaction.status.in_(['failed', 'recovered'])
    )
    if data.get('payment_method'):
        query = query.where(PaymentTransaction.payment_method == data['payment_method'])
    if data.get('failure_reason'):
        query = query.where(PaymentTransaction.failure_reason == data['failure_reason'])
    if data.get('amount_min'):
        query = query.where(PaymentTransaction.amount >= data['amount_min'])
    if data.get('amount_max'):
        query = query.where(PaymentTransaction.amount <= data['amount_max'])
    
    result = await db.execute(query.limit(1000))
    matching_txns = result.scalars().all()
    
    if len(matching_txns) < 10:
        raise HTTPException(status_code=400, detail="Not enough matching transactions (need at least 10)")
    
    # Split into control and treatment
    import random
    random.shuffle(matching_txns)
    mid = len(matching_txns) // 2
    control_txns = matching_txns[:mid]
    treatment_txns = matching_txns[mid:]
    
    control_strategy = data.get('control_strategy', 'retry_now')
    
    # Control group metrics
    control_recovered = sum(1 for t in control_txns if t.status == 'recovered')
    control_revenue_at_risk = sum(t.amount for t in control_txns)
    control_recovered_rev = sum(t.amount for t in control_txns if t.status == 'recovered')
    control_rate = control_recovered / len(control_txns) if control_txns else 0
    
    # Treatment group - simulate AI-optimized recovery
    engine = CounterfactualEngine()
    treatment_recovered_count = 0
    treatment_recovered_rev = 0
    treatment_cost = 0
    
    for txn in treatment_txns:
        cust_q = await db.execute(select(Customer).where(Customer.id == txn.customer_id))
        customer = cust_q.scalar_one_or_none()
        
        context = TransactionContext(
            transaction_id=txn.id,
            customer_id=txn.customer_id,
            amount=txn.amount,
            payment_method=txn.payment_method,
            failure_reason=txn.failure_reason or 'unknown',
            retry_count=txn.retry_count,
            hour_of_day=txn.created_at.hour,
            customer_segment=customer.segment if customer else 'returning',
            customer_success_rate=customer.payment_success_rate if customer else 0.8,
        )
        
        scenarios = engine.simulate(context)
        best = next((s for s in scenarios if s.action != 'stop'), scenarios[0])
        
        # Simulate outcome based on predicted probability
        recovered = random.random() < best.recovery_probability
        if recovered:
            treatment_recovered_count += 1
            treatment_recovered_rev += txn.amount
        treatment_cost += best.intervention_cost
    
    treatment_rate = treatment_recovered_count / len(treatment_txns) if treatment_txns else 0
    treatment_rev_at_risk = sum(t.amount for t in treatment_txns)
    
    # Create experiment
    experiment = Experiment(
        id=exp_id,
        name=data.get('name', 'Custom Experiment'),
        description=data.get('description'),
        segment=data.get('segment'),
        payment_method=data.get('payment_method'),
        failure_reason=data.get('failure_reason'),
        control_strategy=control_strategy,
        ai_strategy='ai_optimal',
        status='completed',
        completed_at=datetime.utcnow(),
    )
    db.add(experiment)
    
    # Control result
    control_result = ExperimentResult(
        experiment_id=exp_id,
        group_name='control',
        strategy=control_strategy,
        total_transactions=len(control_txns),
        recovered_count=control_recovered,
        recovery_rate=round(control_rate, 4),
        total_revenue_at_risk=round(control_revenue_at_risk, 2),
        recovered_revenue=round(control_recovered_rev, 2),
        intervention_cost=0,
        net_recovered=round(control_recovered_rev, 2),
        avg_recovery_time=round(random.uniform(1, 10), 1),
    )
    db.add(control_result)
    
    # Treatment result
    treatment_result = ExperimentResult(
        experiment_id=exp_id,
        group_name='treatment',
        strategy='ai_optimal',
        total_transactions=len(treatment_txns),
        recovered_count=treatment_recovered_count,
        recovery_rate=round(treatment_rate, 4),
        total_revenue_at_risk=round(treatment_rev_at_risk, 2),
        recovered_revenue=round(treatment_recovered_rev, 2),
        intervention_cost=round(treatment_cost, 2),
        net_recovered=round(treatment_recovered_rev - treatment_cost, 2),
        avg_recovery_time=round(random.uniform(10, 60), 1),
    )
    db.add(treatment_result)
    
    return {
        "id": exp_id,
        "name": experiment.name,
        "status": "completed",
        "control": {
            "transactions": len(control_txns),
            "recovery_rate": round(control_rate, 4),
            "recovered_revenue": round(control_recovered_rev, 2),
        },
        "treatment": {
            "transactions": len(treatment_txns),
            "recovery_rate": round(treatment_rate, 4),
            "recovered_revenue": round(treatment_recovered_rev, 2),
        },
        "incremental_recovery_rate": round(treatment_rate - control_rate, 4),
        "message": "Experiment completed (DEMO MODE)",
    }
