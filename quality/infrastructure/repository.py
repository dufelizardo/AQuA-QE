from __future__ import annotations
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from quality.infrastructure.models import QualityReportModel, QualityDimensionScoreModel, QualityPolicyModel
from quality.domain.entities import QualityReport, QualityPolicy
from quality.contracts import GateStatus, PolicyRule, QualityDimensionScore
from validation.infrastructure.models import ValidationReportModel, ValidationIssueModel
from traceability.infrastructure.models import TraceabilityLinkModel
from testing.infrastructure.models import TestSuiteModel, TestScenarioModel
from accessibility.infrastructure.models import AccessibilityReportModel, WCAGIssueModel
from requirements.infrastructure.models import RequirementModel


class QualityRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def save_report(self, report: QualityReport) -> None:
        self._s.add(QualityReportModel(
            id=report.id, project_id=report.project_id, overall_status=report.overall_status.value,
            previous_report_id=report.previous_report_id, integrity_hash=report.integrity_hash,
            generated_at=report.generated_at,
        ))
        for d in report.dimension_scores:
            self._s.add(QualityDimensionScoreModel(
                report_id=report.id, dimension=d.dimension, score=d.score,
                status=d.status.value, evidence=d.evidence,
            ))
        self._s.flush()

    def get_report(self, report_id: str) -> Optional[QualityReport]:
        m = self._s.get(QualityReportModel, report_id)
        return self._to_domain(m) if m else None

    def get_latest_report(self, project_id: str) -> Optional[QualityReport]:
        m = (self._s.query(QualityReportModel)
             .filter(QualityReportModel.project_id == project_id)
             .order_by(QualityReportModel.generated_at.desc()).first())
        return self._to_domain(m) if m else None

    def get_policy(self, project_id: str) -> Optional[QualityPolicy]:
        rules = (self._s.query(QualityPolicyModel)
                 .filter(QualityPolicyModel.project_id == project_id, QualityPolicyModel.active == True).all())
        if not rules:
            return None
        return QualityPolicy(
            id="custom", project_id=project_id,
            rules=[PolicyRule(r.dimension, r.threshold, r.blocking) for r in rules],
        )

    def get_validation_summary(self, project_id: str) -> Optional[dict]:
        req_ids = [r.id for r in self._s.query(RequirementModel.id).filter(RequirementModel.project_id == project_id).all()]
        if not req_ids:
            return None
        total = (self._s.query(func.count(ValidationIssueModel.id))
                 .join(ValidationReportModel)
                 .filter(ValidationReportModel.requirement_id.in_(req_ids)).scalar()) or 0
        critical = (self._s.query(func.count(ValidationIssueModel.id))
                    .join(ValidationReportModel)
                    .filter(ValidationReportModel.requirement_id.in_(req_ids),
                            ValidationIssueModel.severity == "CRITICAL").scalar()) or 0
        return {"total": total, "critical": critical}

    def get_traceability_summary(self, project_id: str) -> Optional[dict]:
        linked = (self._s.query(func.count(func.distinct(TraceabilityLinkModel.source_id)))
                  .filter(TraceabilityLinkModel.project_id == project_id,
                          TraceabilityLinkModel.source_type == "REQUIREMENT",
                          TraceabilityLinkModel.active == True).scalar()) or 0
        return {"linked_reqs": linked}

    def get_coverage_score(self, project_id: str) -> Optional[float]:
        suite = (self._s.query(TestSuiteModel).filter(TestSuiteModel.project_id == project_id)
                 .order_by(TestSuiteModel.generated_at.desc()).first())
        if not suite:
            return None
        total = (self._s.query(func.count(RequirementModel.id))
                 .filter(RequirementModel.project_id == project_id).scalar()) or 1
        covered = (self._s.query(func.count(func.distinct(TestScenarioModel.requirement_id)))
                   .filter(TestScenarioModel.suite_id == suite.id).scalar()) or 0
        return round(covered / total * 100.0, 2)

    def get_accessibility_summary(self, project_id: str) -> Optional[dict]:
        report = (self._s.query(AccessibilityReportModel)
                  .filter(AccessibilityReportModel.project_id == project_id)
                  .order_by(AccessibilityReportModel.generated_at.desc()).first())
        if not report:
            return None
        issue_count = (self._s.query(func.count(WCAGIssueModel.id))
                       .filter(WCAGIssueModel.report_id == report.id, WCAGIssueModel.resolved == False).scalar()) or 0
        return {"level": report.conformance_level_achieved, "issue_count": issue_count}

    def _to_domain(self, m: QualityReportModel) -> QualityReport:
        return QualityReport(
            id=m.id, project_id=m.project_id, overall_status=GateStatus(m.overall_status),
            dimension_scores=[QualityDimensionScore(dimension=d.dimension, score=d.score,
                                                     status=GateStatus(d.status), evidence=d.evidence or "")
                               for d in m.dimension_scores],
            policy_violations=[], previous_report_id=m.previous_report_id,
            generated_at=m.generated_at, integrity_hash=m.integrity_hash,
        )
