from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Sequence
from requirements.contracts.requirement_snapshot import RequirementSnapshot
from requirements.contracts.events import DomainEvent


class IssueSeverity(Enum):
    CRITICAL = "CRITICAL"
    HIGH     = "HIGH"
    MEDIUM   = "MEDIUM"
    LOW      = "LOW"


class IssueType(Enum):
    AMBIGUITY     = "AMBIGUITY"
    INCONSISTENCY = "INCONSISTENCY"
    DUPLICATION   = "DUPLICATION"
    COMPLETENESS  = "COMPLETENESS"
    TESTABILITY   = "TESTABILITY"


@dataclass(frozen=True)
class ValidationIssueDTO:
    issue_type:  IssueType
    severity:    IssueSeverity
    description: str
    suggestion:  str
    location:    str = ""


@dataclass(frozen=True)
class ValidationReportDTO:
    report_id:        str
    requirement_id:   str
    snapshot_version: str
    issues:           Sequence[ValidationIssueDTO]
    generated_at:     datetime

    def has_blockers(self) -> bool:
        return any(i.severity == IssueSeverity.CRITICAL for i in self.issues)

    def issue_count_by_severity(self) -> dict:
        counts = {s: 0 for s in IssueSeverity}
        for issue in self.issues:
            counts[issue.severity] += 1
        return counts


class IValidationService(ABC):
    @abstractmethod
    def validate(self, snapshot: RequirementSnapshot) -> ValidationReportDTO: ...

    @abstractmethod
    def get_report(self, report_id: str) -> ValidationReportDTO: ...


@dataclass(frozen=True)
class ValidationCompleted(DomainEvent):
    report:         ValidationReportDTO = None
    requirement_id: str = ""
    has_blockers:   bool = False


@dataclass(frozen=True)
class CriticalIssueDetected(DomainEvent):
    requirement_id: str = ""
    issue:          ValidationIssueDTO = None


@dataclass(frozen=True)
class RequirementBlockedByValidation(DomainEvent):
    requirement_id: str = ""
    blocker_count:  int = 0
