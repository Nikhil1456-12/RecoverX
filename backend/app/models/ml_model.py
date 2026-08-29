from sqlalchemy import String, Float, DateTime, Integer, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from datetime import datetime

class ModelVersion(Base):
    __tablename__ = "model_versions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    model_name: Mapped[str] = mapped_column(String(100))
    version: Mapped[str] = mapped_column(String(50))
    training_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    dataset_version: Mapped[str] = mapped_column(String(50), nullable=True)
    metrics: Mapped[str] = mapped_column(Text, nullable=True)  # JSON
    features: Mapped[str] = mapped_column(Text, nullable=True)  # JSON list
    artifact_path: Mapped[str] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
