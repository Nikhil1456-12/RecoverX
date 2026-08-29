"""Audit log API endpoints."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_
from typing import Optional

from app.core.database import get_db
from app.models.audit import AuditLog

router = APIRouter()


@router.get("")
async def list_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    transaction_id: Optional[str] = None,
    agent: Optional[str] = None,
    decision_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """List audit logs with pagination and filters."""
    query = select(AuditLog).order_by(desc(AuditLog.created_at))
    count_query = select(func.count(AuditLog.id))
    
    conditions = []
    if transaction_id:
        conditions.append(AuditLog.transaction_id == transaction_id)
    if agent:
        conditions.append(AuditLog.agent == agent)
    if decision_type:
        conditions.append(AuditLog.decision_type == decision_type)
    
    if conditions:
        query = query.where(and_(*conditions))
        count_query = count_query.where(and_(*conditions))
    
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    result = await db.execute(query)
    logs = result.scalars().all()
    
    return {
        "logs": [
            {
                "id": log.id,
                "transaction_id": log.transaction_id,
                "agent": log.agent,
                "decision_type": log.decision_type,
                "action": log.action,
                "reasoning": log.reasoning,
                "model_version": log.model_version,
                "confidence": log.confidence,
                "policy_result": log.policy_result,
                "previous_state": log.previous_state,
                "new_state": log.new_state,
                "execution_result": log.execution_result,
                "created_at": log.created_at.isoformat(),
            }
            for log in logs
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }
