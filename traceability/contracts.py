from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Sequence
from requirements.contracts.events import DomainEvent


class LinkType(Enum):
    IMPLEMENTS = "IMPLEMENTS"
    TESTS      = "TESTS"
    REFINES    = "REFINES"
    RISKS      = "RISKS"
    EVIDENCES  = "EVIDENCES"
    SUPERSEDES = "SUPERSEDES"


class ArtifactType(Enum):
    REQUIREMENT         = "REQUIREMENT"
    BUSINESS_RULE       = "BUSINESS_RULE"
    ACCEPTANCE_CRITERIA = "ACCEPTANCE_CRITERIA"
    TEST_SCENARIO       = "TEST_SCENARIO"
    ACCESSIBILITY_ISSUE = "ACCESSIBILITY_ISSUE"
    RISK                = "RISK"


@dataclass(frozen=True)
class ArtifactRef:
    artifact_type: ArtifactType
    artifact_id:   str
    version:       str

    def __str__(self) -> str:
        return f"{self.artifact_type.value}:{self.artifact_id}@{self.version}"


@dataclass(frozen=True)
class TraceabilityLinkDTO:
    link_id:    str
    source:     ArtifactRef
    target:     ArtifactRef
    link_type:  LinkType
    created_at: datetime
    active:     bool = True


@dataclass(frozen=True)
class ImpactAnalysisDTO:
    changed_artifact:   ArtifactRef
    affected_artifacts: Sequence[ArtifactRef]
    affected_count:     int
    analysis_at:        datetime


class ITraceabilityService(ABC):
    @abstractmethod
    def register_link(self, source: ArtifactRef, target: ArtifactRef, link_type: LinkType) -> TraceabilityLinkDTO: ...

    @abstractmethod
    def invalidate_link(self, link_id: str, reason: str) -> None: ...

    @abstractmethod
    def get_impact(self, artifact: ArtifactRef) -> ImpactAnalysisDTO: ...

    @abstractmethod
    def get_matrix(self, project_id: str) -> Sequence[TraceabilityLinkDTO]: ...


@dataclass(frozen=True)
class LinkCreated(DomainEvent):
    link: TraceabilityLinkDTO = None


@dataclass(frozen=True)
class LinkInvalidated(DomainEvent):
    link_id: str = ""
    reason:  str = ""


@dataclass(frozen=True)
class ImpactAnalysisCompleted(DomainEvent):
    analysis: ImpactAnalysisDTO = None


@dataclass(frozen=True)
class OrphanLinkDetected(DomainEvent):
    link_id:          str = ""
    missing_artifact: ArtifactRef = None
