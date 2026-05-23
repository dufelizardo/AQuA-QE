from __future__ import annotations
from datetime import datetime
from sqlalchemy import String, Text, Float, Integer, Boolean, DateTime, ForeignKey, UniqueConstraint, Index, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship
from persistence.base import Base
import uuid


def _uuid() -> str:
    return str(uuid.uuid4())


class ProjectModel(Base):
    __tablename__ = "req_projects"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    domain: Mapped[str] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    requirements: Mapped[list["RequirementModel"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    sessions: Mapped[list["SessionModel"]] = relationship(back_populates="project", cascade="all, delete-orphan")


class SessionModel(Base):
    __tablename__ = "req_sessions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(ForeignKey("req_projects.id"), nullable=False)
    input_type: Mapped[str] = mapped_column(String(50), nullable=False)
    raw_input: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_input: Mapped[str] = mapped_column(Text, nullable=True)
    language: Mapped[str] = mapped_column(String(10), default="pt")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    project: Mapped["ProjectModel"] = relationship(back_populates="sessions")
    requirements: Mapped[list["RequirementModel"]] = relationship(back_populates="session")


class RequirementModel(Base):
    __tablename__ = "req_requirements"
    __table_args__ = (
        Index("ix_req_project_status", "project_id", "status"),
        Index("ix_req_type_priority", "req_type", "priority"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(ForeignKey("req_projects.id"), nullable=False)
    session_id: Mapped[str] = mapped_column(ForeignKey("req_sessions.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    req_type: Mapped[str] = mapped_column(String(20), nullable=False)
    priority: Mapped[str] = mapped_column(String(10), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="DRAFT", nullable=False)
    version_major: Mapped[int] = mapped_column(Integer, default=1)
    version_minor: Mapped[int] = mapped_column(Integer, default=0)
    version_changelog: Mapped[str] = mapped_column(Text, nullable=True)
    score_clarity: Mapped[float] = mapped_column(Float, default=0.0)
    score_completeness: Mapped[float] = mapped_column(Float, default=0.0)
    score_testability: Mapped[float] = mapped_column(Float, default=0.0)
    score_consistency: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    project: Mapped["ProjectModel"] = relationship(back_populates="requirements")
    session: Mapped["SessionModel"] = relationship(back_populates="requirements")
    acceptance_criteria: Mapped[list["AcceptanceCriteriaModel"]] = relationship(back_populates="requirement", cascade="all, delete-orphan")


class AcceptanceCriteriaModel(Base):
    __tablename__ = "req_acceptance_criteria"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    requirement_id: Mapped[str] = mapped_column(ForeignKey("req_requirements.id"), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    given_context: Mapped[str] = mapped_column(Text, nullable=False)
    when_action: Mapped[str] = mapped_column(Text, nullable=False)
    then_outcome: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="DRAFT")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    requirement: Mapped["RequirementModel"] = relationship(back_populates="acceptance_criteria")


class BusinessRuleModel(Base):
    __tablename__ = "req_business_rules"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(ForeignKey("req_projects.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    condition: Mapped[str] = mapped_column(Text, nullable=True)
    action: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
