from sqlalchemy import String, Float, Boolean, DateTime, Text, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from datetime import datetime
import uuid

class Merchant(Base):
    __tablename__ = "merchants"
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=lambda: f"MERCH_{uuid.uuid4().hex[:8].upper()}")
    name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str] = mapped_column(String(200))
    business_type: Mapped[str] = mapped_column(String(100), default="ecommerce")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    settings: Mapped["MerchantSettings"] = relationship(back_populates="merchant", uselist=False, lazy="selectin")
    customers: Mapped[list["Customer"]] = relationship(back_populates="merchant", lazy="selectin")
    transactions: Mapped[list["PaymentTransaction"]] = relationship(back_populates="merchant", lazy="selectin")

class MerchantSettings(Base):
    __tablename__ = "merchant_settings"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    merchant_id: Mapped[str] = mapped_column(String(50), ForeignKey("merchants.id"))
    daily_recovery_budget: Mapped[float] = mapped_column(Float, default=5000.0)
    max_retries_per_transaction: Mapped[int] = mapped_column(Integer, default=3)
    retry_cooldown_minutes: Mapped[int] = mapped_column(Integer, default=15)
    max_recovery_attempts_per_customer: Mapped[int] = mapped_column(Integer, default=5)
    max_auto_recovery_amount: Mapped[float] = mapped_column(Float, default=50000.0)
    allowed_channels: Mapped[str] = mapped_column(Text, default="retry,payment_link,whatsapp,sms,email,escalation")
    dnd_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    auto_recovery_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    merchant: Mapped["Merchant"] = relationship(back_populates="settings")
