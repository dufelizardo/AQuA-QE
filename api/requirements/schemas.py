from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class CreateProjectRequest(BaseModel):
    name: str
    description: Optional[str] = None
    domain: Optional[str] = None


class CreateProjectResponse(BaseModel):
    id: str
    name: str


class ElicitRequest(BaseModel):
    raw_input: str = Field(..., min_length=5)
    input_type: str = "TEXT"
    language: str = "pt"


class AcceptanceCriteriaOut(BaseModel):
    id: str
    description: str
    given: str
    when: str
    then: str


class QualityScoreOut(BaseModel):
    clarity: float
    completeness: float
    testability: float
    consistency: float
    overall: float


class RequirementOut(BaseModel):
    id: str
    title: str
    description: str
    req_type: str
    priority: str
    status: str
    version: str
    quality_score: QualityScoreOut
    acceptance_criteria: List[AcceptanceCriteriaOut]

    @classmethod
    def from_domain(cls, req) -> "RequirementOut":
        return cls(
            id=req.id, title=req.title, description=req.description,
            req_type=req.req_type.value, priority=req.priority.value, status=req.status.value,
            version=str(req.version),
            quality_score=QualityScoreOut(
                clarity=req.quality_score.clarity, completeness=req.quality_score.completeness,
                testability=req.quality_score.testability, consistency=req.quality_score.consistency,
                overall=req.quality_score.overall,
            ),
            acceptance_criteria=[
                AcceptanceCriteriaOut(id=ac.id, description=ac.description, given=ac.given, when=ac.when, then=ac.then)
                for ac in req.acceptance_criteria
            ],
        )

    @classmethod
    def from_snapshot(cls, snap) -> "RequirementOut":
        return cls(
            id=snap.id, title=snap.title, description=snap.description,
            req_type=snap.req_type.value, priority=snap.priority.value, status="SNAPSHOT",
            version=str(snap.version),
            quality_score=QualityScoreOut(
                clarity=snap.quality_score.clarity, completeness=snap.quality_score.completeness,
                testability=snap.quality_score.testability, consistency=snap.quality_score.consistency,
                overall=snap.quality_score.overall,
            ),
            acceptance_criteria=[
                AcceptanceCriteriaOut(id=ac.id, description=ac.description, given=ac.given, when=ac.when, then=ac.then)
                for ac in snap.acceptance_criteria
            ],
        )


class ElicitResponse(BaseModel):
    session_id: str
    requirements: List[RequirementOut]
    gaps_detected: List[str]


class RefineRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    changelog: Optional[str] = None
    ai_assisted: bool = False


class RefineResponse(BaseModel):
    requirement_id: str
    refined: bool


class ApproveRequest(BaseModel):
    approved_by: str = "system"


class ApproveResponse(BaseModel):
    requirement_id: str
    approved: bool


class BulkApproveResponse(BaseModel):
    approved: List[str]
    failed: List[dict]
