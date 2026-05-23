from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Generator
from persistence.base import get_session
from api.requirements.schemas import (
    CreateProjectRequest, CreateProjectResponse,
    ElicitRequest, ElicitResponse,
    RefineRequest, RefineResponse,
    ApproveRequest, ApproveResponse,
    BulkApproveResponse, RequirementOut,
)
from requirements.domain.entities import Project
from requirements.infrastructure.repository import RequirementRepository
from requirements.infrastructure.reader import RequirementReader
from requirements.application.create import CreateRequirementUseCase, CreateRequirementCommand
from requirements.application.refine import RefineRequirementUseCase, RefineRequirementCommand
from requirements.application.approve import ApproveRequirementUseCase, ApproveRequirementCommand, BulkApproveUseCase
from ai_gateway.infrastructure.router import AIGatewayRouter
from ai_gateway.acl import AIGatewayACL
from shared.event_bus import InProcessEventBus
import uuid

router = APIRouter(prefix="/requirements", tags=["requirements"])
_ai_router = AIGatewayRouter()


def _get_session() -> Generator[Session, None, None]:
    """Re-exported para o router usar sem importar sessionmaker diretamente."""
    from main import _session_factory
    yield from get_session(_session_factory)


def _make_usecases(session: Session) -> dict:
    bus = InProcessEventBus()
    ai_acl = AIGatewayACL(_ai_router)
    repo = RequirementRepository(session)
    reader = RequirementReader(session)
    return {
        "repo": repo, "reader": reader,
        "create": CreateRequirementUseCase(repo, ai_acl, bus),
        "refine": RefineRequirementUseCase(repo, ai_acl, bus),
        "approve": ApproveRequirementUseCase(repo, bus),
        "bulk": BulkApproveUseCase(repo, bus),
    }


@router.post("/projects", response_model=CreateProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(body: CreateProjectRequest, session: Session = Depends(_get_session)):
    project = Project(id=str(uuid.uuid4()), name=body.name, description=body.description, domain=body.domain)
    RequirementRepository(session).save_project(project)
    return CreateProjectResponse(id=project.id, name=project.name)


@router.post("/projects/{project_id}/elicit", response_model=ElicitResponse)
def elicit(project_id: str, body: ElicitRequest, session: Session = Depends(_get_session)):
    uc = _make_usecases(session)
    try:
        result = uc["create"].execute(CreateRequirementCommand(
            project_id=project_id, raw_input=body.raw_input,
            input_type=body.input_type, language=body.language,
        ))
    except ValueError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc))
    return ElicitResponse(
        session_id=result.session_id,
        requirements=[RequirementOut.from_domain(r) for r in result.requirements],
        gaps_detected=result.gaps_detected,
    )


@router.patch("/{requirement_id}/refine", response_model=RefineResponse)
def refine(requirement_id: str, body: RefineRequest, session: Session = Depends(_get_session)):
    uc = _make_usecases(session)
    try:
        uc["refine"].execute(RefineRequirementCommand(
            requirement_id=requirement_id, title=body.title, description=body.description,
            priority=body.priority, changelog=body.changelog or "", ai_assisted=body.ai_assisted,
        ))
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    return RefineResponse(requirement_id=requirement_id, refined=True)


@router.post("/{requirement_id}/approve", response_model=ApproveResponse)
def approve(requirement_id: str, body: ApproveRequest, session: Session = Depends(_get_session)):
    uc = _make_usecases(session)
    try:
        uc["approve"].execute(ApproveRequirementCommand(requirement_id=requirement_id, approved_by=body.approved_by))
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    return ApproveResponse(requirement_id=requirement_id, approved=True)


@router.post("/projects/{project_id}/approve-all", response_model=BulkApproveResponse)
def bulk_approve(project_id: str, body: ApproveRequest, session: Session = Depends(_get_session)):
    uc = _make_usecases(session)
    result = uc["bulk"].execute(project_id, body.approved_by)
    return BulkApproveResponse(**result)


@router.get("/projects/{project_id}", response_model=list[RequirementOut])
def list_requirements(project_id: str, approved_only: bool = False, session: Session = Depends(_get_session)):
    reader = RequirementReader(session)
    snapshots = reader.get_project_snapshots(project_id, approved_only=approved_only)
    return [RequirementOut.from_snapshot(s) for s in snapshots]
