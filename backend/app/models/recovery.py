from sqlalchemy import String, Float, Boolean, DateTime, Integer, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from datetime import datetime
import uuid

class RecoveryTwin(Base):
    __tablename__ = "recovery_twins"
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=lambda: f"TWIN_{uuid.uuid4().hex[:8].upper()}")
    transaction_id: Mapped[str] = mapped_column(String(50), ForeignKey("payment_transactions.id"), unique=True, index=True)
    customer_id: Mapped[str] = mapped_column(String(50), ForeignKey("customers.id"))
    
    amount: Mapped[float] = mapped_column(Float)
    payment_method: Mapped[str] = mapped_column(String(50))
    failure_reason: Mapped[str] = mapped_column(String(100))
    
    # Customer features as JSON
    customer_history: Mapped[str] = mapped_column(Text, nullable=True)  # JSON
    payment_history: Mapped[str] = mapped_column(Text, nullable=True)   # JSON
    time_features: Mapped[str] = mapped_column(Text, nullable=True)     # JSON
    merchant_context: Mapped[str] = mapped_column(Text, nullable=True)  # JSON
    risk_features: Mapped[str] = mapped_column(Text, nullable=True)     # JSON
    recovery_features: Mapped[str] = mapped_column(Text, nullable=True) # JSON
    
    recovery_probability: Mapped[float] = mapped_column(Float, default=0.0)
    recommended_action: Mapped[str] = mapped_column(String(50), nullable=True)
    explanation: Mapped[str] = mapped_column(Text, nullable=True)
    
    status: Mapped[str] = mapped_column(String(30), default="created")  # created, simulated, action_selected, executing, completed
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    transaction: Mapped["PaymentTransaction"] = relationship(back_populates="recovery_twin")
    scenarios: Mapped[list["RecoveryScenario"]] = relationship(back_populates="twin", lazy="selectin")


class RecoveryScenario(Base):
    __tablename__ = "recovery_scenarios"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    twin_id: Mapped[str] = mapped_column(String(50), ForeignKey("recovery_twins.id"), index=True)
    action: Mapped[str] = mapped_column(String(50))  # retry_now, retry_15m, retry_45m, whatsapp, payment_link, sms, email, human_escalation, stop
    recovery_probability: Mapped[float] = mapped_column(Float)
    expected_revenue: Mapped[float] = mapped_column(Float)
    intervention_cost: Mapped[float] = mapped_column(Float, default=0.0)
    friction_score: Mapped[float] = mapped_column(Float, default=0.0)
    expected_net_recovery: Mapped[float] = mapped_column(Float)
    confidence: Mapped[float] = mapped_column(Float)
    explanation: Mapped[str] = mapped_column(Text, nullable=True)
    is_selected: Mapped[bool] = mapped_column(Boolean, default=False)
    is_policy_approved: Mapped[bool] = mapped_column(Boolean, default=True)
    policy_rejection_reason: Mapped[str] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    twin: Mapped["RecoveryTwin"] = relationship(back_populates="scenarios")


class RecoveryAction(Base):
    __tablename__ = "recovery_actions"
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=lambda: f"ACT_{uuid.uuid4().hex[:8].upper()}")
    transaction_id: Mapped[str] = mapped_column(String(50), ForeignKey("payment_transactions.id"), index=True)
    action_type: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(30), default="pending")  # pending, executing, completed, failed, cancelled
    scheduled_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    executed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    result: Mapped[str] = mapped_column(String(30), nullable=True)  # success, failure
    result_details: Mapped[str] = mapped_column(Text, nullable=True)
    cost: Mapped[float] = mapped_column(Float, default=0.0)
    model_version: Mapped[str] = mapped_column(String(50), nullable=True)
    idempotency_key: Mapped[str] = mapped_column(String(100), unique=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    transaction: Mapped["PaymentTransaction"] = relationship(back_populates="recovery_actions")
    outcome: Mapped["RecoveryOutcome"] = relationship(back_populates="action", uselist=False, lazy="selectin")


class RecoveryOutcome(Base):
    __tablename__ = "recovery_outcomes"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    action_id: Mapped[str] = mapped_column(String(50), ForeignKey("recovery_actions.id"), unique=True)
    recovered: Mapped[bool] = mapped_column(Boolean)
    recovered_amount: Mapped[float] = mapped_column(Float, default=0.0)
    recovery_time_minutes: Mapped[float] = mapped_column(Float, nullable=True)
    intervention_cost: Mapped[float] = mapped_column(Float, default=0.0)
    net_recovered: Mapped[float] = mapped_column(Float, default=0.0)
    customer_feedback: Mapped[str] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    action: Mapped["RecoveryAction"] = relationship(back_populates="outcome")
