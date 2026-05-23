from __future__ import annotations
from sqlalchemy.orm import Session
from shared.event_bus import InProcessEventBus, IEventBus

from ai_gateway.infrastructure.router import AIGatewayRouter
from ai_gateway.acl import AIGatewayACL

from knowledge.infrastructure.repository import KnowledgeRepository
from knowledge.domain.services import KnowledgeService
from knowledge.acl import KnowledgeACL
from knowledge.application.handlers import make_knowledge_handlers

from requirements.infrastructure.repository import RequirementRepository
from requirements.infrastructure.reader import RequirementReader
from requirements.application.create import CreateRequirementUseCase
from requirements.application.refine import RefineRequirementUseCase
from requirements.application.approve import ApproveRequirementUseCase, BulkApproveUseCase

from validation.infrastructure.repository import ValidationRepository
from validation.domain.services import ValidationService
from validation.application.handlers import make_validation_handler

from testing.infrastructure.repository import TestRepository
from testing.domain.services import TestGenerationService
from testing.application.handlers import make_testing_handler

from traceability.infrastructure.repository import TraceabilityRepository
from traceability.domain.services import TraceabilityService
from traceability.application.handlers import make_traceability_handlers

from accessibility.infrastructure.repository import AccessibilityRepository
from accessibility.domain.services import AccessibilityService
from accessibility.application.handlers import make_accessibility_handler

from quality.infrastructure.repository import QualityRepository
from quality.domain.services import QualityGateService
from quality.application.evaluate import EvaluateQualityGateUseCase
from quality.application.handlers import make_quality_handlers

from requirements.contracts.events import RequirementCreated, RequirementRefined, RequirementApproved
from testing.contracts import TestSuiteGenerated, CoverageGapDetected
from validation.contracts import ValidationCompleted
from accessibility.contracts import AccessibilityReportGenerated

_ai_router = AIGatewayRouter()


class Container:
    """Container de dependências completo — todos os bounded contexts conectados."""

    def __init__(self, session: Session) -> None:
        bus: IEventBus = InProcessEventBus()

        ai_acl        = AIGatewayACL(_ai_router)
        knowledge_acl = KnowledgeACL(KnowledgeService(KnowledgeRepository(session)))
        req_repo      = RequirementRepository(session)
        req_reader    = RequirementReader(session)
        val_svc       = ValidationService(ValidationRepository(session), ai_acl)
        test_svc      = TestGenerationService(TestRepository(session), req_reader, ai_acl)
        trace_svc     = TraceabilityService(TraceabilityRepository(session))
        acc_svc       = AccessibilityService(AccessibilityRepository(session), req_reader, ai_acl)
        qual_svc      = QualityGateService(QualityRepository(session), req_reader)

        # ── Use cases públicos ─────────────────────────────────────
        self.create_requirement  = CreateRequirementUseCase(req_repo, ai_acl, bus)
        self.refine_requirement  = RefineRequirementUseCase(req_repo, ai_acl, bus)
        self.approve_requirement = ApproveRequirementUseCase(req_repo, bus)
        self.bulk_approve        = BulkApproveUseCase(req_repo, bus)
        self.evaluate_quality    = EvaluateQualityGateUseCase(qual_svc, bus)
        self.req_reader          = req_reader
        self.trace_svc           = trace_svc
        self.qual_svc            = qual_svc

        # ── Handlers ──────────────────────────────────────────────
        val_h                           = make_validation_handler(val_svc, bus)
        trc_created, trc_refined, trc_suite = make_traceability_handlers(trace_svc, bus)
        tst_h                           = make_testing_handler(test_svc, req_reader, bus)
        acc_h                           = make_accessibility_handler(acc_svc, req_reader, bus)
        qlt_val, qlt_suite, qlt_acc, qlt_cov = make_quality_handlers(qual_svc, bus)
        knw_req, knw_tst                = make_knowledge_handlers(knowledge_acl, req_reader)

        # ── Subscrições ────────────────────────────────────────────
        bus.subscribe(RequirementCreated,            val_h)
        bus.subscribe(RequirementRefined,            val_h)
        bus.subscribe(RequirementCreated,            trc_created)
        bus.subscribe(RequirementRefined,            trc_refined)
        bus.subscribe(RequirementApproved,           tst_h)
        bus.subscribe(RequirementApproved,           acc_h)
        bus.subscribe(RequirementApproved,           knw_req)
        bus.subscribe(TestSuiteGenerated,            trc_suite)
        bus.subscribe(TestSuiteGenerated,            qlt_suite)
        bus.subscribe(TestSuiteGenerated,            knw_tst)
        bus.subscribe(ValidationCompleted,           qlt_val)
        bus.subscribe(AccessibilityReportGenerated,  qlt_acc)
        bus.subscribe(CoverageGapDetected,           qlt_cov)
