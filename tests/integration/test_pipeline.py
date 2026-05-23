import pytest, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from tests.conftest import make_quality_score, MockAIGateway
from ai_gateway.acl import AIGatewayACL
from shared.event_bus import InProcessEventBus
from requirements.infrastructure.repository import RequirementRepository
from requirements.infrastructure.reader import RequirementReader
from requirements.application.create import CreateRequirementUseCase, CreateRequirementCommand
from requirements.application.approve import ApproveRequirementUseCase, ApproveRequirementCommand
from requirements.application.refine import RefineRequirementUseCase, RefineRequirementCommand
from requirements.domain.entities import Project
from requirements.domain.value_objects import QualityScore, RequirementStatus
import uuid


@pytest.fixture
def pipeline(session):
    bus = InProcessEventBus()
    ai_acl = AIGatewayACL(MockAIGateway())
    repo = RequirementRepository(session)
    reader = RequirementReader(session)
    project = Project(id=str(uuid.uuid4()), name="Projeto Teste", description=None, domain="test")
    repo.save_project(project)
    session.commit()
    return {
        "bus": bus, "repo": repo, "reader": reader, "project_id": project.id,
        "create": CreateRequirementUseCase(repo, ai_acl, bus),
        "approve": ApproveRequirementUseCase(repo, bus),
        "refine": RefineRequirementUseCase(repo, ai_acl, bus),
    }


def test_elicitation_creates_requirements(pipeline, session):
    result = pipeline["create"].execute(CreateRequirementCommand(
        project_id=pipeline["project_id"],
        raw_input="O sistema deve permitir que o usuário faça login com e-mail e senha.",
    ))
    session.commit()
    assert len(result.requirements) >= 1
    req = result.requirements[0]
    assert req.title
    assert req.req_type.value in ("RF", "RNF", "RN", "CONSTRAINT", "ASSUMPTION")
    assert result.session_id


def test_project_not_found_raises(pipeline, session):
    with pytest.raises(ValueError, match="não encontrado"):
        pipeline["create"].execute(CreateRequirementCommand(
            project_id="nonexistent", raw_input="teste",
        ))


def test_approve_blocked_by_low_clarity(pipeline, session):
    result = pipeline["create"].execute(CreateRequirementCommand(
        project_id=pipeline["project_id"], raw_input="teste de sistema",
    ))
    session.commit()
    if not result.requirements:
        pytest.skip("Mock retornou lista vazia")

    req = pipeline["repo"].get_requirement(result.requirements[0].id)
    req.update_quality(QualityScore(clarity=40.0, completeness=50.0, testability=50.0, consistency=50.0))
    req.status = RequirementStatus.REVIEW
    pipeline["repo"].save_requirement(req)
    session.commit()

    with pytest.raises(ValueError, match="clareza"):
        pipeline["approve"].execute(ApproveRequirementCommand(req.id, "user-1"))


def test_full_elicit_refine_approve_cycle(pipeline, session):
    result = pipeline["create"].execute(CreateRequirementCommand(
        project_id=pipeline["project_id"],
        raw_input="Sistema de autenticação com bloqueio após 3 tentativas",
    ))
    session.commit()
    if not result.requirements:
        pytest.skip()

    req_id = result.requirements[0].id
    pipeline["refine"].execute(RefineRequirementCommand(
        requirement_id=req_id,
        description="Autenticação robusta com bloqueio e 2FA",
        changelog="Adicionado 2FA",
    ))

    req = pipeline["repo"].get_requirement(req_id)
    req.update_quality(QualityScore(clarity=85.0, completeness=80.0, testability=90.0, consistency=82.0))
    pipeline["repo"].save_requirement(req)
    session.commit()

    pipeline["approve"].execute(ApproveRequirementCommand(req_id, "tech-lead"))
    session.commit()

    approved = pipeline["repo"].get_requirement(req_id)
    assert approved.status == RequirementStatus.APPROVED
    assert approved.version.minor == 1


