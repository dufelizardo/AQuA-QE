from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import List
from validation.contracts import IssueSeverity, IssueType, ValidationReportDTO, ValidationIssueDTO


@dataclass
class ValidationIssue:
    id:          str
    issue_type:  IssueType
    severity:    IssueSeverity
    description: str
    suggestion:  str
    location:    str = ""
    resolved:    bool = False

    def is_blocker(self) -> bool:
        return self.severity == IssueSeverity.CRITICAL

    def to_dto(self) -> ValidationIssueDTO:
        return ValidationIssueDTO(
            issue_type=self.issue_type, severity=self.severity,
            description=self.description, suggestion=self.suggestion, location=self.location,
        )


@dataclass
class ValidationReport:
    id:               str
    requirement_id:   str
    snapshot_version: str
    issues:           List[ValidationIssue] = field(default_factory=list)
    generated_at:     datetime = field(default_factory=datetime.utcnow)

    def has_blockers(self) -> bool:
        return any(i.is_blocker() for i in self.issues)

    def critical_count(self) -> int:
        return sum(1 for i in self.issues if i.is_blocker())

    def to_dto(self) -> ValidationReportDTO:
        return ValidationReportDTO(
            report_id=self.id, requirement_id=self.requirement_id,
            snapshot_version=self.snapshot_version,
            issues=[i.to_dto() for i in self.issues],
            generated_at=self.generated_at,
        )
