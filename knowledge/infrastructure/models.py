from __future__ import annotations
from datetime import datetime
from sqlalchemy import String, Text, Float, Integer, Boolean, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column
from persistence.base import Base
import uuid

def _uuid(): return str(uuid.uuid4())

class KnowledgePatternModel(Base):
    __tablename__ = "knw_patterns"
    __table_args__ = (Index("ix_knw_domain_type", "domain", "pattern_type"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    source_context: Mapped[str] = mapped_column(String(50), nullable=False)
    pattern_type: Mapped[str] = mapped_column(String(30), nullable=False)
    domain: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    usage_count: Mapped[int] = mapped_column(Integer, default=1)
    source_id: Mapped[str] = mapped_column(String(36), nullable=True)
    embedding: Mapped[str] = mapped_column(Text, nullable=True)
    promoted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_used_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class DomainOntologyModel(Base):
    __tablename__ = "knw_ontologies"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    domain: Mapped[str] = mapped_column(String(100), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
