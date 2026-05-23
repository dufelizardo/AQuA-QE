from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from testing.contracts import TestType, TestTechnique, GherkinScript, TestScenarioDTO, TestSuiteDTO


@dataclass
class TestScenario:
    id:                     str
    requirement_id:         str
    acceptance_criteria_id: Optional[str]
    title:                  str
    test_type:              TestType
    technique:              TestTechnique
    gherkin:                GherkinScript
    automation_candidate:   bool = False
    automation_strategy:    Optional[str] = None
    status:                 str = "DRAFT"
    created_at:             datetime = field(default_factory=datetime.utcnow)

    def is_negative(self) -> bool:
        return self.test_type == TestType.NEGATIVE

    def to_dto(self) -> TestScenarioDTO:
        return TestScenarioDTO(
            id=self.id, requirement_id=self.requirement_id,
            acceptance_criteria_id=self.acceptance_criteria_id or "",
            title=self.title, test_type=self.test_type, technique=self.technique,
            gherkin=self.gherkin, automation_candidate=self.automation_candidate,
            automation_strategy=self.automation_strategy,
        )


@dataclass
class TestSuite:
    id:           str
    project_id:   str
    scenarios:    List[TestScenario] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.utcnow)

    def add_scenario(self, scenario: TestScenario) -> None:
        self.scenarios.append(scenario)

    def has_negative_for(self, requirement_id: str) -> bool:
        return any(s.requirement_id == requirement_id and s.is_negative() for s in self.scenarios)

    def automation_candidates(self) -> List[TestScenario]:
        return [s for s in self.scenarios if s.automation_candidate]

    def to_dto(self) -> TestSuiteDTO:
        return TestSuiteDTO(
            suite_id=self.id, project_id=self.project_id,
            scenarios=[s.to_dto() for s in self.scenarios],
            generated_at=self.generated_at,
        )
