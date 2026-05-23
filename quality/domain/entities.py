from __future__ import annotations
import hashlib, json
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from quality.contracts import GateStatus, PolicyRule, QualityDimensionScore, QualityReportDTO


@dataclass
class QualityPolicy:
    id:         str
    project_id: str
    rules:      List[PolicyRule] = field(default_factory=list)
    active:     bool = True

    def evaluate_dimension(self, dimension: str, score: float) -> GateStatus:
        rule = next((r for r in self.rules if r.dimension == dimension), None)
        if not rule:
            return GateStatus.PASSED
        if score >= rule.threshold:
            return GateStatus.PASSED
        return GateStatus.FAILED if rule.blocking else GateStatus.WARNING


@dataclass
class QualityReport:
    id:                 str
    project_id:         str
    overall_status:     GateStatus
    dimension_scores:   List[QualityDimensionScore]
    policy_violations:  List[str]
    previous_report_id: Optional[str] = None
    generated_at:       datetime = field(default_factory=datetime.utcnow)
    integrity_hash:     str = ""

    def __post_init__(self) -> None:
        if not self.integrity_hash:
            self.integrity_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        payload = json.dumps({
            "id": self.id, "project_id": self.project_id,
            "overall_status": self.overall_status.value,
            "scores": {d.dimension: d.score for d in self.dimension_scores},
        }, sort_keys=True)
        return hashlib.sha256(payload.encode()).hexdigest()

    def is_approved(self) -> bool:
        return self.overall_status == GateStatus.PASSED

    def to_dto(self) -> QualityReportDTO:
        return QualityReportDTO(
            report_id=self.id, project_id=self.project_id, overall_status=self.overall_status,
            dimension_scores=self.dimension_scores, policy_violations=self.policy_violations,
            previous_report_id=self.previous_report_id, generated_at=self.generated_at,
            integrity_hash=self.integrity_hash,
        )
