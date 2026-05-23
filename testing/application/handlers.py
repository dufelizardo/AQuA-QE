from __future__ import annotations
import logging
from testing.application.generate import GenerateTestSuiteUseCase, GenerateTestSuiteCommand
from testing.domain.services import TestGenerationService
from requirements.contracts.i_requirement_reader import IRequirementReader
from shared.event_bus import IEventBus

logger = logging.getLogger(__name__)


def make_testing_handler(service: TestGenerationService, reader: IRequirementReader, bus: IEventBus):
    use_case = GenerateTestSuiteUseCase(service, bus)

    def on_requirement_approved(event) -> None:
        logger.info(f"[Testing] RequirementApproved → gerando suite para {event.project_id}")
        try:
            use_case.execute(GenerateTestSuiteCommand(project_id=event.project_id))
        except Exception as exc:
            logger.error(f"[Testing] Falha para {event.project_id}: {exc}", exc_info=True)

    return on_requirement_approved
