from __future__ import annotations
import logging
from quality.application.evaluate import EvaluateQualityGateUseCase, EvaluateQualityGateCommand
from quality.domain.services import QualityGateService
from shared.event_bus import IEventBus

logger = logging.getLogger(__name__)


def make_quality_handlers(service: QualityGateService, bus: IEventBus):
    uc = EvaluateQualityGateUseCase(service, bus)

    def _evaluate(project_id: str, source: str) -> None:
        logger.info(f"[Quality] Reavaliando gate para {project_id} (trigger: {source})")
        try:
            uc.execute(EvaluateQualityGateCommand(project_id=project_id))
        except Exception as exc:
            logger.error(f"[Quality] Gate falhou para {project_id}: {exc}", exc_info=True)

    def on_validation_completed(event) -> None:
        pass  # project_id resolvido via req_reader no wiring — placeholder

    def on_test_suite_generated(event) -> None:
        _evaluate(event.project_id, "TestSuiteGenerated")

    def on_accessibility_report_generated(event) -> None:
        _evaluate(event.project_id, "AccessibilityReportGenerated")

    def on_coverage_gap(event) -> None:
        _evaluate(event.project_id, "CoverageGapDetected")

    return on_validation_completed, on_test_suite_generated, on_accessibility_report_generated, on_coverage_gap
