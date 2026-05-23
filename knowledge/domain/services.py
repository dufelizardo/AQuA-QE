from __future__ import annotations
import uuid, logging
from typing import Sequence
from knowledge.contracts import IKnowledgeService, KnowledgeContribution, KnowledgeQuery, KnowledgePatternDTO, PatternLearned, PatternPromoted
from knowledge.domain.entities import OrganizationalPattern, KnowledgeBase

logger = logging.getLogger(__name__)


class KnowledgeService(IKnowledgeService):
    def __init__(self, repo) -> None:
        self._repo = repo

    def contribute(self, contribution: KnowledgeContribution) -> None:
        existing = self._repo.find_by_source(contribution.source_context, contribution.source_id)
        if existing:
            existing.increment_usage()
            self._repo.update_pattern(existing)
            self._check_promotion(existing)
            return
        pattern = OrganizationalPattern(
            id=str(uuid.uuid4()), source_context=contribution.source_context,
            pattern_type=contribution.pattern_type, domain=contribution.domain,
            content=contribution.content, confidence=contribution.confidence,
            source_id=contribution.source_id, embedding=contribution.embedding,
        )
        self._repo.save_pattern(pattern)
        logger.info(f"[Knowledge] Padrão aprendido: {pattern.id} [{pattern.pattern_type.value}]")

    def query(self, query: KnowledgeQuery) -> Sequence[KnowledgePatternDTO]:
        patterns = self._repo.find_by_domain(domain=query.domain, pattern_type=query.pattern_type, limit=query.limit)
        if query.semantic_text:
            kb = KnowledgeBase(domain=query.domain, patterns=patterns)
            patterns = kb.find_similar(query.semantic_text, query.limit)
        return [p.to_dto() for p in patterns]

    def get_ontology(self, domain: str) -> dict:
        ontology = self._repo.get_latest_ontology(domain)
        if not ontology:
            return {"domain": domain, "terms": {}, "relations": {}, "version": 0}
        import json
        data = json.loads(ontology.content)
        return {"domain": ontology.domain, "terms": data.get("terms",{}), "relations": data.get("relations",{}), "version": ontology.version}

    def _check_promotion(self, pattern: OrganizationalPattern) -> None:
        if pattern.is_mature() and not pattern.promoted:
            pattern.promote()
            self._repo.update_pattern(pattern)
            logger.info(f"[Knowledge] Padrão promovido: {pattern.id} (uso: {pattern.usage_count}x)")
