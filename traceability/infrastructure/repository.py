from __future__ import annotations
from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session
from traceability.infrastructure.models import TraceabilityLinkModel
from traceability.domain.entities import TraceabilityLink, TraceabilityMatrix
from traceability.contracts import ArtifactRef, ArtifactType, LinkType
from requirements.infrastructure.models import RequirementModel


class TraceabilityRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def save_link(self, link: TraceabilityLink, project_id: str) -> None:
        self._s.add(TraceabilityLinkModel(
            id=link.id, project_id=project_id,
            source_type=link.source.artifact_type.value, source_id=link.source.artifact_id, source_ver=link.source.version,
            target_type=link.target.artifact_type.value, target_id=link.target.artifact_id, target_ver=link.target.version,
            link_type=link.link_type.value, active=link.active, created_at=link.created_at,
        ))
        self._s.flush()

    def get_link(self, link_id: str) -> Optional[TraceabilityLink]:
        m = self._s.get(TraceabilityLinkModel, link_id)
        return self._to_domain(m) if m else None

    def update_link(self, link: TraceabilityLink) -> None:
        m = self._s.get(TraceabilityLinkModel, link.id)
        if m:
            m.active = link.active
            m.invalidated_reason = link.invalidated_reason
            m.invalidated_at = link.invalidated_at

    def find_link(self, source: ArtifactRef, target: ArtifactRef, link_type: LinkType) -> Optional[TraceabilityLink]:
        m = (self._s.query(TraceabilityLinkModel).filter(
            TraceabilityLinkModel.source_type == source.artifact_type.value,
            TraceabilityLinkModel.source_id   == source.artifact_id,
            TraceabilityLinkModel.target_type == target.artifact_type.value,
            TraceabilityLinkModel.target_id   == target.artifact_id,
            TraceabilityLinkModel.link_type   == link_type.value,
        ).first())
        return self._to_domain(m) if m else None

    def get_full_matrix(self, project_id: str) -> TraceabilityMatrix:
        models = self._s.query(TraceabilityLinkModel).filter(TraceabilityLinkModel.project_id == project_id).all()
        matrix = TraceabilityMatrix(project_id=project_id)
        for m in models:
            matrix.links.append(self._to_domain(m))
        return matrix

    def get_matrix(self, artifact: ArtifactRef) -> TraceabilityMatrix:
        models = self._s.query(TraceabilityLinkModel).filter(
            ((TraceabilityLinkModel.source_type == artifact.artifact_type.value) &
             (TraceabilityLinkModel.source_id   == artifact.artifact_id)) |
            ((TraceabilityLinkModel.target_type == artifact.artifact_type.value) &
             (TraceabilityLinkModel.target_id   == artifact.artifact_id))
        ).all()
        matrix = TraceabilityMatrix(project_id="adhoc")
        for m in models:
            matrix.links.append(self._to_domain(m))
        return matrix

    def project_id_for(self, requirement_id: str) -> Optional[str]:
        m = self._s.get(RequirementModel, requirement_id)
        return m.project_id if m else None

    def _to_domain(self, m: TraceabilityLinkModel) -> TraceabilityLink:
        return TraceabilityLink(
            id=m.id,
            source=ArtifactRef(ArtifactType(m.source_type), m.source_id, m.source_ver),
            target=ArtifactRef(ArtifactType(m.target_type), m.target_id, m.target_ver),
            link_type=LinkType(m.link_type), created_at=m.created_at, active=m.active,
            invalidated_reason=m.invalidated_reason, invalidated_at=m.invalidated_at,
        )
