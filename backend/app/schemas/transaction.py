from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime

class TransactionBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    merchant_id: str
    customer_id: str
    amount: float
    currency: str = "INR"
    payment_method: str
    status: str
    failure_reason: Optional[str] = None
    transaction_type: str = "payment"
    retry_count: int = 0
    is_recoverable: bool = True
    recovery_status: Optional[str] = None
    recovery_priority: float = 0.0
    created_at: datetime
    updated_at: datetime

class TransactionList(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    transactions: List[TransactionBase]
    total: int
    page: int
    page_size: int

class TransactionDetail(TransactionBase):
    customer_name: Optional[str] = None
    customer_segment: Optional[str] = None
    customer_success_rate: Optional[float] = None
    last_payment_at: Optional[datetime] = None

class RecoveryTwinResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    transaction_id: str
    customer_id: str
    amount: float
    payment_method: str
    failure_reason: str
    customer_history: Optional[dict] = None
    payment_history: Optional[dict] = None
    time_features: Optional[dict] = None
    risk_features: Optional[dict] = None
    recovery_features: Optional[dict] = None
    recovery_probability: float
    recommended_action: Optional[str] = None
    explanation: Optional[str] = None
    scenarios: List["ScenarioResponse"] = []
    status: str
    created_at: datetime

class ScenarioResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    action: str
    recovery_probability: float
    expected_revenue: float
    intervention_cost: float
    friction_score: float
    expected_net_recovery: float
    confidence: float
    explanation: Optional[str] = None
    is_selected: bool = False
    is_policy_approved: bool = True
    policy_rejection_reason: Optional[str] = None

class SimulateRequest(BaseModel):
    actions: Optional[List[str]] = None  # if None, simulate all

class SimulateResponse(BaseModel):
    transaction_id: str
    scenarios: List[ScenarioResponse]
    recommended_action: str
    explanation: str

class RecoverRequest(BaseModel):
    action: Optional[str] = None  # if None, use AI recommendation
    force: bool = False

class RecoverResponse(BaseModel):
    transaction_id: str
    action: str
    status: str
    policy_approved: bool
    policy_reason: Optional[str] = None
    execution_result: Optional[str] = None
    message: str
