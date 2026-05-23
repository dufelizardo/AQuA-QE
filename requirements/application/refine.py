from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import json, logging
from requirements.domain.value_objects import Priority, QualityScore
from requirements.contracts.events import RequirementRefined
from requirements.infrastructure.repository import RequirementRepository
from requirements.infrastructure.mappers import RequirementMapper
from ai_gateway.acl import AIGatewayACL
from shared.event_bus import IEventBus

logger = logging.getLogger(__name__)


@dataclass
class RefineRequirementCommand:
    requirement_id: str
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    changelog: str = ""
    ai_assisted: bool = False


class RefineRequirementUseCase:
    def __init__(self, repo: RequirementRepository, ai_acl: AIGatewayACL, bus: IEventBus) -> None:
        self._repo = repo
        self._ai_acl = ai_acl
        self._bus = bus

    def execute(self, cmd: RefineRequirementCommand) -> None:
        req = self._repo.get_requirement(cmd.requirement_id)
        if not req:
            raise ValueError(f"Requisito {cmd.requirement_id} não encontrado")

        previous_version = str(req.version)
        title, description, new_score = cmd.title, cmd.description, None

        if cmd.ai_assisted:
            title, description, new_score = self._ai_refine(req, cmd)

        priority = Priority(cmd.priority) if cmd.priority else None
        req.refine(title=title, description=description, priority=priority, changelog=cmd.changelog or "Refinamento")
        if new_score:
            req.update_quality(new_score)

        self._repo.save_requirement(req)
        self._bus.publish(RequirementRefined(
            snapshot=RequirementMapper.to_snapshot(req),
            previous_version=previous_version, change_reason=cmd.changelog,
        ))
        logger.info(f"Requisito refinado: {req.id} {previous_version} → {str(req.version)}")

    def _ai_refine(self, req, cmd):
        snapshot = RequirementMapper.to_snapshot(req)
        response = self._ai_acl.validate_requirement(snapshot, context_id=req.id)
        try:
            clean = response.content.strip().lstrip("```json").rstrip("```").strip()
            data = json.loads(clean)
            scores = data.get("improved_scores", {})
            new_score = QualityScore(
                clarity=float(scores.get("clarity", req.quality_score.clarity)),
                completeness=float(scores.get("completeness", req.quality_score.completeness)),
                testability=float(scores.get("testability", req.quality_score.testability)),
                consistency=float(scores.get("consistency", req.quality_score.consistency)),
            ) if scores else None
            return data.get("improved_title") or cmd.title, data.get("improved_description") or cmd.description, new_score
        except Exception:
            return cmd.title, cmd.description, None
