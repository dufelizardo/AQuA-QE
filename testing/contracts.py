from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Sequence, Optional
from requirements.contracts.requirement_snapshot import RequirementSnapshot
from requirements.contracts.events import DomainEvent


class TestType(Enum):
    FUNCTIONAL    = "FUNCTIONAL"
    NEGATIVE      = "NEGATIVE"
    EXCEPTION     = "EXCEPTION"
    ACCESSIBILITY = "ACCESSIBILITY"
    INTEGRATION   = "INTEGRATION"
    UNIT          = "UNIT"


class TestTechnique(Enum):
    EQUIVALENCE        = "EQUIVALENCE"
    BOUNDARY_VALUE     = "BOUNDARY_VALUE"
    DECISION_TABLE     = "DECISION_TABLE"
    STATE_TRANSITION   = "STATE_TRANSITION"
    STATEMENT_COVERAGE = "STATEMENT_COVERAGE"
    BRANCH_COVERAGE    = "BRANCH_COVERAGE"


@dataclass(frozen=True)
class GherkinScript:
    feature:  str
    scenario: str
    given:    str
    when:     str
    then:     str
    tags:     Sequence[str] = field(default_factory=tuple)

    def render(self) -> str:
        tag_line = " ".join(f"@{t}" for t in self.tags)
        return (
            f"{tag_line}\n" if tag_line else ""
        ) + (
            f"Feature: {self.feature}\n\n"
            f"  Scenario: {self.scenario}\n"
            f"    Given {self.given}\n"
            f"    When {self.when}\n"
            f"    Then {self.then}\n"
        )


@dataclass(frozen=True)
class TestScenarioDTO:
    id:                     str
    requirement_id:         str
    acceptance_criteria_id: str
    title:                  str
    test_type:              TestType
    technique:              TestTechnique
    gherkin:                GherkinScript
    automation_candidate:   bool
    automation_strategy:    Optional[str]


@dataclass(frozen=True)
class TestSuiteDTO:
    suite_id:     str
    project_id:   str
    scenarios:    Sequence[TestScenarioDTO]
    generated_at: datetime

    def coverage_by_requirement(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for s in self.scenarios:
            counts[s.requirement_id] = counts.get(s.requirement_id, 0) + 1
        return counts

    def has_negative_for(self, requirement_id: str) -> bool:
        return any(
            s.requirement_id == requirement_id and s.test_type == TestType.NEGATIVE
            for s in self.scenarios
        )


@dataclass(frozen=True)
class TestSuiteGenerated(DomainEvent):
    suite:      TestSuiteDTO = None
    project_id: str = ""


@dataclass(frozen=True)
class CoverageGapDetected(DomainEvent):
    project_id:      str = ""
    requirement_id:  str = ""
    gap_description: str = ""


@dataclass(frozen=True)
class AutomationCandidateIdentified(DomainEvent):
    scenario_id:         str = ""
    strategy:            str = ""
    suggested_framework: str = ""
