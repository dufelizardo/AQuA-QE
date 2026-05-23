from __future__ import annotations
import uuid, logging
from datetime import datetime
from typing import Sequence
from traceability.contracts import (
    ITraceabilityService, ArtifactRef, LinkType,
    TraceabilityLinkDTO, ImpactAnalysisDTO,
)
from traceability.domain.entities import TraceabilityLink

logger = logging.getLogger(__name__)


class TraceabilityService(ITraceabilityService):
    def __init__(self, repo) -> None:
        self._repo = repo

    def register_link(self, source: ArtifactRef, target: ArtifactRef, link_type: LinkType) -> TraceabilityLinkDTO:
        existing = self._repo.find_link(source, target, link_type)
        if existing and existing.active:
            return existing.to_dto()
        link = TraceabilityLink(id=str(uuid.uuid4()), source=source, target=target, link_type=link_type)
        project_id = self._repo.project_id_for(source.artifact_id) or "unknown"
        self._repo.save_link(link, project_id)
        logger.info(f"[Traceability] Link registrado: {source} → {target} [{link_type.value}]")
        return link.to_dto()

    def invalidate_link(self, link_id: str, reason: str) -> None:
        link = self._repo.get_link(link_id)
        if not link:
            raise ValueError(f"Link {link_id} não encontrado")
        link.invalidate(reason)
        self._repo.update_link(link)

    def get_impact(self, artifact: ArtifactRef) -> ImpactAnalysisDTO:
        matrix   = self._repo.get_matrix(artifact)
        impacted = matrix.impact_of(artifact)
        return ImpactAnalysisDTO(
            changed_artifact=artifact, affected_artifacts=impacted,
            affected_count=len(impacted), analysis_at=datetime.utcnow(),
        )

    def get_matrix(self, project_id: str) -> Sequence[TraceabilityLinkDTO]:
        matrix = self._repo.get_full_matrix(project_id)
        return [l.to_dto() for l in matrix.active_links()]
