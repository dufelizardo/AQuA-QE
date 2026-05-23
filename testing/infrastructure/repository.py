from __future__ import annotations
import json
from typing import Optional
from sqlalchemy.orm import Session
from testing.infrastructure.models import TestSuiteModel, TestScenarioModel
from testing.domain.entities import TestSuite, TestScenario
from testing.contracts import TestType, TestTechnique, GherkinScript


class TestRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def save_suite(self, suite: TestSuite) -> None:
        self._s.add(TestSuiteModel(id=suite.id, project_id=suite.project_id, generated_at=suite.generated_at))
        for s in suite.scenarios:
            self._s.add(TestScenarioModel(
                id=s.id, suite_id=suite.id, requirement_id=s.requirement_id,
                acceptance_criteria_id=s.acceptance_criteria_id,
                title=s.title, test_type=s.test_type.value, technique=s.technique.value,
                gherkin_feature=s.gherkin.feature, gherkin_scenario=s.gherkin.scenario,
                gherkin_given=s.gherkin.given, gherkin_when=s.gherkin.when, gherkin_then=s.gherkin.then,
                gherkin_tags=json.dumps(list(s.gherkin.tags)),
                automation_candidate=s.automation_candidate, automation_strategy=s.automation_strategy,
                status=s.status, created_at=s.created_at,
            ))
        self._s.flush()

    def get_suite(self, suite_id: str) -> Optional[TestSuite]:
        m = self._s.get(TestSuiteModel, suite_id)
        if not m:
            return None
        suite = TestSuite(id=m.id, project_id=m.project_id, generated_at=m.generated_at)
        for s in m.scenarios:
            suite.add_scenario(TestScenario(
                id=s.id, requirement_id=s.requirement_id, acceptance_criteria_id=s.acceptance_criteria_id,
                title=s.title, test_type=TestType(s.test_type), technique=TestTechnique(s.technique),
                gherkin=GherkinScript(
                    feature=s.gherkin_feature, scenario=s.gherkin_scenario,
                    given=s.gherkin_given, when=s.gherkin_when, then=s.gherkin_then,
                    tags=tuple(json.loads(s.gherkin_tags or "[]")),
                ),
                automation_candidate=s.automation_candidate, automation_strategy=s.automation_strategy,
                status=s.status, created_at=s.created_at,
            ))
        return suite

    def latest_suite_for_project(self, project_id: str) -> Optional[TestSuite]:
        m = (self._s.query(TestSuiteModel)
             .filter(TestSuiteModel.project_id == project_id)
             .order_by(TestSuiteModel.generated_at.desc()).first())
        return self.get_suite(m.id) if m else None
