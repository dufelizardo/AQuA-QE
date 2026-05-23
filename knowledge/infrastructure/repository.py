from __future__ import annotations
import json
from typing import Optional, List
from sqlalchemy.orm import Session
from knowledge.infrastructure.models import KnowledgePatternModel, DomainOntologyModel
from knowledge.domain.entities import OrganizationalPattern
from knowledge.contracts import PatternType


class KnowledgeRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def save_pattern(self, pattern: OrganizationalPattern) -> None:
        self._s.add(KnowledgePatternModel(
            id=pattern.id, source_context=pattern.source_context,
            pattern_type=pattern.pattern_type.value, domain=pattern.domain,
            content=pattern.content, confidence=pattern.confidence, usage_count=pattern.usage_count,
            source_id=pattern.source_id, embedding=json.dumps(pattern.embedding) if pattern.embedding else None,
            promoted=pattern.promoted, created_at=pattern.created_at, last_used_at=pattern.last_used_at,
        ))
        self._s.flush()

    def update_pattern(self, pattern: OrganizationalPattern) -> None:
        m = self._s.get(KnowledgePatternModel, pattern.id)
        if m:
            m.usage_count = pattern.usage_count
            m.promoted    = pattern.promoted
            m.last_used_at = pattern.last_used_at

    def find_by_source(self, source_context: str, source_id: str) -> Optional[OrganizationalPattern]:
        m = (self._s.query(KnowledgePatternModel)
             .filter(KnowledgePatternModel.source_context == source_context,
                     KnowledgePatternModel.source_id == source_id).first())
        return self._to_domain(m) if m else None

    def find_by_domain(self, domain: str, pattern_type=None, limit: int = 10) -> List[OrganizationalPattern]:
        q = self._s.query(KnowledgePatternModel).filter(KnowledgePatternModel.domain == domain)
        if pattern_type:
            q = q.filter(KnowledgePatternModel.pattern_type == pattern_type.value)
        q = q.order_by(KnowledgePatternModel.usage_count.desc()).limit(limit)
        return [self._to_domain(m) for m in q.all()]

    def get_latest_ontology(self, domain: str):
        return (self._s.query(DomainOntologyModel).filter(DomainOntologyModel.domain == domain)
                .order_by(DomainOntologyModel.version.desc()).first())

    def _to_domain(self, m: KnowledgePatternModel) -> OrganizationalPattern:
        return OrganizationalPattern(
            id=m.id, source_context=m.source_context, pattern_type=PatternType(m.pattern_type),
            domain=m.domain, content=m.content, confidence=m.confidence, source_id=m.source_id or "",
            usage_count=m.usage_count, promoted=m.promoted,
            embedding=json.loads(m.embedding) if m.embedding else None,
            created_at=m.created_at, last_used_at=m.last_used_at,
        )
