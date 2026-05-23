from __future__ import annotations
import os, logging, time, json
from ai_gateway.contracts import IAIGateway, PromptRequest, PromptResponse, ModelProvider, PromptPurpose

logger = logging.getLogger(__name__)

_ROUTING: dict[PromptPurpose, ModelProvider] = {
    PromptPurpose.EXTRACTION: ModelProvider.CLAUDE,
    PromptPurpose.VALIDATION: ModelProvider.CLAUDE,
    PromptPurpose.GENERATION: ModelProvider.CLAUDE,
    PromptPurpose.SCORING: ModelProvider.OPENAI,
    PromptPurpose.ACCESSIBILITY: ModelProvider.CLAUDE,
}
_FALLBACK = {ModelProvider.CLAUDE: ModelProvider.OPENAI, ModelProvider.OPENAI: ModelProvider.CLAUDE}


class AIGatewayRouter(IAIGateway):
    def __init__(self) -> None:
        self._adapters: dict[ModelProvider, IAIGateway] = {}
        self._init_adapters()

    def _init_adapters(self) -> None:
        if os.getenv("ANTHROPIC_API_KEY") and os.getenv("ANTHROPIC_API_KEY") != "mock":
            try:
                from ai_gateway.infrastructure.claude_adapter import ClaudeAdapter
                self._adapters[ModelProvider.CLAUDE] = ClaudeAdapter()
                logger.info("[AIGateway] Claude registrado")
            except Exception as e:
                logger.warning(f"[AIGateway] Claude indisponível: {e}")
        if os.getenv("OPENAI_API_KEY") and os.getenv("OPENAI_API_KEY") != "mock":
            try:
                from ai_gateway.infrastructure.openai_adapter import OpenAIAdapter
                self._adapters[ModelProvider.OPENAI] = OpenAIAdapter()
                logger.info("[AIGateway] OpenAI registrado")
            except Exception as e:
                logger.warning(f"[AIGateway] OpenAI indisponível: {e}")
        if not self._adapters:
            logger.warning("[AIGateway] Sem adaptadores — modo mock ativo")

    def complete(self, request: PromptRequest) -> PromptResponse:
        provider = request.preferred_provider or _ROUTING.get(request.purpose, ModelProvider.CLAUDE)
        return self._try_complete(request, provider)

    async def complete_async(self, request: PromptRequest) -> PromptResponse:
        return self.complete(request)

    def _try_complete(self, request: PromptRequest, provider: ModelProvider, tried: set | None = None) -> PromptResponse:
        tried = tried or set()
        tried.add(provider)
        adapter = self._adapters.get(provider)
        if not adapter:
            fallback = _FALLBACK.get(provider)
            if fallback and fallback not in tried:
                return self._try_complete(request, fallback, tried)
            return self._mock_response(request)
        try:
            return adapter.complete(request)
        except Exception as exc:
            fallback = _FALLBACK.get(provider)
            if fallback and fallback not in tried:
                logger.warning(f"[AIGateway] {provider.value} falhou ({exc}), fallback → {fallback.value}")
                return self._try_complete(request, fallback, tried)
            raise

    def _mock_response(self, request: PromptRequest) -> PromptResponse:
        logger.warning("[AIGateway] Usando mock response")
        content = json.dumps({
            "requirements": [{
                "title": "Requisito extraído via mock",
                "description": "Descrição gerada em modo mock sem API key configurada",
                "type": "RF", "priority": "SHOULD",
                "scores": {"clarity": 70.0, "completeness": 65.0, "testability": 72.0, "consistency": 68.0},
                "acceptance_criteria": [{
                    "description": "Critério mock",
                    "given": "contexto mock", "when": "ação mock", "then": "resultado mock",
                }],
            }],
            "gaps": [], "questions": [], "issues": [], "wcag_issues": [],
        })
        return PromptResponse(
            content=content, provider_used=ModelProvider.LOCAL, model_used="mock",
            tokens_in=0, tokens_out=0, latency_ms=0,
        )
