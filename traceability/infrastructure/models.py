from __future__ import annotations
from datetime import datetime
from sqlalchemy import String, Text, Boolean, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column
from persistence.base import Base
import uuid

def _uuid(): return str(uuid.uuid4())

class TraceabilityLinkModel(Base):
    __tablename__ = "trc_links"
    __table_args__ = (
        Index("ix_trc_source", "source_type", "source_id"),
        Index("ix_trc_target", "target_type", "target_id"),
        Index("ix_trc_project_active", "project_id", "active"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(String(36), nullable=False)
    source_type: Mapped[str] = mapped_column(String(30), nullable=False)
    source_id: Mapped[str] = mapped_column(String(36), nullable=False)
    source_ver: Mapped[str] = mapped_column(String(20), nullable=False)
    target_type: Mapped[str] = mapped_column(String(30), nullable=False)
    target_id: Mapped[str] = mapped_column(String(36), nullable=False)
    target_ver: Mapped[str] = mapped_column(String(20), nullable=False)
    link_type: Mapped[str] = mapped_column(String(20), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    invalidated_reason: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    invalidated_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
