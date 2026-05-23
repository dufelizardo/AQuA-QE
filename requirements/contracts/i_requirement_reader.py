from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Sequence
from requirements.contracts.requirement_snapshot import RequirementSnapshot
from requirements.domain.value_objects import RequirementType, Priority


@dataclass(frozen=True)
class RequirementFilter:
    project_id: Optional[str] = None
    req_type: Optional[RequirementType] = None
    priority: Optional[Priority] = None
    status: Optional[str] = None
    min_quality: Optional[float] = None


class IRequirementReader(ABC):
    @abstractmethod
    def get_snapshot(self, requirement_id: str, version: Optional[str] = None) -> RequirementSnapshot: ...

    @abstractmethod
    def list_snapshots(self, filters: RequirementFilter) -> Sequence[RequirementSnapshot]: ...

    @abstractmethod
    def get_project_snapshots(self, project_id: str, approved_only: bool = True) -> Sequence[RequirementSnapshot]: ...

    @abstractmethod
    def snapshot_exists(self, requirement_id: str) -> bool: ...
