from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    transaction_id: str
    agent: str
    decision_type: str
    action: str
    reasoning: Optional[str] = None
    model_version: Optional[str] = None
    confidence: Optional[float] = None
    policy_result: Optional[str] = None
    previous_state: Optional[str] = None
    new_state: Optional[str] = None
    execution_result: Optional[str] = None
    created_at: datetime

class AuditLogList(BaseModel):
    logs: List[AuditLogResponse]
    total: int
    page: int
    page_size: int
