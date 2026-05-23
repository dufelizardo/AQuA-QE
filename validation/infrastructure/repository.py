from __future__ import annotations
from typing import Optional, List
from sqlalchemy.orm import Session
from validation.infrastructure.models import ValidationReportModel, ValidationIssueModel
from validation.domain.entities import ValidationReport, ValidationIssue
from validation.contracts import IssueSeverity, IssueType


class ValidationRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def save_report(self, report: ValidationReport) -> None:
        self._s.add(ValidationReportModel(
            id=report.id, requirement_id=report.requirement_id,
            snapshot_version=report.snapshot_version,
            has_blockers=report.has_blockers(), generated_at=report.generated_at,
        ))
        for issue in report.issues:
            self._s.add(ValidationIssueModel(
                id=issue.id, report_id=report.id,
                issue_type=issue.issue_type.value, severity=issue.severity.value,
                description=issue.description, suggestion=issue.suggestion,
                location=issue.location, resolved=issue.resolved,
            ))
        self._s.flush()

    def get_report(self, report_id: str) -> Optional[ValidationReport]:
        m = self._s.get(ValidationReportModel, report_id)
        if not m:
            return None
        return ValidationReport(
            id=m.id, requirement_id=m.requirement_id, snapshot_version=m.snapshot_version,
            issues=[ValidationIssue(
                id=i.id, issue_type=IssueType(i.issue_type), severity=IssueSeverity(i.severity),
                description=i.description, suggestion=i.suggestion or "", location=i.location or "",
                resolved=i.resolved,
            ) for i in m.issues],
            generated_at=m.generated_at,
        )

    def latest_for_requirement(self, requirement_id: str) -> Optional[ValidationReport]:
        m = (
            self._s.query(ValidationReportModel)
            .filter(ValidationReportModel.requirement_id == requirement_id)
            .order_by(ValidationReportModel.generated_at.desc())
            .first()
        )
        return self.get_report(m.id) if m else None
