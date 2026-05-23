from __future__ import annotations
import uuid, json, logging
from datetime import datetime
from typing import Sequence
from requirements.contracts.requirement_snapshot import RequirementSnapshot
from requirements.contracts.i_requirement_reader import IRequirementReader
from testing.contracts import GherkinScript, TestSuiteDTO
from testing.domain.entities import TestScenario, TestSuite
from testing.domain.techniques import ScenarioBlueprint, select_techniques
from ai_gateway.acl import AIGatewayACL

logger = logging.getLogger(__name__)


class TestGenerationService:
    def __init__(self, repo, reader: IRequirementReader, ai_acl: AIGatewayACL) -> None:
        self._repo   = repo
        self._reader = reader
        self._ai_acl = ai_acl

    def generate_suite(self, snapshots: Sequence[RequirementSnapshot]) -> TestSuiteDTO:
        if not snapshots:
            raise ValueError("Nenhum snapshot fornecido")
        suite = TestSuite(id=str(uuid.uuid4()), project_id=snapshots[0].project_id)
        for snap in snapshots:
            for bp in self._build_blueprints(snap):
                scenario = self._materialize(bp, snap)
                if scenario:
                    suite.add_scenario(scenario)
        self._repo.save_suite(suite)
        logger.info(f"Suite gerada: {suite.id} — {len(suite.scenarios)} cenários para {len(snapshots)} requisitos")
        return suite.to_dto()

    def generate_suite_for_project(self, project_id: str) -> TestSuiteDTO:
        snapshots = self._reader.get_project_snapshots(project_id, approved_only=True)
        if not snapshots:
            logger.warning(f"Nenhum requisito aprovado para projeto {project_id}")
            return TestSuiteDTO(suite_id=str(uuid.uuid4()), project_id=project_id,
                                scenarios=[], generated_at=datetime.utcnow())
        return self.generate_suite(list(snapshots))

    def get_suite(self, suite_id: str) -> TestSuiteDTO:
        suite = self._repo.get_suite(suite_id)
        if not suite:
            raise ValueError(f"Suite {suite_id} não encontrada")
        return suite.to_dto()

    def _build_blueprints(self, snap: RequirementSnapshot) -> list[ScenarioBlueprint]:
        blueprints = []
        for technique in select_techniques(snap):
            blueprints.extend(technique.generate_blueprints(snap))
        return blueprints

    def _materialize(self, bp: ScenarioBlueprint, snap: RequirementSnapshot) -> TestScenario | None:
        try:
            response = self._ai_acl.generate_test_scenarios(snap, context_id=bp.requirement_id)
            raw  = response.content.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
            data = json.loads(raw)
            items = data if isinstance(data, list) else [data]
            for item in items:
                gherkin = GherkinScript(
                    feature=item.get("feature", snap.title),
                    scenario=item.get("scenario", bp.title_hint),
                    given=item.get("given",""), when=item.get("when",""), then=item.get("then",""),
                    tags=tuple(item.get("tags",[])),
                )
                if not (gherkin.given and gherkin.when and gherkin.then):
                    logger.warning(f"GWT incompleto para {bp.requirement_id} — ignorado")
                    continue
                return TestScenario(
                    id=str(uuid.uuid4()), requirement_id=bp.requirement_id,
                    acceptance_criteria_id=bp.acceptance_criteria_id or None,
                    title=item.get("scenario", bp.title_hint),
                    test_type=bp.test_type, technique=bp.technique, gherkin=gherkin,
                    automation_candidate=bp.automation_candidate,
                    automation_strategy=item.get("automation_strategy"),
                )
        except Exception as exc:
            logger.error(f"Materialização falhou para {bp.requirement_id}: {exc}")
        return None
