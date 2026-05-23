from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import List
from accessibility.contracts import WCAGCriterion, ConformanceLevel, WCAGIssueDTO, HeuristicIssueDTO, AccessibilityReportDTO


@dataclass
class WCAGIssue:
    id:             str
    criterion:      WCAGCriterion
    description:    str
    recommendation: str
    requirement_id: str
    resolved:       bool = False

    def is_level_a(self) -> bool:
        return self.criterion.level == ConformanceLevel.A

    def to_dto(self) -> WCAGIssueDTO:
        return WCAGIssueDTO(
            criterion=self.criterion, description=self.description,
            recommendation=self.recommendation, requirement_id=self.requirement_id, resolved=self.resolved,
        )


@dataclass
class HeuristicIssue:
    id:               str
    heuristic_number: int
    heuristic_name:   str
    description:      str
    recommendation:   str
    requirement_id:   str

    def to_dto(self) -> HeuristicIssueDTO:
        return HeuristicIssueDTO(
            heuristic_number=self.heuristic_number, heuristic_name=self.heuristic_name,
            description=self.description, recommendation=self.recommendation, requirement_id=self.requirement_id,
        )


@dataclass
class AccessibilityReport:
    id:               str
    project_id:       str
    wcag_issues:      List[WCAGIssue]      = field(default_factory=list)
    heuristic_issues: List[HeuristicIssue] = field(default_factory=list)
    generated_at:     datetime = field(default_factory=datetime.utcnow)

    def conformance_level_achieved(self) -> ConformanceLevel:
        if any(i.is_level_a() and not i.resolved for i in self.wcag_issues):
            return ConformanceLevel.A
        unresolved_aa = [i for i in self.wcag_issues if i.criterion.level == ConformanceLevel.AA and not i.resolved]
        if unresolved_aa:
            return ConformanceLevel.A
        return ConformanceLevel.AA

    def to_dto(self) -> AccessibilityReportDTO:
        return AccessibilityReportDTO(
            report_id=self.id, project_id=self.project_id,
            wcag_issues=[i.to_dto() for i in self.wcag_issues],
            heuristic_issues=[i.to_dto() for i in self.heuristic_issues],
            conformance_level_achieved=self.conformance_level_achieved(),
            generated_at=self.generated_at,
        )
