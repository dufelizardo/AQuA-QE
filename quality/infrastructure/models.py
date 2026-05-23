from __future__ import annotations
from datetime import datetime
from sqlalchemy import String, Text, Float, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from persistence.base import Base
import uuid

def _uuid(): return str(uuid.uuid4())

class QualityReportModel(Base):
    __tablename__ = "qlt_reports"
    __table_args__ = (Index("ix_qlt_report_project", "project_id", "generated_at"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(String(36), nullable=False)
    overall_status: Mapped[str] = mapped_column(String(20), nullable=False)
    previous_report_id: Mapped[str] = mapped_column(String(36), nullable=True)
    integrity_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    dimension_scores: Mapped[list["QualityDimensionScoreModel"]] = relationship(back_populates="report", cascade="all, delete-orphan")

class QualityDimensionScoreModel(Base):
    __tablename__ = "qlt_dimension_scores"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    report_id: Mapped[str] = mapped_column(ForeignKey("qlt_reports.id"), nullable=False)
    dimension: Mapped[str] = mapped_column(String(50), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    evidence: Mapped[str] = mapped_column(Text, nullable=True)
    report: Mapped["QualityReportModel"] = relationship(back_populates="dimension_scores")

class QualityPolicyModel(Base):
    __tablename__ = "qlt_policies"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(String(36), nullable=False)
    dimension: Mapped[str] = mapped_column(String(50), nullable=False)
    threshold: Mapped[float] = mapped_column(Float, nullable=False)
    blocking: Mapped[bool] = mapped_column(Boolean, default=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
