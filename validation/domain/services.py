from __future__ import annotations
import uuid, json, logging
from typing import List
from requirements.contracts.requirement_snapshot import RequirementSnapshot
from requirements.contracts.value_objects import RequirementType as _RT
from validation.contracts import IssueSeverity, IssueType, ValidationReportDTO
from validation.domain.entities import ValidationIssue, ValidationReport
from ai_gateway.acl import AIGatewayACL

logger = logging.getLogger(__name__)

_VAGUE_TERMS = [
    "rápido","fácil","simples","adequado","amigável","eficiente","intuitivo",
    "robusto","escalável","flexível","conveniente","suficiente","melhor","bom",
]


class ValidationService:
    def __init__(self, repo, ai_acl: AIGatewayACL) -> None:
        self._repo   = repo
        self._ai_acl = ai_acl

    def validate(self, snapshot: RequirementSnapshot) -> ValidationReportDTO:
        issues: List[ValidationIssue] = []
        issues.extend(self._check_vague_terms(snapshot))
        issues.extend(self._check_missing_ac(snapshot))
        issues.extend(self._check_empty_fields(snapshot))
        issues.extend(self._llm_analyze(snapshot))
        report = ValidationReport(
            id=str(uuid.uuid4()), requirement_id=snapshot.id,
            snapshot_version=str(snapshot.version), issues=issues,
        )
        self._repo.save_report(report)
        return report.to_dto()

    def get_report(self, report_id: str) -> ValidationReportDTO:
        report = self._repo.get_report(report_id)
        if not report:
            raise ValueError(f"Relatório {report_id} não encontrado")
        return report.to_dto()

    def _check_vague_terms(self, snap: RequirementSnapshot) -> List[ValidationIssue]:
        text  = f"{snap.title} {snap.description}".lower()
        found = [t for t in _VAGUE_TERMS if t in text]
        if not found:
            return []
        return [ValidationIssue(
            id=str(uuid.uuid4()), issue_type=IssueType.AMBIGUITY, severity=IssueSeverity.HIGH,
            description=f"Termos vagos encontrados: {', '.join(found)}",
            suggestion="Substitua por critérios mensuráveis. Ex: 'rápido' → 'resposta em até 2 segundos'.",
            location="title/description",
        )]

    def _check_missing_ac(self, snap: RequirementSnapshot) -> List[ValidationIssue]:
        from requirements.contracts.requirement_snapshot import RequirementSnapshot
        from requirements.domain.value_objects import RequirementType
        if snap.req_type == RequirementType.FUNCTIONAL and not snap.has_acceptance_criteria():
            return [ValidationIssue(
                id=str(uuid.uuid4()), issue_type=IssueType.COMPLETENESS, severity=IssueSeverity.CRITICAL,
                description="Requisito funcional sem critérios de aceite.",
                suggestion="Adicione ao menos um critério Given–When–Then.",
                location="acceptance_criteria",
            )]
        return []

    def _check_empty_fields(self, snap: RequirementSnapshot) -> List[ValidationIssue]:
        issues = []
        if not snap.description.strip():
            issues.append(ValidationIssue(
                id=str(uuid.uuid4()), issue_type=IssueType.COMPLETENESS, severity=IssueSeverity.CRITICAL,
                description="Campo 'description' está vazio.",
                suggestion="Descreva o comportamento esperado.",
                location="description",
            ))
        if len(snap.title.strip()) < 10:
            issues.append(ValidationIssue(
                id=str(uuid.uuid4()), issue_type=IssueType.COMPLETENESS, severity=IssueSeverity.MEDIUM,
                description="Título muito curto (menos de 10 caracteres).",
                suggestion="Use um título descritivo.",
                location="title",
            ))
        return issues

    def _llm_analyze(self, snap: RequirementSnapshot) -> List[ValidationIssue]:
        try:
            response = self._ai_acl.validate_requirement(snap, context_id=snap.id)
            raw  = response.content.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
            data = json.loads(raw)
            issues = []
            for item in data.get("issues", []):
                try:
                    issues.append(ValidationIssue(
                        id=str(uuid.uuid4()),
                        issue_type=IssueType(item["type"]),
                        severity=IssueSeverity(item["severity"]),
                        description=item["description"],
                        suggestion=item.get("suggestion",""),
                        location=item.get("location",""),
                    ))
                except (KeyError, ValueError) as e:
                    logger.warning(f"Issue LLM ignorada: {e} — {item}")
            return issues
        except Exception as exc:
            logger.error(f"LLM validation falhou para {snap.id}: {exc}")
            return []
