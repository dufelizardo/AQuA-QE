from __future__ import annotations
from knowledge.contracts import IKnowledgeService, KnowledgeContribution, PatternType
from requirements.contracts.requirement_snapshot import RequirementSnapshot


class KnowledgeACL:
    def __init__(self, service: IKnowledgeService) -> None:
        self._svc = service

    def learn_from_requirement(self, snapshot: RequirementSnapshot, domain: str) -> None:
        self._svc.contribute(KnowledgeContribution(
            source_context="requirement_engineering", pattern_type=PatternType.REQUIREMENT,
            domain=domain, content=f"{snapshot.title}\n{snapshot.description}",
            confidence=round(snapshot.quality_score.overall / 100.0, 3), source_id=snapshot.id,
        ))

    def learn_from_test_scenario(self, scenario, domain: str) -> None:
        self._svc.contribute(KnowledgeContribution(
            source_context="test_intelligence", pattern_type=PatternType.TEST_SCENARIO,
            domain=domain, content=scenario.gherkin.render(),
            confidence=0.8 if scenario.automation_candidate else 0.5, source_id=scenario.id,
        ))

    def suggest_for_elicitation(self, domain: str, raw_input: str) -> list:
        from knowledge.contracts import KnowledgeQuery
        return list(self._svc.query(KnowledgeQuery(domain=domain, semantic_text=raw_input, limit=5)))
