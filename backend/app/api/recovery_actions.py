"""Recovery actions API."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.core.database import get_db
from app.models.recovery import RecoveryAction, RecoveryOutcome

router = APIRouter()


@router.get("")
async def list_recovery_actions(db: AsyncSession = Depends(get_db)):
    """List all recovery actions with outcomes."""
    result = await db.execute(
        select(RecoveryAction).order_by(desc(RecoveryAction.created_at)).limit(100)
    )
    actions = result.scalars().all()
    
    action_list = []
    for a in actions:
        # Get outcome
        outcome_q = await db.execute(
            select(RecoveryOutcome).where(RecoveryOutcome.action_id == a.id)
        )
        outcome = outcome_q.scalar_one_or_none()
        
        action_list.append({
            "id": a.id,
            "transaction_id": a.transaction_id,
            "action_type": a.action_type,
            "status": a.status,
            "scheduled_at": a.scheduled_at.isoformat() if a.scheduled_at else None,
            "executed_at": a.executed_at.isoformat() if a.executed_at else None,
            "result": a.result,
            "cost": a.cost,
            "outcome": {
                "recovered": outcome.recovered,
                "recovered_amount": outcome.recovered_amount,
                "net_recovered": outcome.net_recovered,
                "recovery_time_minutes": outcome.recovery_time_minutes,
            } if outcome else None,
        })
    
    # Summary stats
    total_actions = len(action_list)
    successful = sum(1 for a in action_list if a.get('result') == 'success')
    total_cost = sum(a['cost'] for a in action_list)
    total_recovered = sum(a['outcome']['recovered_amount'] for a in action_list if a.get('outcome') and a['outcome']['recovered'])
    
    return {
        "actions": action_list,
        "summary": {
            "total_actions": total_actions,
            "successful": successful,
            "success_rate": successful / total_actions if total_actions > 0 else 0,
            "total_cost": round(total_cost, 2),
            "total_recovered": round(total_recovered, 2),
        }
    }
