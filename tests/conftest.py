import pytest, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault("ANTHROPIC_API_KEY", "mock")
os.environ.setdefault("OPENAI_API_KEY", "mock")

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from persistence.base import Base, get_session, create_all_tables
from shared.event_bus import InProcessEventBus
from requirements.domain.value_objects import RequirementType, Priority, RequirementStatus, QualityScore, RequirementVersion
from requirements.domain.entities import Requirement, Project, AcceptanceCriteria
from requirements.contracts.requirement_snapshot import RequirementSnapshot, AcceptanceCriteriaSnapshot
from datetime import datetime
import uuid, json


@pytest.fixture(scope="session")
def engine():
    eng = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    create_all_tables(eng)
    yield eng
    eng.dispose()


@pytest.fixture
def session(engine):
    factory = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    s = factory()
    yield s
    s.rollback()
    s.close()


@pytest.fixture
def bus():
    return InProcessEventBus()


class MockAIGateway:
    def __init__(self, response_content: str = "") -> None:
        self.response_content = response_content or self._default()
        self.calls = []

    def _default(self) -> str:
        return json.dumps({
            "requirements": [{
                "title": "O sistema deve permitir login",
                "description": "Autenticação com e-mail e senha",
                "type": "RF", "priority": "MUST",
                "scores": {"clarity": 80.0, "completeness": 75.0, "testability": 85.0, "consistency": 78.0},
                "acceptance_criteria": [{
                    "description": "Login válido",
                    "given": "conta ativa", "when": "credenciais corretas", "then": "autenticado",
                }],
            }],
            "gaps": ["Ausência de recuperação de senha"],
            "issues": [], "wcag_issues": [],
        })

    def complete(self, request):
        self.calls.append(request)
        from ai_gateway.contracts import PromptResponse, ModelProvider
        return PromptResponse(
            content=self.response_content, provider_used=ModelProvider.LOCAL,
            model_used="mock", tokens_in=100, tokens_out=200, latency_ms=10,
        )

    async def complete_async(self, request):
        return self.complete(request)


@pytest.fixture
def mock_ai():
    return MockAIGateway()


@pytest.fixture
def mock_ai_acl(mock_ai):
    from ai_gateway.acl import AIGatewayACL
    return AIGatewayACL(mock_ai)


def make_quality_score(**kwargs) -> QualityScore:
    defaults = dict(clarity=80.0, completeness=75.0, testability=85.0, consistency=78.0)
    return QualityScore(**{**defaults, **kwargs})


def make_requirement(**kwargs) -> Requirement:
    defaults = dict(
        id=str(uuid.uuid4()), project_id=str(uuid.uuid4()), session_id=None,
        title="O sistema deve permitir login",
        description="Autenticação com e-mail e senha válidos",
        req_type=RequirementType.FUNCTIONAL, priority=Priority.MUST,
        status=RequirementStatus.DRAFT,
        version=RequirementVersion(1, 0, "Criação"),
        quality_score=make_quality_score(),
        acceptance_criteria=[],
    )
    return Requirement(**{**defaults, **kwargs})


def make_snapshot(req: Requirement = None, **kwargs) -> RequirementSnapshot:
    r = req or make_requirement()
    defaults = dict(
        id=r.id, project_id=r.project_id, title=r.title, description=r.description,
        req_type=r.req_type, priority=r.priority, version=r.version, quality_score=r.quality_score,
        acceptance_criteria=[
            AcceptanceCriteriaSnapshot(
                id="ac-1", description="Login válido",
                given="conta ativa", when="credenciais corretas", then="autenticado",
            )
        ],
        business_rule_ids=[], snapshotted_at=datetime.utcnow(),
    )
    return RequirementSnapshot(**{**defaults, **kwargs})


@pytest.fixture
def client(session):
    from main import app
    app.dependency_overrides[get_session] = lambda: session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def client(session):
    import api.requirements.router as req_router_module
    original = req_router_module._get_session

    def override():
        yield session

    req_router_module._get_session = override
    from main import app
    with TestClient(app) as c:
        yield c
    req_router_module._get_session = original
