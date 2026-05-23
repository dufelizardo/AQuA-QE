from __future__ import annotations
from datetime import datetime
from sqlalchemy import String, Text, Float, Integer, Boolean, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column
from persistence.base import Base
import uuid


def _uuid() -> str:
    return str(uuid.uuid4())


class PromptLogModel(Base):
    __tablename__ = "aig_prompt_logs"
    __table_args__ = (Index("ix_aig_log_context", "context_id"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    context_id: Mapped[str] = mapped_column(String(36), nullable=False)
    purpose: Mapped[str] = mapped_column(String(30), nullable=False)
    provider_used: Mapped[str] = mapped_column(String(20), nullable=False)
    model_used: Mapped[str] = mapped_column(String(50), nullable=False)
    tokens_in: Mapped[int] = mapped_column(Integer, nullable=False)
    tokens_out: Mapped[int] = mapped_column(Integer, nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    cached: Mapped[bool] = mapped_column(Boolean, default=False)
    called_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
