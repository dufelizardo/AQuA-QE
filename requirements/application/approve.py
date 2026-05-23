from __future__ import annotations
from dataclasses import dataclass
import logging
from requirements.contracts.events import RequirementApproved
from requirements.infrastructure.repository import RequirementRepository
from requirements.infrastructure.mappers import RequirementMapper
from shared.event_bus import IEventBus

logger = logging.getLogger(__name__)


@dataclass
class ApproveRequirementCommand:
    requirement_id: str
    approved_by: str


class ApproveRequirementUseCase:
    def __init__(self, repo: RequirementRepository, bus: IEventBus) -> None:
        self._repo = repo
        self._bus = bus

    def execute(self, cmd: ApproveRequirementCommand) -> None:
        req = self._repo.get_requirement(cmd.requirement_id)
        if not req:
            raise ValueError(f"Requisito {cmd.requirement_id} não encontrado")
        req.approve(cmd.approved_by)
        self._repo.save_requirement(req)
        self._bus.publish(RequirementApproved(
            requirement_id=req.id, project_id=req.project_id, approved_by=cmd.approved_by,
        ))
        logger.info(f"Requisito aprovado: {req.id} por '{cmd.approved_by}' (quality: {req.quality_score.overall:.1f})")


class BulkApproveUseCase:
    def __init__(self, repo: RequirementRepository, bus: IEventBus) -> None:
        self._approve = ApproveRequirementUseCase(repo, bus)
        self._repo = repo

    def execute(self, project_id: str, approved_by: str) -> dict:
        from requirements.domain.value_objects import RequirementStatus
        candidates = self._repo.list_by_project(project_id, RequirementStatus.REVIEW)
        approved, failed = [], []
        for req in candidates:
            try:
                self._approve.execute(ApproveRequirementCommand(req.id, approved_by))
                approved.append(req.id)
            except ValueError as exc:
                failed.append({"id": req.id, "reason": str(exc)})
        return {"approved": approved, "failed": failed}
