from sqlalchemy import String, Float, DateTime, Integer, ForeignKey, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from datetime import datetime

class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index('idx_audit_txn', 'transaction_id'),
        Index('idx_audit_created', 'created_at'),
    )
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    transaction_id: Mapped[str] = mapped_column(String(50), ForeignKey("payment_transactions.id"), index=True)
    agent: Mapped[str] = mapped_column(String(50))  # revenue_risk, root_cause, recovery_twin, counterfactual, policy, action_executor, evaluation
    decision_type: Mapped[str] = mapped_column(String(50))  # detection, diagnosis, simulation, policy_check, action_selection, execution, observation
    action: Mapped[str] = mapped_column(String(100))
    reasoning: Mapped[str] = mapped_column(Text, nullable=True)
    model_version: Mapped[str] = mapped_column(String(50), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=True)
    policy_result: Mapped[str] = mapped_column(Text, nullable=True)
    previous_state: Mapped[str] = mapped_column(String(30), nullable=True)
    new_state: Mapped[str] = mapped_column(String(30), nullable=True)
    execution_result: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    transaction: Mapped["PaymentTransaction"] = relationship(back_populates="audit_logs")
