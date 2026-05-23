from __future__ import annotations
from typing import Optional, Sequence
from sqlalchemy.orm import Session
from requirements.contracts.i_requirement_reader import IRequirementReader, RequirementFilter
from requirements.contracts.requirement_snapshot import RequirementSnapshot
from requirements.domain.value_objects import RequirementStatus
from requirements.infrastructure.models import RequirementModel
from requirements.infrastructure.mappers import RequirementMapper


class RequirementReader(IRequirementReader):
    def __init__(self, session: Session) -> None:
        self._s = session

    def get_snapshot(self, requirement_id: str, version: Optional[str] = None) -> RequirementSnapshot:
        if version:
            major, minor = (int(p) for p in version.lstrip("v").split("."))
            model = (
                self._s.query(RequirementModel)
                .filter(RequirementModel.id == requirement_id,
                        RequirementModel.version_major == major,
                        RequirementModel.version_minor == minor)
                .first()
            )
        else:
            model = self._s.get(RequirementModel, requirement_id)
        if not model:
            raise ValueError(f"Requisito {requirement_id} não encontrado")
        return RequirementMapper.to_snapshot(RequirementMapper.to_domain(model))

    def list_snapshots(self, filters: RequirementFilter) -> Sequence[RequirementSnapshot]:
        q = self._s.query(RequirementModel)
        if filters.project_id:
            q = q.filter(RequirementModel.project_id == filters.project_id)
        if filters.req_type:
            q = q.filter(RequirementModel.req_type == filters.req_type.value)
        if filters.priority:
            q = q.filter(RequirementModel.priority == filters.priority.value)
        if filters.status:
            q = q.filter(RequirementModel.status == filters.status)
        if filters.min_quality is not None:
            q = q.filter(RequirementModel.score_clarity >= filters.min_quality)
        return [RequirementMapper.to_snapshot(RequirementMapper.to_domain(m)) for m in q.all()]

    def get_project_snapshots(self, project_id: str, approved_only: bool = True) -> Sequence[RequirementSnapshot]:
        q = self._s.query(RequirementModel).filter(RequirementModel.project_id == project_id)
        if approved_only:
            q = q.filter(RequirementModel.status == RequirementStatus.APPROVED.value)
        return [RequirementMapper.to_snapshot(RequirementMapper.to_domain(m)) for m in q.all()]

    def snapshot_exists(self, requirement_id: str) -> bool:
        return (
            self._s.query(RequirementModel.id)
            .filter(RequirementModel.id == requirement_id)
            .first()
        ) is not None
