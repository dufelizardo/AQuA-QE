from __future__ import annotations
from datetime import datetime
from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey, Index, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from persistence.base import Base
import uuid

def _uuid(): return str(uuid.uuid4())

class AccessibilityReportModel(Base):
    __tablename__ = "acc_reports"
    __table_args__ = (Index("ix_acc_report_project", "project_id"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(String(36), nullable=False)
    conformance_level_achieved: Mapped[str] = mapped_column(String(5), nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    wcag_issues: Mapped[list["WCAGIssueModel"]] = relationship(back_populates="report", cascade="all, delete-orphan")
    heuristic_issues: Mapped[list["HeuristicIssueModel"]] = relationship(back_populates="report", cascade="all, delete-orphan")

class WCAGIssueModel(Base):
    __tablename__ = "acc_wcag_issues"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    report_id: Mapped[str] = mapped_column(ForeignKey("acc_reports.id"), nullable=False)
    requirement_id: Mapped[str] = mapped_column(String(36), nullable=False)
    wcag_code: Mapped[str] = mapped_column(String(20), nullable=False)
    wcag_level: Mapped[str] = mapped_column(String(5), nullable=False)
    wcag_guideline: Mapped[str] = mapped_column(String(20), default="WCAG 2.1")
    description: Mapped[str] = mapped_column(Text, nullable=False)
    recommendation: Mapped[str] = mapped_column(Text, nullable=True)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    report: Mapped["AccessibilityReportModel"] = relationship(back_populates="wcag_issues")

class HeuristicIssueModel(Base):
    __tablename__ = "acc_heuristic_issues"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    report_id: Mapped[str] = mapped_column(ForeignKey("acc_reports.id"), nullable=False)
    requirement_id: Mapped[str] = mapped_column(String(36), nullable=False)
    heuristic_number: Mapped[int] = mapped_column(Integer, nullable=False)
    heuristic_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    recommendation: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    report: Mapped["AccessibilityReportModel"] = relationship(back_populates="heuristic_issues")
