from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class QualityInputs:
    project_id:       str
    avg_clarity:      Optional[float] = None
    avg_completeness: Optional[float] = None
    avg_testability:  Optional[float] = None
    avg_consistency:  Optional[float] = None
    critical_issues:  int = 0
    total_issues:     int = 0
    total_reqs:       int = 0
    linked_reqs:      int = 0
    coverage_score:   Optional[float] = None
    wcag_level:       Optional[str] = None
    wcag_issues:      int = 0


class QualityScorer:
    def compute_clarity(self, inputs: QualityInputs) -> float:
        if inputs.avg_clarity is None:
            return 0.0
        return max(0.0, round(inputs.avg_clarity - min(inputs.total_issues * 2.0, 20.0), 2))

    def compute_completeness(self, inputs: QualityInputs) -> float:
        if inputs.avg_completeness is None:
            return 0.0
        return max(0.0, round(inputs.avg_completeness - min(inputs.critical_issues * 5.0, 30.0), 2))

    def compute_consistency(self, inputs: QualityInputs) -> float:
        return round(inputs.avg_consistency or 0.0, 2)

    def compute_traceability(self, inputs: QualityInputs) -> float:
        if not inputs.total_reqs:
            return 0.0
        return round(min(inputs.linked_reqs / inputs.total_reqs * 100.0, 100.0), 2)

    def compute_coverage(self, inputs: QualityInputs) -> float:
        return round(inputs.coverage_score or 0.0, 2)

    def compute_testability(self, inputs: QualityInputs) -> float:
        return round(inputs.avg_testability or 0.0, 2)

    def compute_accessibility(self, inputs: QualityInputs) -> float:
        base = {"AAA": 100.0, "AA": 85.0, "A": 50.0}.get(inputs.wcag_level or "", 0.0)
        return max(0.0, round(base - min(inputs.wcag_issues * 3.0, 30.0), 2))

    def compute_all(self, inputs: QualityInputs) -> dict[str, float]:
        return {
            "clarity":       self.compute_clarity(inputs),
            "completeness":  self.compute_completeness(inputs),
            "consistency":   self.compute_consistency(inputs),
            "traceability":  self.compute_traceability(inputs),
            "coverage":      self.compute_coverage(inputs),
            "testability":   self.compute_testability(inputs),
            "accessibility": self.compute_accessibility(inputs),
        }
