from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Sequence
import hashlib, json
from requirements.domain.value_objects import RequirementType, Priority, QualityScore, RequirementVersion


@dataclass(frozen=True)
class AcceptanceCriteriaSnapshot:
    id: str
    description: str
    given: str
    when: str
    then: str


@dataclass(frozen=True)
class RequirementSnapshot:
    id: str
    project_id: str
    title: str
    description: str
    req_type: RequirementType
    priority: Priority
    version: RequirementVersion
    quality_score: QualityScore
    acceptance_criteria: Sequence[AcceptanceCriteriaSnapshot]
    business_rule_ids: Sequence[str]
    snapshotted_at: datetime
    schema_version: str = "1.0"

    def is_critical(self) -> bool:
        return self.priority == Priority.MUST

    def has_acceptance_criteria(self) -> bool:
        return len(self.acceptance_criteria) > 0

    def fingerprint(self) -> str:
        payload = json.dumps({
            "id": self.id,
            "version": str(self.version),
            "schema_version": self.schema_version,
        }, sort_keys=True)
        return hashlib.sha256(payload.encode()).hexdigest()[:16]
