from __future__ import annotations
from ai_gateway.contracts import IAIGateway, PromptRequest, PromptResponse, PromptPurpose
from requirements.contracts.requirement_snapshot import RequirementSnapshot

_SYSTEM_PROMPTS = {
    PromptPurpose.EXTRACTION: (
        "Você é um especialista sênior em engenharia de requisitos de software. "
        "Extraia requisitos estruturados do texto fornecido pelo usuário. "
        "Classifique cada item como RF, RNF, RN, CONSTRAINT ou ASSUMPTION. "
        "Para cada requisito gere critérios de aceite Given-When-Then quando aplicável. "
        "Atribua scores de clareza, completude, testabilidade e consistência (0–100). "
        "Identifique gaps e perguntas complementares. "
        'Responda EXCLUSIVAMENTE em JSON: {"requirements": [...], "gaps": [...], "questions": []}'
    ),
    PromptPurpose.VALIDATION: (
        "Você é um analista de qualidade de requisitos. "
        "Analise o requisito e identifique ambiguidades, inconsistências, gaps e problemas de testabilidade. "
        "Para cada issue forneça: type, severity (CRITICAL|HIGH|MEDIUM|LOW), description, suggestion, location. "
        'Responda EXCLUSIVAMENTE em JSON: {"issues": [...], "improved_title": "", "improved_description": "", "improved_scores": {}}'
    ),
    PromptPurpose.GENERATION: (
        "Você é um engenheiro de testes sênior especialista em BDD. "
        "Gere cenários Given-When-Then para o requisito fornecido. "
        "Para cada cenário: feature, scenario, given, when, then, tags, automation_strategy. "
        "Responda EXCLUSIVAMENTE em JSON: [{...}]"
    ),
    PromptPurpose.ACCESSIBILITY: (
        "Você é um especialista em acessibilidade WCAG 2.1/2.2. "
        "Analise os requisitos e identifique critérios WCAG ausentes ou violados. "
        "Para cada issue: code, level (A|AA|AAA), description, recommendation. "
        'Responda EXCLUSIVAMENTE em JSON: {"wcag_issues": [...]}'
    ),
    PromptPurpose.SCORING: (
        "Você é um auditor de qualidade de requisitos. "
        "Avalie e retorne scores de qualidade. Responda EXCLUSIVAMENTE em JSON."
    ),
}


class AIGatewayACL:
    def __init__(self, gateway: IAIGateway) -> None:
        self._gw = gateway

    def extract_requirements(self, raw_input: str, context_id: str) -> PromptResponse:
        return self._gw.complete(PromptRequest(
            purpose=PromptPurpose.EXTRACTION,
            system=_SYSTEM_PROMPTS[PromptPurpose.EXTRACTION],
            user=raw_input, context_id=context_id,
            max_tokens=4000, temperature=0.1, cost_budget="medium",
        ))

    def validate_requirement(self, snapshot: RequirementSnapshot, context_id: str) -> PromptResponse:
        user = (
            f"Título: {snapshot.title}\nTipo: {snapshot.req_type.value}\n"
            f"Descrição: {snapshot.description}\nCritérios:\n"
            + "\n".join(f"  - Dado {ac.given} | Quando {ac.when} | Então {ac.then}"
                        for ac in snapshot.acceptance_criteria)
        )
        return self._gw.complete(PromptRequest(
            purpose=PromptPurpose.VALIDATION,
            system=_SYSTEM_PROMPTS[PromptPurpose.VALIDATION],
            user=user, context_id=context_id,
            max_tokens=2000, temperature=0.1, cost_budget="low",
        ))

    def generate_test_scenarios(self, snapshot: RequirementSnapshot, context_id: str) -> PromptResponse:
        user = (
            f"Requisito: {snapshot.title}\nDescrição: {snapshot.description}\n"
            + "\n".join(f"  - Dado {ac.given} | Quando {ac.when} | Então {ac.then}"
                        for ac in snapshot.acceptance_criteria)
        )
        return self._gw.complete(PromptRequest(
            purpose=PromptPurpose.GENERATION,
            system=_SYSTEM_PROMPTS[PromptPurpose.GENERATION],
            user=user, context_id=context_id,
            max_tokens=3000, temperature=0.2, cost_budget="medium",
        ))

    def analyze_accessibility(self, snapshots_text: str, context_id: str) -> PromptResponse:
        return self._gw.complete(PromptRequest(
            purpose=PromptPurpose.ACCESSIBILITY,
            system=_SYSTEM_PROMPTS[PromptPurpose.ACCESSIBILITY],
            user=snapshots_text, context_id=context_id,
            max_tokens=2000, temperature=0.1, cost_budget="low",
        ))
