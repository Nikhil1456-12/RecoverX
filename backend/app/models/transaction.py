from sqlalchemy import String, Float, Boolean, DateTime, Integer, ForeignKey, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from datetime import datetime
import uuid

class PaymentTransaction(Base):
    __tablename__ = "payment_transactions"
    __table_args__ = (
        Index('idx_txn_status', 'status'),
        Index('idx_txn_merchant', 'merchant_id'),
        Index('idx_txn_customer', 'customer_id'),
        Index('idx_txn_created', 'created_at'),
        Index('idx_txn_failure_reason', 'failure_reason'),
    )
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=lambda: f"TXN_{uuid.uuid4().hex[:8].upper()}")
    merchant_id: Mapped[str] = mapped_column(String(50), ForeignKey("merchants.id"), index=True)
    customer_id: Mapped[str] = mapped_column(String(50), ForeignKey("customers.id"), index=True)
    amount: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(3), default="INR")
    payment_method: Mapped[str] = mapped_column(String(50))  # upi, card, netbanking, wallet
    status: Mapped[str] = mapped_column(String(30))  # success, failed, pending, recovered
    failure_reason: Mapped[str] = mapped_column(String(100), nullable=True)
    gateway_response: Mapped[str] = mapped_column(Text, nullable=True)
    transaction_type: Mapped[str] = mapped_column(String(30), default="payment")  # payment, subscription, invoice
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    is_recoverable: Mapped[bool] = mapped_column(Boolean, default=True)
    recovery_status: Mapped[str] = mapped_column(String(30), nullable=True)  # detected, diagnosed, simulating, recovering, recovered, failed, stopped
    recovery_priority: Mapped[float] = mapped_column(Float, default=0.0)
    razorpay_payment_id: Mapped[str] = mapped_column(String(100), nullable=True)
    razorpay_order_id: Mapped[str] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    merchant: Mapped["Merchant"] = relationship(back_populates="transactions")
    customer: Mapped["Customer"] = relationship(back_populates="transactions")
    attempts: Mapped[list["PaymentAttempt"]] = relationship(back_populates="transaction", lazy="selectin")
    failure_events: Mapped[list["FailureEvent"]] = relationship(back_populates="transaction", lazy="selectin")
    recovery_twin: Mapped["RecoveryTwin"] = relationship(back_populates="transaction", uselist=False, lazy="selectin")
    recovery_actions: Mapped[list["RecoveryAction"]] = relationship(back_populates="transaction", lazy="selectin")
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="transaction", lazy="selectin")


class PaymentAttempt(Base):
    __tablename__ = "payment_attempts"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    transaction_id: Mapped[str] = mapped_column(String(50), ForeignKey("payment_transactions.id"), index=True)
    attempt_number: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(30))  # success, failed
    failure_reason: Mapped[str] = mapped_column(String(100), nullable=True)
    payment_method: Mapped[str] = mapped_column(String(50))
    gateway_response: Mapped[str] = mapped_column(Text, nullable=True)
    amount: Mapped[float] = mapped_column(Float)
    attempted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    transaction: Mapped["PaymentTransaction"] = relationship(back_populates="attempts")


class FailureEvent(Base):
    __tablename__ = "failure_events"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    transaction_id: Mapped[str] = mapped_column(String(50), ForeignKey("payment_transactions.id"), index=True)
    failure_reason: Mapped[str] = mapped_column(String(100))
    failure_category: Mapped[str] = mapped_column(String(50))  # bank, network, card, authentication, checkout, subscription, invoice
    root_cause: Mapped[str] = mapped_column(String(200), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    supporting_signals: Mapped[str] = mapped_column(Text, nullable=True)
    detected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    transaction: Mapped["PaymentTransaction"] = relationship(back_populates="failure_events")
