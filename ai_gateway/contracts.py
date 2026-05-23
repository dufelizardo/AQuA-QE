from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ModelProvider(Enum):
    OPENAI = "openai"
    CLAUDE = "claude"
    GEMINI = "gemini"
    LOCAL = "local"


class PromptPurpose(Enum):
    EXTRACTION = "extraction"
    VALIDATION = "validation"
    GENERATION = "generation"
    SCORING = "scoring"
    ACCESSIBILITY = "accessibility"


@dataclass(frozen=True)
class PromptRequest:
    purpose: PromptPurpose
    system: str
    user: str
    context_id: str
    max_tokens: int = 2000
    temperature: float = 0.2
    cost_budget: Optional[str] = None
    preferred_provider: Optional[ModelProvider] = None


@dataclass(frozen=True)
class PromptResponse:
    content: str
    provider_used: ModelProvider
    model_used: str
    tokens_in: int
    tokens_out: int
    latency_ms: int
    cached: bool = False
    cost_usd: float = 0.0


class IAIGateway(ABC):
    @abstractmethod
    def complete(self, request: PromptRequest) -> PromptResponse: ...

    @abstractmethod
    async def complete_async(self, request: PromptRequest) -> PromptResponse: ...
