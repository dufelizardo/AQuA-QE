from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Sequence
from requirements.contracts.requirement_snapshot import RequirementSnapshot
from requirements.contracts.events import DomainEvent


class ConformanceLevel(Enum):
    A   = "A"
    AA  = "AA"
    AAA = "AAA"


@dataclass(frozen=True)
class WCAGCriterion:
    code:        str
    level:       ConformanceLevel
    description: str
    guideline:   str


@dataclass(frozen=True)
class WCAGIssueDTO:
    criterion:      WCAGCriterion
    description:    str
    recommendation: str
    requirement_id: str
    resolved:       bool = False


@dataclass(frozen=True)
class HeuristicIssueDTO:
    heuristic_number: int
    heuristic_name:   str
    description:      str
    recommendation:   str
    requirement_id:   str


@dataclass(frozen=True)
class AccessibilityReportDTO:
    report_id:                  str
    project_id:                 str
    wcag_issues:                Sequence[WCAGIssueDTO]
    heuristic_issues:           Sequence[HeuristicIssueDTO]
    conformance_level_achieved: ConformanceLevel
    generated_at:               datetime

    def blocks_aa_conformance(self) -> bool:
        return any(i.criterion.level == ConformanceLevel.A and not i.resolved for i in self.wcag_issues)


class IAccessibilityAnalysisService(ABC):
    @abstractmethod
    def analyze(self, snapshots: Sequence[RequirementSnapshot],
                target_level: ConformanceLevel = ConformanceLevel.AA) -> AccessibilityReportDTO: ...

    @abstractmethod
    def get_report(self, report_id: str) -> AccessibilityReportDTO: ...


@dataclass(frozen=True)
class AccessibilityReportGenerated(DomainEvent):
    report:     AccessibilityReportDTO = None
    project_id: str = ""


@dataclass(frozen=True)
class WCAGViolationDetected(DomainEvent):
    requirement_id: str = ""
    issue:          WCAGIssueDTO = None


@dataclass(frozen=True)
class ConformanceLevelAchieved(DomainEvent):
    project_id: str = ""
    level:      ConformanceLevel = None
