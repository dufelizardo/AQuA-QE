import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import pytest, json
from unittest.mock import MagicMock
from tests.conftest import make_snapshot, MockAIGateway
from ai_gateway.acl import AIGatewayACL
from validation.domain.services import ValidationService
from validation.contracts import IssueSeverity, IssueType


def _make_val_service(ai_response: str = '{"issues": []}') -> ValidationService:
    mock_repo = MagicMock()
    mock_repo.save_report = MagicMock()
    return ValidationService(mock_repo, AIGatewayACL(MockAIGateway(ai_response)))


class TestHeuristicValidation:
    def test_detects_vague_term(self):
        svc  = _make_val_service()
        snap = make_snapshot(title="O sistema deve ser rápido e fácil de usar")
        dto  = svc.validate(snap)
        types = [i.issue_type.value for i in dto.issues]
        assert "AMBIGUITY" in types

    def test_rf_without_ac_is_critical(self):
        svc  = _make_val_service()
        snap = make_snapshot(acceptance_criteria=[])
        dto  = svc.validate(snap)
        assert dto.has_blockers()
        assert any(i.severity == IssueSeverity.CRITICAL for i in dto.issues)

    def test_empty_description_is_critical(self):
        svc  = _make_val_service()
        snap = make_snapshot(description="   ")
        dto  = svc.validate(snap)
        assert dto.has_blockers()

    def test_good_requirement_no_blockers(self):
        svc  = _make_val_service()
        snap = make_snapshot(
            title="Autenticar usuário com CPF e senha em até 2 segundos",
            description="O sistema valida as credenciais e estabelece sessão segura com token JWT.",
        )
        blockers = [i for i in svc.validate(snap).issues if i.severity == IssueSeverity.CRITICAL]
        assert len(blockers) == 0

    def test_llm_issues_merged_with_heuristic(self):
        llm_resp = json.dumps({"issues": [{
            "type": "INCONSISTENCY", "severity": "HIGH",
            "description": "Conflito com RN-005", "suggestion": "Revisar",
        }]})
        svc  = _make_val_service(llm_resp)
        snap = make_snapshot()
        dto  = svc.validate(snap)
        assert "INCONSISTENCY" in [i.issue_type.value for i in dto.issues]

    def test_report_has_blockers_returns_true_when_critical(self):
        svc  = _make_val_service()
        snap = make_snapshot(description="")
        dto  = svc.validate(snap)
        assert dto.has_blockers() is True

    def test_issue_count_by_severity(self):
        svc  = _make_val_service()
        snap = make_snapshot(description="")
        dto  = svc.validate(snap)
        counts = dto.issue_count_by_severity()
        assert counts[IssueSeverity.CRITICAL] >= 1
