from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Sequence, Optional
from requirements.contracts.events import DomainEvent


class PatternType(Enum):
    REQUIREMENT   = "REQUIREMENT"
    BUSINESS_RULE = "BUSINESS_RULE"
    TEST_SCENARIO = "TEST_SCENARIO"
    CRITERIA      = "CRITERIA"


@dataclass(frozen=True)
class KnowledgeContribution:
    source_context: str
    pattern_type:   PatternType
    domain:         str
    content:        str
    confidence:     float
    source_id:      str
    embedding:      Optional[list] = None


@dataclass(frozen=True)
class KnowledgePatternDTO:
    id:           str
    pattern_type: PatternType
    domain:       str
    content:      str
    usage_count:  int
    confidence:   float
    created_at:   datetime

    def is_mature(self) -> bool:
        return self.usage_count >= 3


@dataclass(frozen=True)
class KnowledgeQuery:
    domain:        str
    pattern_type:  Optional[PatternType] = None
    semantic_text: Optional[str] = None
    limit:         int = 10


class IKnowledgeService(ABC):
    @abstractmethod
    def contribute(self, contribution: KnowledgeContribution) -> None: ...

    @abstractmethod
    def query(self, query: KnowledgeQuery) -> Sequence[KnowledgePatternDTO]: ...

    @abstractmethod
    def get_ontology(self, domain: str) -> dict: ...


@dataclass(frozen=True)
class PatternLearned(DomainEvent):
    pattern: KnowledgePatternDTO = None
    domain:  str = ""


@dataclass(frozen=True)
class PatternPromoted(DomainEvent):
    pattern_id:  str = ""
    usage_count: int = 0


@dataclass(frozen=True)
class ReuseTemplateSuggested(DomainEvent):
    context:      str = ""
    pattern_id:   str = ""
    triggered_by: str = ""
