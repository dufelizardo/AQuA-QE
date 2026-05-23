from __future__ import annotations
import logging
from traceability.contracts import ArtifactRef, ArtifactType, LinkType, LinkCreated
from traceability.domain.services import TraceabilityService
from shared.event_bus import IEventBus

logger = logging.getLogger(__name__)


def make_traceability_handlers(service: TraceabilityService, bus: IEventBus):

    def _register(source: ArtifactRef, target: ArtifactRef, link_type: LinkType) -> None:
        try:
            dto = service.register_link(source, target, link_type)
            bus.publish(LinkCreated(link=dto))
        except Exception as exc:
            logger.error(f"[Traceability] Falha ao registrar link: {exc}")

    def on_requirement_created(event) -> None:
        snap    = event.snapshot
        req_ref = ArtifactRef(ArtifactType.REQUIREMENT, snap.id, str(snap.version))
        for ac in snap.acceptance_criteria:
            _register(req_ref, ArtifactRef(ArtifactType.ACCEPTANCE_CRITERIA, ac.id, "1.0"), LinkType.IMPLEMENTS)
        for br_id in snap.business_rule_ids:
            _register(req_ref, ArtifactRef(ArtifactType.BUSINESS_RULE, br_id, "1.0"), LinkType.IMPLEMENTS)
        logger.info(f"[Traceability] Links para {snap.id}: {len(snap.acceptance_criteria)} AC + {len(snap.business_rule_ids)} RN")

    def on_requirement_refined(event) -> None:
        snap    = event.snapshot
        new_ref = ArtifactRef(ArtifactType.REQUIREMENT, snap.id, str(snap.version))
        old_ref = ArtifactRef(ArtifactType.REQUIREMENT, snap.id, event.previous_version)
        _register(new_ref, old_ref, LinkType.SUPERSEDES)

    def on_test_suite_generated(event) -> None:
        for scenario in event.suite.scenarios:
            _register(
                ArtifactRef(ArtifactType.TEST_SCENARIO, scenario.id, "1.0"),
                ArtifactRef(ArtifactType.REQUIREMENT, scenario.requirement_id, "current"),
                LinkType.TESTS,
            )

    return on_requirement_created, on_requirement_refined, on_test_suite_generated