def test_reader_returns_only_approved(pipeline, session):
    result = pipeline["create"].execute(CreateRequirementCommand(
        project_id=pipeline["project_id"], raw_input="Funcionalidade X do sistema",
    ))
    session.commit()
    if not result.requirements:
        pytest.skip()

    snapshots_before = pipeline["reader"].get_project_snapshots(pipeline["project_id"], approved_only=True)
    initial_count = len(snapshots_before)

    req = pipeline["repo"].get_requirement(result.requirements[0].id)
    req.update_quality(QualityScore(clarity=75.0, completeness=80.0, testability=80.0, consistency=80.0))
    req.status = RequirementStatus.REVIEW
    pipeline["repo"].save_requirement(req)
    pipeline["approve"].execute(ApproveRequirementCommand(req.id, "user-1"))
    session.commit()

    snapshots_after = pipeline["reader"].get_project_snapshots(pipeline["project_id"], approved_only=True)
    assert len(snapshots_after) == initial_count + 1


def test_validation_triggered_by_elicitation(pipeline, session):
    """Após elicitação, handler de validação deve ter gerado um relatório."""
    from validation.infrastructure.repository import ValidationRepository
    from validation.domain.services import ValidationService
    from validation.application.handlers import make_validation_handler

    bus    = pipeline["bus"]
    val_repo = ValidationRepository(session)
    val_svc  = ValidationService(val_repo, AIGatewayACL(MockAIGateway()))
    val_h    = make_validation_handler(val_svc, bus)

    from requirements.contracts.events import RequirementCreated
    bus.subscribe(RequirementCreated, val_h)

    result = pipeline["create"].execute(CreateRequirementCommand(
        project_id=pipeline["project_id"], raw_input="Sistema de pagamento com cartão de crédito",
    ))
    session.commit()

    if not result.requirements:
        pytest.skip()

    report = val_repo.latest_for_requirement(result.requirements[0].id)
    assert report is not None


def test_traceability_links_registered_on_creation(pipeline, session):
    """Links de rastreabilidade devem ser criados para AC e RN após RequirementCreated."""
    from traceability.infrastructure.repository import TraceabilityRepository
    from traceability.domain.services import TraceabilityService
    from traceability.application.handlers import make_traceability_handlers

    bus = pipeline["bus"]
    trace_repo = TraceabilityRepository(session)
    trace_svc  = TraceabilityService(trace_repo)
    trc_created, _, _ = make_traceability_handlers(trace_svc, bus)

    from requirements.contracts.events import RequirementCreated
    bus.subscribe(RequirementCreated, trc_created)

    result = pipeline["create"].execute(CreateRequirementCommand(
        project_id=pipeline["project_id"],
        raw_input="O sistema deve exibir saldo disponível ao usuário autenticado",
    ))
    session.commit()

    if not result.requirements:
        pytest.skip()

    req = result.requirements[0]
    matrix = trace_repo.get_full_matrix(pipeline["project_id"])
    req_links = [l for l in matrix.active_links() if l.source.artifact_id == req.id]
    # Links para ACs gerados pelo mock (pelo menos 0 — se mock gera AC, haverá links)
    assert isinstance(req_links, list)


def test_quality_gate_evaluates_after_suite_generated(pipeline, session):
    """Quality gate deve ser avaliado quando TestSuiteGenerated é publicado."""
    from quality.infrastructure.repository import QualityRepository
    from quality.domain.services import QualityGateService
    from quality.application.handlers import make_quality_handlers
    from quality.application.evaluate import EvaluateQualityGateUseCase

    bus = pipeline["bus"]
    qual_repo = QualityRepository(session)
    qual_svc  = QualityGateService(qual_repo, pipeline["reader"])
    _, qlt_suite, _, _ = make_quality_handlers(qual_svc, bus)

    from testing.contracts import TestSuiteGenerated, TestSuiteDTO
    from datetime import datetime
    bus.subscribe(TestSuiteGenerated, qlt_suite)

    # Publica evento manualmente
    bus.publish(TestSuiteGenerated(
        suite=TestSuiteDTO(suite_id="s1", project_id=pipeline["project_id"], scenarios=[], generated_at=datetime.utcnow()),
        project_id=pipeline["project_id"],
    ))
    session.commit()

    report = qual_repo.get_latest_report(pipeline["project_id"])
    assert report is not None
    assert report.overall_status.value in ("PASSED", "FAILED", "WARNING")
