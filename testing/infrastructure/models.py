from __future__ import annotations
from datetime import datetime
from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from persistence.base import Base
import uuid

def _uuid(): return str(uuid.uuid4())

class TestSuiteModel(Base):
    __tablename__ = "tst_suites"
    __table_args__ = (Index("ix_tst_suite_project", "project_id"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(String(36), nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    scenarios: Mapped[list["TestScenarioModel"]] = relationship(back_populates="suite", cascade="all, delete-orphan")

class TestScenarioModel(Base):
    __tablename__ = "tst_scenarios"
    __table_args__ = (Index("ix_tst_scenario_req", "requirement_id"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    suite_id: Mapped[str] = mapped_column(ForeignKey("tst_suites.id"), nullable=False)
    requirement_id: Mapped[str] = mapped_column(String(36), nullable=False)
    acceptance_criteria_id: Mapped[str] = mapped_column(String(36), nullable=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    test_type: Mapped[str] = mapped_column(String(30), nullable=False)
    technique: Mapped[str] = mapped_column(String(30), nullable=False)
    gherkin_feature: Mapped[str] = mapped_column(Text, nullable=False)
    gherkin_scenario: Mapped[str] = mapped_column(Text, nullable=False)
    gherkin_given: Mapped[str] = mapped_column(Text, nullable=False)
    gherkin_when: Mapped[str] = mapped_column(Text, nullable=False)
    gherkin_then: Mapped[str] = mapped_column(Text, nullable=False)
    gherkin_tags: Mapped[str] = mapped_column(Text, default="[]")
    automation_candidate: Mapped[bool] = mapped_column(Boolean, default=False)
    automation_strategy: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="DRAFT")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    suite: Mapped["TestSuiteModel"] = relationship(back_populates="scenarios")
