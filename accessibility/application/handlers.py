from __future__ import annotations
import logging
from accessibility.application.analyze import AnalyzeAccessibilityUseCase, AnalyzeAccessibilityCommand
from accessibility.domain.services import AccessibilityService
from requirements.contracts.i_requirement_reader import IRequirementReader
from shared.event_bus import IEventBus

logger = logging.getLogger(__name__)


def make_accessibility_handler(service: AccessibilityService, reader: IRequirementReader, bus: IEventBus):
    use_case = AnalyzeAccessibilityUseCase(service, reader, bus)

    def on_requirement_approved(event) -> None:
        logger.info(f"[Accessibility] Analisando projeto {event.project_id}")
        try:
            use_case.execute(AnalyzeAccessibilityCommand(project_id=event.project_id))
        except Exception as exc:
            logger.error(f"[Accessibility] Falha para {event.project_id}: {exc}", exc_info=True)

    return on_requirement_approved
