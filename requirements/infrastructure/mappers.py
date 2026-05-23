from __future__ import annotations
from datetime import datetime
from requirements.domain.entities import Project, Requirement, AcceptanceCriteria, ElicitationSession
from requirements.domain.value_objects import RequirementType, Priority, RequirementStatus, QualityScore, RequirementVersion
from requirements.infrastructure.models import ProjectModel, RequirementModel, AcceptanceCriteriaModel, SessionModel
from requirements.contracts.requirement_snapshot import RequirementSnapshot, AcceptanceCriteriaSnapshot


class RequirementMapper:
    @staticmethod
    def to_model(req: Requirement) -> RequirementModel:
        return RequirementModel(
            id=req.id, project_id=req.project_id, session_id=req.session_id,
            title=req.title, description=req.description,
            req_type=req.req_type.value, priority=req.priority.value, status=req.status.value,
            version_major=req.version.major, version_minor=req.version.minor,
            version_changelog=req.version.changelog,
            score_clarity=req.quality_score.clarity, score_completeness=req.quality_score.completeness,
            score_testability=req.quality_score.testability, score_consistency=req.quality_score.consistency,
            created_at=req.created_at, updated_at=req.updated_at,
        )

    @staticmethod
    def to_domain(model: RequirementModel) -> Requirement:
        return Requirement(
            id=model.id, project_id=model.project_id, session_id=model.session_id,
            title=model.title, description=model.description,
            req_type=RequirementType(model.req_type), priority=Priority(model.priority),
            status=RequirementStatus(model.status),
            version=RequirementVersion(model.version_major, model.version_minor, model.version_changelog or ""),
            quality_score=QualityScore(
                clarity=model.score_clarity, completeness=model.score_completeness,
                testability=model.score_testability, consistency=model.score_consistency,
            ),
            acceptance_criteria=[AcceptanceCriteriaMapper.to_domain(ac) for ac in (model.acceptance_criteria or [])],
            created_at=model.created_at, updated_at=model.updated_at,
        )

    @staticmethod
    def to_snapshot(req: Requirement) -> RequirementSnapshot:
        return RequirementSnapshot(
            id=req.id, project_id=req.project_id, title=req.title, description=req.description,
            req_type=req.req_type, priority=req.priority, version=req.version,
            quality_score=req.quality_score,
            acceptance_criteria=[
                AcceptanceCriteriaSnapshot(id=ac.id, description=ac.description, given=ac.given, when=ac.when, then=ac.then)
                for ac in req.acceptance_criteria
            ],
            business_rule_ids=list(req.business_rule_ids),
            snapshotted_at=datetime.utcnow(),
        )


class AcceptanceCriteriaMapper:
    @staticmethod
    def to_model(ac: AcceptanceCriteria, requirement_id: str) -> AcceptanceCriteriaModel:
        return AcceptanceCriteriaModel(
            id=ac.id, requirement_id=requirement_id, description=ac.description,
            given_context=ac.given, when_action=ac.when, then_outcome=ac.then, status=ac.status,
        )

    @staticmethod
    def to_domain(model: AcceptanceCriteriaModel) -> AcceptanceCriteria:
        return AcceptanceCriteria(
            id=model.id, description=model.description,
            given=model.given_context, when=model.when_action, then=model.then_outcome, status=model.status,
        )


class ProjectMapper:
    @staticmethod
    def to_model(project: Project) -> ProjectModel:
        return ProjectModel(
            id=project.id, name=project.name, description=project.description,
            domain=project.domain, status=project.status,
            created_at=project.created_at, updated_at=project.updated_at,
        )

    @staticmethod
    def to_domain(model: ProjectModel) -> Project:
        return Project(
            id=model.id, name=model.name, description=model.description,
            domain=model.domain, status=model.status,
            created_at=model.created_at, updated_at=model.updated_at,
        )
