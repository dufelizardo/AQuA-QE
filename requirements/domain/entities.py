from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from .value_objects import (
    RequirementType, Priority, RequirementStatus,
    QualityScore, RequirementVersion,
)


@dataclass
class AcceptanceCriteria:
    id: str
    description: str
    given: str
    when: str
    then: str
    status: str = "DRAFT"


@dataclass
class BusinessRule:
    id: str
    project_id: str
    code: str
    description: str
    condition: Optional[str] = None
    action: Optional[str] = None
    status: str = "ACTIVE"


@dataclass
class Requirement:
    id: str
    project_id: str
    session_id: Optional[str]
    title: str
    description: str
    req_type: RequirementType
    priority: Priority
    version: RequirementVersion
    quality_score: QualityScore
    status: RequirementStatus
    acceptance_criteria: List[AcceptanceCriteria] = field(default_factory=list)
    business_rule_ids: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def refine(
        self,
        title: Optional[str] = None,
        description: Optional[str] = None,
        priority: Optional[Priority] = None,
        changelog: str = "",
    ) -> None:
        if self.status not in (RequirementStatus.DRAFT, RequirementStatus.REVIEW):
            raise ValueError(
                f"Requisito {self.id} com status {self.status.value} não pode ser refinado"
            )
        if title:
            self.title = title
        if description:
            self.description = description
        if priority:
            self.priority = priority
        self.version = self.version.next_minor(changelog)
        self.status = RequirementStatus.REVIEW
        self.updated_at = datetime.utcnow()

    def update_quality(self, score: QualityScore) -> None:
        self.quality_score = score
        self.updated_at = datetime.utcnow()

    def approve(self, approved_by: str) -> None:
        if self.quality_score.blocks_approval():
            raise ValueError(
                f"Requisito {self.id} não pode ser aprovado: "
                f"score de clareza {self.quality_score.clarity:.1f} abaixo de 60"
            )
        self.status = RequirementStatus.APPROVED
        self.updated_at = datetime.utcnow()

    def add_acceptance_criteria(self, ac: AcceptanceCriteria) -> None:
        self.acceptance_criteria.append(ac)
        self.updated_at = datetime.utcnow()


@dataclass
class ElicitationSession:
    id: str
    project_id: str
    input_type: str
    raw_input: str
    normalized_input: Optional[str] = None
    language: str = "pt"
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Project:
    id: str
    name: str
    description: Optional[str]
    domain: Optional[str]
    status: str = "ACTIVE"
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def archive(self) -> None:
        if self.status != "ACTIVE":
            raise ValueError(f"Projeto {self.id} já está {self.status}")
        self.status = "ARCHIVED"
        self.updated_at = datetime.utcnow()
