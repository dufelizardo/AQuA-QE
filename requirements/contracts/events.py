from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4
from typing import Any


@dataclass(frozen=True)
class DomainEvent:
    event_id: str = field(default_factory=lambda: str(uuid4()))
    occurred_at: datetime = field(default_factory=datetime.utcnow)
    schema_version: str = "1.0"


@dataclass(frozen=True)
class RequirementCreated(DomainEvent):
    snapshot: Any = None
    session_id: str = ""


@dataclass(frozen=True)
class RequirementRefined(DomainEvent):
    snapshot: Any = None
    previous_version: str = ""
    change_reason: str = ""


@dataclass(frozen=True)
class RequirementApproved(DomainEvent):
    requirement_id: str = ""
    project_id: str = ""
    approved_by: str = ""


@dataclass(frozen=True)
class GapDetected(DomainEvent):
    project_id: str = ""
    gap_type: str = ""
    description: str = ""
    suggested_rqs: list = field(default_factory=list)


@dataclass(frozen=True)
class ErsGenerated(DomainEvent):
    project_id: str = ""
    artifact_path: str = ""
    req_count: int = 0


@dataclass(frozen=True)
class ElicitationSessionStarted(DomainEvent):
    session_id: str = ""
    project_id: str = ""
