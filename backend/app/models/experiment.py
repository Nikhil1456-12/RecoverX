from sqlalchemy import String, Float, DateTime, Integer, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from datetime import datetime
import uuid

class Experiment(Base):
    __tablename__ = "experiments"
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=lambda: f"EXP_{uuid.uuid4().hex[:8].upper()}")
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, nullable=True)
    segment: Mapped[str] = mapped_column(String(100), nullable=True)
    payment_method: Mapped[str] = mapped_column(String(50), nullable=True)
    failure_reason: Mapped[str] = mapped_column(String(100), nullable=True)
    amount_min: Mapped[float] = mapped_column(Float, nullable=True)
    amount_max: Mapped[float] = mapped_column(Float, nullable=True)
    control_strategy: Mapped[str] = mapped_column(String(50), default="retry_now")
    ai_strategy: Mapped[str] = mapped_column(String(50), default="ai_optimal")
    status: Mapped[str] = mapped_column(String(30), default="pending")  # pending, running, completed
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    results: Mapped[list["ExperimentResult"]] = relationship(back_populates="experiment", lazy="selectin")


class ExperimentResult(Base):
    __tablename__ = "experiment_results"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    experiment_id: Mapped[str] = mapped_column(String(50), ForeignKey("experiments.id"), index=True)
    group_name: Mapped[str] = mapped_column(String(30))  # control, treatment
    strategy: Mapped[str] = mapped_column(String(50))
    total_transactions: Mapped[int] = mapped_column(Integer, default=0)
    recovered_count: Mapped[int] = mapped_column(Integer, default=0)
    recovery_rate: Mapped[float] = mapped_column(Float, default=0.0)
    total_revenue_at_risk: Mapped[float] = mapped_column(Float, default=0.0)
    recovered_revenue: Mapped[float] = mapped_column(Float, default=0.0)
    intervention_cost: Mapped[float] = mapped_column(Float, default=0.0)
    net_recovered: Mapped[float] = mapped_column(Float, default=0.0)
    avg_recovery_time: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    experiment: Mapped["Experiment"] = relationship(back_populates="results")
