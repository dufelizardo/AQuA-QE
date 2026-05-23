from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from traceability.contracts import LinkType, ArtifactRef, ArtifactType, TraceabilityLinkDTO


@dataclass
class TraceabilityLink:
    id:                 str
    source:             ArtifactRef
    target:             ArtifactRef
    link_type:          LinkType
    created_at:         datetime = field(default_factory=datetime.utcnow)
    active:             bool = True
    invalidated_reason: Optional[str] = None
    invalidated_at:     Optional[datetime] = None

    def invalidate(self, reason: str) -> None:
        if not self.active:
            raise ValueError(f"Link {self.id} já está inativo")
        self.active = False
        self.invalidated_reason = reason
        self.invalidated_at = datetime.utcnow()

    def to_dto(self) -> TraceabilityLinkDTO:
        return TraceabilityLinkDTO(
            link_id=self.id, source=self.source, target=self.target,
            link_type=self.link_type, created_at=self.created_at, active=self.active,
        )


@dataclass
class TraceabilityMatrix:
    project_id: str
    links:      List[TraceabilityLink] = field(default_factory=list)

    def active_links(self) -> List[TraceabilityLink]:
        return [l for l in self.links if l.active]

    def links_from(self, ref: ArtifactRef) -> List[TraceabilityLink]:
        return [l for l in self.active_links()
                if l.source.artifact_id == ref.artifact_id and l.source.artifact_type == ref.artifact_type]

    def impact_of(self, ref: ArtifactRef) -> List[ArtifactRef]:
        visited: set[str] = set()
        queue = [ref]
        impacted: List[ArtifactRef] = []
        while queue:
            current = queue.pop(0)
            key = f"{current.artifact_type.value}:{current.artifact_id}"
            if key in visited:
                continue
            visited.add(key)
            for link in self.links_from(current):
                impacted.append(link.target)
                queue.append(link.target)
        return impacted
