from __future__ import annotations
from typing import Optional
from sqlalchemy.orm import Session
from accessibility.infrastructure.models import AccessibilityReportModel, WCAGIssueModel, HeuristicIssueModel
from accessibility.domain.entities import AccessibilityReport, WCAGIssue, HeuristicIssue
from accessibility.contracts import WCAGCriterion, ConformanceLevel


class AccessibilityRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def save_report(self, report: AccessibilityReport) -> None:
        self._s.add(AccessibilityReportModel(
            id=report.id, project_id=report.project_id,
            conformance_level_achieved=report.conformance_level_achieved().value,
            generated_at=report.generated_at,
        ))
        for issue in report.wcag_issues:
            self._s.add(WCAGIssueModel(
                id=issue.id, report_id=report.id, requirement_id=issue.requirement_id,
                wcag_code=issue.criterion.code, wcag_level=issue.criterion.level.value,
                wcag_guideline=issue.criterion.guideline, description=issue.description,
                recommendation=issue.recommendation, resolved=issue.resolved,
            ))
        for issue in report.heuristic_issues:
            self._s.add(HeuristicIssueModel(
                id=issue.id, report_id=report.id, requirement_id=issue.requirement_id,
                heuristic_number=issue.heuristic_number, heuristic_name=issue.heuristic_name,
                description=issue.description, recommendation=issue.recommendation,
            ))
        self._s.flush()

    def get_report(self, report_id: str) -> Optional[AccessibilityReport]:
        m = self._s.get(AccessibilityReportModel, report_id)
        if not m:
            return None
        report = AccessibilityReport(id=m.id, project_id=m.project_id, generated_at=m.generated_at)
        for wi in m.wcag_issues:
            report.wcag_issues.append(WCAGIssue(
                id=wi.id, criterion=WCAGCriterion(wi.wcag_code, ConformanceLevel(wi.wcag_level), "", wi.wcag_guideline),
                description=wi.description, recommendation=wi.recommendation or "",
                requirement_id=wi.requirement_id, resolved=wi.resolved,
            ))
        for hi in m.heuristic_issues:
            report.heuristic_issues.append(HeuristicIssue(
                id=hi.id, heuristic_number=hi.heuristic_number, heuristic_name=hi.heuristic_name,
                description=hi.description, recommendation=hi.recommendation or "",
                requirement_id=hi.requirement_id,
            ))
        return report

    def latest_for_project(self, project_id: str) -> Optional[AccessibilityReport]:
        m = (self._s.query(AccessibilityReportModel)
             .filter(AccessibilityReportModel.project_id == project_id)
             .order_by(AccessibilityReportModel.generated_at.desc()).first())
        return self.get_report(m.id) if m else None
