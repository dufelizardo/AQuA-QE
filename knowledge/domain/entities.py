from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from knowledge.contracts import PatternType, KnowledgePatternDTO


@dataclass
class OrganizationalPattern:
    id:             str
    source_context: str
    pattern_type:   PatternType
    domain:         str
    content:        str
    confidence:     float
    source_id:      str
    usage_count:    int = 1
    promoted:       bool = False
    embedding:      Optional[List[float]] = None
    created_at:     datetime = field(default_factory=datetime.utcnow)
    last_used_at:   datetime = field(default_factory=datetime.utcnow)

    def increment_usage(self) -> None:
        self.usage_count += 1
        self.last_used_at = datetime.utcnow()

    def promote(self) -> None:
        if self.usage_count < 3:
            raise ValueError(f"Padrão {self.id} não pode ser promovido: usage_count={self.usage_count} < 3")
        self.promoted = True

    def is_mature(self) -> bool:
        return self.usage_count >= 3

    def to_dto(self) -> KnowledgePatternDTO:
        return KnowledgePatternDTO(
            id=self.id, pattern_type=self.pattern_type, domain=self.domain,
            content=self.content, usage_count=self.usage_count, confidence=self.confidence,
            created_at=self.created_at,
        )


@dataclass
class KnowledgeBase:
    domain:   str
    patterns: List[OrganizationalPattern] = field(default_factory=list)

    def find_similar(self, content: str, limit: int = 5) -> List[OrganizationalPattern]:
        words = set(content.lower().split())
        scored = []
        for p in self.patterns:
            p_words = set(p.content.lower().split())
            overlap = len(words & p_words) / max(len(words | p_words), 1)
            if overlap > 0.1:
                scored.append((overlap, p))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [p for _, p in scored[:limit]]
