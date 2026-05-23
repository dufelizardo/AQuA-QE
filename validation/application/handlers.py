from __future__ import annotations
import logging
from requirements.contracts.events import RequirementCreated, RequirementRefined
from validation.application.validate import ValidateRequirementUseCase, ValidateRequirementCommand
from validation.domain.services import ValidationService
from shared.event_bus import IEventBus

logger = logging.getLogger(__name__)


def make_validation_handler(service: ValidationService, bus: IEventBus):
    use_case = ValidateRequirementUseCase(service, bus)

    def on_requirement_created_or_refined(event) -> None:
        snapshot = event.snapshot
        logger.info(f"[Validation] Validando {snapshot.id} ({type(event).__name__})")
        try:
            use_case.execute(ValidateRequirementCommand(snapshot=snapshot))
        except Exception as exc:
            logger.error(f"[Validation] Falha ao validar {snapshot.id}: {exc}", exc_info=True)

    return on_requirement_created_or_refined
