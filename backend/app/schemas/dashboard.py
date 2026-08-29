from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime

class KPISummary(BaseModel):
    total_processed_revenue: float
    revenue_at_risk: float
    revenue_recovered: float
    recovery_rate: float
    net_recovered_revenue: float
    intervention_cost: float
    failed_payment_count: int
    checkout_abandonment_count: int
    subscription_failure_count: int
    invoice_failure_count: int
    recovery_budget_total: float
    recovery_budget_used: float
    recovery_budget_utilization: float
    incremental_recovery: float
    total_transactions: int
    successful_transactions: int
    failed_transactions: int
    recovered_transactions: int
    active_recoveries: int

class TrendPoint(BaseModel):
    date: str
    value: float
    label: Optional[str] = None

class TrendData(BaseModel):
    revenue_at_risk: List[TrendPoint]
    recovery_over_time: List[TrendPoint]
    recovery_rate_trend: List[TrendPoint]

class LeakageCategory(BaseModel):
    category: str
    amount: float
    percentage: float
    transaction_count: int
    avg_recovery_rate: float

class LeakageDNA(BaseModel):
    categories: List[LeakageCategory]
    high_risk_hours: List[Dict]
    problematic_methods: List[Dict]
    affected_segments: List[Dict]
    ai_explanation: str

class RecoveryOpportunity(BaseModel):
    transaction_id: str
    customer_id: str
    amount: float
    failure_reason: str
    payment_method: str
    recovery_probability: float
    recommended_action: str
    expected_net_recovery: float

class DashboardData(BaseModel):
    kpis: KPISummary
    trends: TrendData
    leakage: LeakageDNA
    top_opportunities: List[RecoveryOpportunity]
    recent_recoveries: List[dict]
