from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional
import uuid, json, logging
from requirements.domain.entities import Requirement, AcceptanceCriteria, ElicitationSession, Project
from requirements.domain.value_objects import RequirementType, Priority, RequirementStatus, QualityScore, RequirementVersion
from requirements.contracts.events import RequirementCreated, ElicitationSessionStarted
from requirements.infrastructure.repository import RequirementRepository
from requirements.infrastructure.mappers import RequirementMapper
from ai_gateway.acl import AIGatewayACL
from shared.event_bus import IEventBus

logger = logging.getLogger(__name__)


@dataclass
class CreateRequirementCommand:
    project_id: str
    raw_input: str
    input_type: str = "TEXT"
    language: str = "pt"
    session_id: Optional[str] = None


@dataclass
class CreateRequirementResult:
    requirements: List[Requirement]
    session_id: str
    gaps_detected: List[str]


class CreateRequirementUseCase:
    def __init__(self, repo: RequirementRepository, ai_acl: AIGatewayACL, bus: IEventBus) -> None:
        self._repo = repo
        self._ai_acl = ai_acl
        self._bus = bus

    def execute(self, cmd: CreateRequirementCommand) -> CreateRequirementResult:
        if not self._repo.project_exists(cmd.project_id):
            raise ValueError(f"Projeto {cmd.project_id} não encontrado")

        session_id = cmd.session_id or str(uuid.uuid4())
        session = ElicitationSession(
            id=session_id, project_id=cmd.project_id,
            input_type=cmd.input_type, raw_input=cmd.raw_input, language=cmd.language,
        )
        self._repo.save_session(session)
        self._bus.publish(ElicitationSessionStarted(session_id=session_id, project_id=cmd.project_id))

        response = self._ai_acl.extract_requirements(raw_input=cmd.raw_input, context_id=session_id)
        extracted = self._parse_extraction(response.content)

        requirements = []
        gaps = extracted.get("gaps", [])

        for item in extracted.get("requirements", []):
            req = self._build_requirement(item, cmd.project_id, session_id)
            self._repo.save_requirement(req)
            snapshot = RequirementMapper.to_snapshot(req)
            self._bus.publish(RequirementCreated(snapshot=snapshot, session_id=session_id))
            requirements.append(req)
            logger.info(f"Requisito criado: {req.id} [{req.req_type.value}] '{req.title}'")

        return CreateRequirementResult(requirements=requirements, session_id=session_id, gaps_detected=gaps)

    def _parse_extraction(self, content: str) -> dict:
        try:
            clean = content.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
            return json.loads(clean)
        except json.JSONDecodeError as exc:
            logger.error(f"Falha ao parsear resposta do LLM: {exc}")
            return {"requirements": [], "gaps": []}

    def _build_requirement(self, item: dict, project_id: str, session_id: str) -> Requirement:
        acs = []
        for ac_data in item.get("acceptance_criteria", []):
            acs.append(AcceptanceCriteria(
                id=str(uuid.uuid4()), description=ac_data.get("description", ""),
                given=ac_data.get("given", ""), when=ac_data.get("when", ""), then=ac_data.get("then", ""),
            ))
        scores = item.get("scores", {})
        return Requirement(
            id=str(uuid.uuid4()), project_id=project_id, session_id=session_id,
            title=item.get("title", "Sem título"), description=item.get("description", ""),
            req_type=RequirementType(item.get("type", "RF")),
            priority=Priority(item.get("priority", "SHOULD")),
            status=RequirementStatus.DRAFT,
            version=RequirementVersion(1, 0, "Criação inicial"),
            quality_score=QualityScore(
                clarity=float(scores.get("clarity", 0.0)),
                completeness=float(scores.get("completeness", 0.0)),
                testability=float(scores.get("testability", 0.0)),
                consistency=float(scores.get("consistency", 0.0)),
            ),
            acceptance_criteria=acs,
        )
