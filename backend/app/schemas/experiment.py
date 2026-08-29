from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

class ExperimentCreate(BaseModel):
    name: str
    description: Optional[str] = None
    segment: Optional[str] = None
    payment_method: Optional[str] = None
    failure_reason: Optional[str] = None
    amount_min: Optional[float] = None
    amount_max: Optional[float] = None
    control_strategy: str = "retry_now"
    ai_strategy: str = "ai_optimal"

class ExperimentResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    group_name: str
    strategy: str
    total_transactions: int
    recovered_count: int
    recovery_rate: float
    total_revenue_at_risk: float
    recovered_revenue: float
    intervention_cost: float
    net_recovered: float
    avg_recovery_time: float

class ExperimentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    description: Optional[str] = None
    segment: Optional[str] = None
    payment_method: Optional[str] = None
    failure_reason: Optional[str] = None
    control_strategy: str
    ai_strategy: str
    status: str
    results: List[ExperimentResultResponse] = []
    incremental_recovery_rate: Optional[float] = None
    incremental_revenue: Optional[float] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

class ExperimentList(BaseModel):
    experiments: List[ExperimentResponse]
    total: int
