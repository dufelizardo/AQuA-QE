from __future__ import annotations
from datetime import datetime
from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from persistence.base import Base
import uuid

def _uuid(): return str(uuid.uuid4())

class ValidationReportModel(Base):
    __tablename__ = "val_reports"
    __table_args__ = (Index("ix_val_report_req", "requirement_id", "snapshot_version"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    requirement_id: Mapped[str] = mapped_column(String(36), nullable=False)
    snapshot_version: Mapped[str] = mapped_column(String(20), nullable=False)
    has_blockers: Mapped[bool] = mapped_column(Boolean, default=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    issues: Mapped[list["ValidationIssueModel"]] = relationship(back_populates="report", cascade="all, delete-orphan")

class ValidationIssueModel(Base):
    __tablename__ = "val_issues"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    report_id: Mapped[str] = mapped_column(ForeignKey("val_reports.id"), nullable=False)
    issue_type: Mapped[str] = mapped_column(String(30), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    suggestion: Mapped[str] = mapped_column(Text, nullable=True)
    location: Mapped[str] = mapped_column(Text, nullable=True)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    report: Mapped["ValidationReportModel"] = relationship(back_populates="issues")
