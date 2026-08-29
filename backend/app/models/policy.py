from sqlalchemy import String, Float, Boolean, DateTime, Integer, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from datetime import datetime

class Policy(Base):
    __tablename__ = "policies"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    merchant_id: Mapped[str] = mapped_column(String(50), ForeignKey("merchants.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    rule_type: Mapped[str] = mapped_column(String(50))  # max_retry, cooldown, budget, amount_limit, dnd, channel, escalation
    rule_config: Mapped[str] = mapped_column(Text)  # JSON config
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PolicyDecision(Base):
    __tablename__ = "policy_decisions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    transaction_id: Mapped[str] = mapped_column(String(50), ForeignKey("payment_transactions.id"), index=True)
    action_type: Mapped[str] = mapped_column(String(50))
    approved: Mapped[bool] = mapped_column(Boolean)
    reason: Mapped[str] = mapped_column(Text, nullable=True)
    policies_evaluated: Mapped[str] = mapped_column(Text, nullable=True)  # JSON list
    decided_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
