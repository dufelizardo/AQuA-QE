from __future__ import annotations
import uuid, json, logging
from typing import List, Sequence
from requirements.contracts.requirement_snapshot import RequirementSnapshot
from accessibility.contracts import ConformanceLevel, AccessibilityReportDTO, WCAGCriterion
from accessibility.domain.entities import AccessibilityReport, WCAGIssue, HeuristicIssue
from accessibility.domain.wcag_catalog import WCAG_CATALOG, NIELSEN_HEURISTICS, _UI_KEYWORDS
from ai_gateway.acl import AIGatewayACL

logger = logging.getLogger(__name__)

_CHECKS = [
    (["formulário","input","campo"], ["3.3.1","3.3.2","3.3.3"]),
    (["botão","link","ação"],        ["2.1.1","4.1.2"]),
    (["imagem","ícone","ilustração"],["1.1.1"]),
    (["cor","destaque","alerta"],    ["1.4.1","1.4.3"]),
    (["modal","popup","dialog"],     ["2.1.1","4.1.2"]),
    (["autenticação","login"],       ["3.3.8"]),
]
_RECS = {
    "1.1.1": "Adicione critério exigindo texto alternativo para imagens.",
    "1.4.1": "Garanta que informação não seja transmitida apenas por cor.",
    "1.4.3": "Especifique requisito de contraste mínimo 4.5:1 para texto.",
    "2.1.1": "Adicione critério exigindo navegação completa por teclado.",
    "3.3.1": "Inclua critério para identificação e descrição de erros.",
    "3.3.2": "Especifique que campos de formulário devem ter rótulos visíveis.",
    "3.3.3": "Adicione critério de sugestão de correção em erros de validação.",
    "3.3.8": "Especifique autenticação sem exigir teste cognitivo complexo.",
    "4.1.2": "Defina requisito de acessibilidade programática para todos os controles.",
}


class AccessibilityService:
    def __init__(self, repo, reader, ai_acl: AIGatewayACL) -> None:
        self._repo   = repo
        self._reader = reader
        self._ai_acl = ai_acl

    def analyze(self, snapshots: Sequence[RequirementSnapshot], target_level: ConformanceLevel = ConformanceLevel.AA) -> AccessibilityReportDTO:
        project_id = snapshots[0].project_id if snapshots else "unknown"
        report = AccessibilityReport(id=str(uuid.uuid4()), project_id=project_id)
        for snap in snapshots:
            report.wcag_issues.extend(self._heuristic_wcag(snap))
            report.heuristic_issues.extend(self._heuristic_nielsen(snap))
            if self._has_ui(snap):
                report.wcag_issues.extend(self._llm_analyze(snap))
        self._repo.save_report(report)
        logger.info(f"[Accessibility] {report.id}: {len(report.wcag_issues)} WCAG + {len(report.heuristic_issues)} Nielsen")
        return report.to_dto()

    def get_report(self, report_id: str) -> AccessibilityReportDTO:
        report = self._repo.get_report(report_id)
        if not report:
            raise ValueError(f"Relatório {report_id} não encontrado")
        return report.to_dto()

    def _has_ui(self, snap: RequirementSnapshot) -> bool:
        text = f"{snap.title} {snap.description}".lower()
        return any(kw in text for kw in _UI_KEYWORDS)

    def _heuristic_wcag(self, snap: RequirementSnapshot) -> List[WCAGIssue]:
        text = f"{snap.title} {snap.description}".lower()
        ac_text = " ".join(f"{ac.given} {ac.when} {ac.then}" for ac in snap.acceptance_criteria).lower()
        full = text + " " + ac_text
        catalog_idx = {c.code: c for c in WCAG_CATALOG}
        missing_codes: set[str] = set()
        for keywords, codes in _CHECKS:
            if any(kw in full for kw in keywords):
                for code in codes:
                    if code not in full:
                        missing_codes.add(code)
        issues = []
        for code in missing_codes:
            criterion = catalog_idx.get(code)
            if not criterion:
                continue
            issues.append(WCAGIssue(
                id=str(uuid.uuid4()), criterion=criterion,
                description=f"Critério {criterion.code} ({criterion.level.value}) não abordado: {criterion.description}",
                recommendation=_RECS.get(code, f"Endereçar critério WCAG {code}."),
                requirement_id=snap.id,
            ))
        return issues

    def _heuristic_nielsen(self, snap: RequirementSnapshot) -> List[HeuristicIssue]:
        text = f"{snap.title} {snap.description}".lower()
        ac_text = " ".join(f"{ac.given} {ac.when} {ac.then}" for ac in snap.acceptance_criteria).lower()
        issues = []
        for number, name, keywords in NIELSEN_HEURISTICS:
            if any(kw in text for kw in keywords) and not any(kw in ac_text for kw in keywords):
                found = [kw for kw in keywords if kw in text]
                issues.append(HeuristicIssue(
                    id=str(uuid.uuid4()), heuristic_number=number, heuristic_name=name,
                    description=f"Requisito menciona '{', '.join(found)}' mas não aborda heurística {number}: {name}.",
                    recommendation=f"Adicione critério de aceite abordando: {name}.",
                    requirement_id=snap.id,
                ))
        return issues

    def _llm_analyze(self, snap: RequirementSnapshot) -> List[WCAGIssue]:
        catalog_ctx = "\n".join(f"{c.code} ({c.level.value}): {c.description}" for c in WCAG_CATALOG)
        text = f"Requisito: {snap.title}\n{snap.description}\nCatálogo WCAG relevante:\n{catalog_ctx}"
        try:
            response = self._ai_acl.analyze_accessibility(text, context_id=snap.id)
            raw  = response.content.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
            data = json.loads(raw)
            catalog_idx = {c.code: c for c in WCAG_CATALOG}
            issues = []
            for item in data.get("wcag_issues", []):
                criterion = catalog_idx.get(item.get("code",""))
                if not criterion:
                    continue
                issues.append(WCAGIssue(
                    id=str(uuid.uuid4()), criterion=criterion,
                    description=item.get("description",""), recommendation=item.get("recommendation",""),
                    requirement_id=snap.id,
                ))
            return issues
        except Exception as exc:
            logger.error(f"[Accessibility] LLM falhou para {snap.id}: {exc}")
            return []
