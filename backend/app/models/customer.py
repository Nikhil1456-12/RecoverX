from sqlalchemy import String, Float, Boolean, DateTime, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from datetime import datetime
import uuid

class Customer(Base):
    __tablename__ = "customers"
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=lambda: f"CUST_{uuid.uuid4().hex[:6].upper()}")
    merchant_id: Mapped[str] = mapped_column(String(50), ForeignKey("merchants.id"), index=True)
    email: Mapped[str] = mapped_column(String(200), nullable=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=True)
    name: Mapped[str] = mapped_column(String(200), nullable=True)
    segment: Mapped[str] = mapped_column(String(50), default="regular")  # new, returning, premium, high_value
    total_transactions: Mapped[int] = mapped_column(Integer, default=0)
    successful_transactions: Mapped[int] = mapped_column(Integer, default=0)
    failed_transactions: Mapped[int] = mapped_column(Integer, default=0)
    total_amount_paid: Mapped[float] = mapped_column(Float, default=0.0)
    average_transaction_amount: Mapped[float] = mapped_column(Float, default=0.0)
    lifetime_value: Mapped[float] = mapped_column(Float, default=0.0)
    payment_success_rate: Mapped[float] = mapped_column(Float, default=0.0)
    preferred_payment_method: Mapped[str] = mapped_column(String(50), nullable=True)
    preferred_payment_hour: Mapped[int] = mapped_column(Integer, nullable=True)
    is_dnd: Mapped[bool] = mapped_column(Boolean, default=False)
    last_payment_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    merchant: Mapped["Merchant"] = relationship(back_populates="customers")
    transactions: Mapped[list["PaymentTransaction"]] = relationship(back_populates="customer", lazy="selectin")
