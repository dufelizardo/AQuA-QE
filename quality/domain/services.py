from __future__ import annotations
import uuid, logging
from typing import Optional
from quality.contracts import IQualityGateService, GateStatus, PolicyRule, QualityDimensionScore, QualityReportDTO
from quality.domain.entities import QualityReport, QualityPolicy
from quality.domain.scorer import QualityScorer, QualityInputs
from requirements.contracts.i_requirement_reader import IRequirementReader

logger = logging.getLogger(__name__)

DEFAULT_RULES: list[PolicyRule] = [
    PolicyRule("clarity",       60.0, True),
    PolicyRule("completeness",  70.0, True),
    PolicyRule("consistency",   60.0, False),
    PolicyRule("traceability",  80.0, False),
    PolicyRule("coverage",      70.0, True),
    PolicyRule("testability",   60.0, False),
    PolicyRule("accessibility", 50.0, False),
]


class QualityGateService(IQualityGateService):
    def __init__(self, repo, reader: IRequirementReader) -> None:
        self._repo   = repo
        self._reader = reader
        self._scorer = QualityScorer()

    def evaluate(self, project_id: str) -> QualityReportDTO:
        inputs = self._collect_inputs(project_id)
        scores = self._scorer.compute_all(inputs)
        policy = self._repo.get_policy(project_id) or QualityPolicy("default", project_id, DEFAULT_RULES)

        dim_scores, violations, has_blocking_fail = [], [], False
        for dimension, score in scores.items():
            status = policy.evaluate_dimension(dimension, score)
            rule   = next((r for r in policy.rules if r.dimension == dimension), None)
            evidence = self._evidence(dimension, inputs, score, rule)
            dim_scores.append(QualityDimensionScore(dimension=dimension, score=score, status=status, evidence=evidence))
            if status == GateStatus.FAILED:
                threshold = rule.threshold if rule else 0.0
                violations.append(f"{dimension}: {score:.1f} < {threshold:.1f}{' [BLOQUEANTE]' if rule and rule.blocking else ''}")
                if rule and rule.blocking:
                    has_blocking_fail = True

        overall = GateStatus.FAILED if has_blocking_fail else (GateStatus.WARNING if violations else GateStatus.PASSED)
        latest  = self._repo.get_latest_report(project_id)
        report  = QualityReport(
            id=str(uuid.uuid4()), project_id=project_id, overall_status=overall,
            dimension_scores=dim_scores, policy_violations=violations,
            previous_report_id=latest.report_id if latest else None,
        )
        self._repo.save_report(report)
        logger.info(f"[Quality] Gate {project_id}: {overall.value} — {len(violations)} violação(ões)")
        return report.to_dto()

    def get_report(self, report_id: str) -> QualityReportDTO:
        r = self._repo.get_report(report_id)
        if not r:
            raise ValueError(f"Relatório {report_id} não encontrado")
        return r.to_dto()

    def get_latest_report(self, project_id: str) -> Optional[QualityReportDTO]:
        r = self._repo.get_latest_report(project_id)
        return r.to_dto() if r else None

    def _collect_inputs(self, project_id: str) -> QualityInputs:
        snapshots = list(self._reader.get_project_snapshots(project_id, approved_only=False))
        inputs = QualityInputs(project_id=project_id, total_reqs=len(snapshots))
        if snapshots:
            inputs.avg_clarity      = sum(s.quality_score.clarity      for s in snapshots) / len(snapshots)
            inputs.avg_completeness = sum(s.quality_score.completeness for s in snapshots) / len(snapshots)
            inputs.avg_testability  = sum(s.quality_score.testability  for s in snapshots) / len(snapshots)
            inputs.avg_consistency  = sum(s.quality_score.consistency  for s in snapshots) / len(snapshots)
        val_summary = self._repo.get_validation_summary(project_id)
        if val_summary:
            inputs.critical_issues = val_summary.get("critical", 0)
            inputs.total_issues    = val_summary.get("total", 0)
        trc_summary = self._repo.get_traceability_summary(project_id)
        if trc_summary:
            inputs.linked_reqs = trc_summary.get("linked_reqs", 0)
        cov = self._repo.get_coverage_score(project_id)
        if cov is not None:
            inputs.coverage_score = cov
        acc = self._repo.get_accessibility_summary(project_id)
        if acc:
            inputs.wcag_level  = acc.get("level")
            inputs.wcag_issues = acc.get("issue_count", 0)
        return inputs

    def _evidence(self, dim: str, inp: QualityInputs, score: float, rule) -> str:
        threshold = f" (mínimo: {rule.threshold:.0f})" if rule else ""
        return {
            "clarity":       f"Média clareza: {inp.avg_clarity or 0:.1f}{threshold}",
            "completeness":  f"Completude: {inp.avg_completeness or 0:.1f} — issues críticas: {inp.critical_issues}{threshold}",
            "consistency":   f"Consistência: {inp.avg_consistency or 0:.1f}{threshold}",
            "traceability":  f"{inp.linked_reqs}/{inp.total_reqs} requisitos com links{threshold}",
            "coverage":      f"Cobertura: {inp.coverage_score or 0:.1f}%{threshold}",
            "testability":   f"Testabilidade: {inp.avg_testability or 0:.1f}{threshold}",
            "accessibility": f"WCAG: {inp.wcag_level or 'não avaliado'} — {inp.wcag_issues} issues{threshold}",
        }.get(dim, f"Score: {score:.1f}")
