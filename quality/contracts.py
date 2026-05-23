from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Sequence, Optional
from requirements.contracts.events import DomainEvent


class GateStatus(Enum):
    PASSED  = "PASSED"
    FAILED  = "FAILED"
    WARNING = "WARNING"


@dataclass(frozen=True)
class PolicyRule:
    dimension: str
    threshold: float
    blocking:  bool

    def __post_init__(self) -> None:
        if not (0.0 <= self.threshold <= 100.0):
            raise ValueError("PolicyRule.threshold deve estar entre 0 e 100")


@dataclass(frozen=True)
class QualityDimensionScore:
    dimension: str
    score:     float
    status:    GateStatus
    evidence:  str


@dataclass(frozen=True)
class QualityReportDTO:
    report_id:          str
    project_id:         str
    overall_status:     GateStatus
    dimension_scores:   Sequence[QualityDimensionScore]
    policy_violations:  Sequence[str]
    previous_report_id: Optional[str]
    generated_at:       datetime
    integrity_hash:     str

    def is_approved(self) -> bool:
        return self.overall_status == GateStatus.PASSED

    def score_for(self, dimension: str) -> Optional[float]:
        for d in self.dimension_scores:
            if d.dimension == dimension:
                return d.score
        return None


class IQualityGateService(ABC):
    @abstractmethod
    def evaluate(self, project_id: str) -> QualityReportDTO: ...

    @abstractmethod
    def get_report(self, report_id: str) -> QualityReportDTO: ...

    @abstractmethod
    def get_latest_report(self, project_id: str) -> Optional[QualityReportDTO]: ...


@dataclass(frozen=True)
class QualityGatePassed(DomainEvent):
    report:     QualityReportDTO = None
    project_id: str = ""


@dataclass(frozen=True)
class QualityGateFailed(DomainEvent):
    report:              QualityReportDTO = None
    project_id:          str = ""
    blocking_violations: Sequence[str] = field(default_factory=tuple)


@dataclass(frozen=True)
class PolicyViolationDetected(DomainEvent):
    project_id:   str = ""
    rule:         PolicyRule = None
    actual_score: float = 0.0
