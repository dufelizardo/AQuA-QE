from __future__ import annotations
from typing import Optional, List
from sqlalchemy.orm import Session
from requirements.domain.entities import Project, Requirement, AcceptanceCriteria, ElicitationSession
from requirements.domain.value_objects import RequirementStatus
from requirements.infrastructure.models import ProjectModel, RequirementModel, AcceptanceCriteriaModel, SessionModel
from requirements.infrastructure.mappers import RequirementMapper, AcceptanceCriteriaMapper, ProjectMapper


class RequirementRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def save_project(self, project: Project) -> None:
        existing = self._s.get(ProjectModel, project.id)
        if existing:
            existing.name = project.name
            existing.description = project.description
            existing.domain = project.domain
            existing.status = project.status
            existing.updated_at = project.updated_at
        else:
            self._s.add(ProjectMapper.to_model(project))

    def get_project(self, project_id: str) -> Optional[Project]:
        model = self._s.get(ProjectModel, project_id)
        return ProjectMapper.to_domain(model) if model else None

    def project_exists(self, project_id: str) -> bool:
        return self._s.get(ProjectModel, project_id) is not None

    def save_requirement(self, req: Requirement) -> None:
        existing = self._s.get(RequirementModel, req.id)
        if existing:
            existing.title = req.title
            existing.description = req.description
            existing.req_type = req.req_type.value
            existing.priority = req.priority.value
            existing.status = req.status.value
            existing.version_major = req.version.major
            existing.version_minor = req.version.minor
            existing.version_changelog = req.version.changelog
            existing.score_clarity = req.quality_score.clarity
            existing.score_completeness = req.quality_score.completeness
            existing.score_testability = req.quality_score.testability
            existing.score_consistency = req.quality_score.consistency
            existing.updated_at = req.updated_at
            existing_ac_ids = {ac.id for ac in existing.acceptance_criteria}
            for ac in req.acceptance_criteria:
                if ac.id not in existing_ac_ids:
                    self._s.add(AcceptanceCriteriaMapper.to_model(ac, req.id))
        else:
            model = RequirementMapper.to_model(req)
            self._s.add(model)
            for ac in req.acceptance_criteria:
                self._s.add(AcceptanceCriteriaMapper.to_model(ac, req.id))

    def get_requirement(self, req_id: str) -> Optional[Requirement]:
        model = self._s.get(RequirementModel, req_id)
        return RequirementMapper.to_domain(model) if model else None

    def list_by_project(self, project_id: str, status: Optional[RequirementStatus] = None) -> List[Requirement]:
        q = self._s.query(RequirementModel).filter(RequirementModel.project_id == project_id)
        if status:
            q = q.filter(RequirementModel.status == status.value)
        return [RequirementMapper.to_domain(m) for m in q.all()]

    def requirement_exists(self, req_id: str) -> bool:
        return self._s.get(RequirementModel, req_id) is not None

    def save_session(self, session: ElicitationSession) -> None:
        self._s.add(SessionModel(
            id=session.id, project_id=session.project_id, input_type=session.input_type,
            raw_input=session.raw_input, normalized_input=session.normalized_input,
            language=session.language, created_at=session.created_at,
        ))
