from __future__ import annotations
from dataclasses import dataclass
from typing import Sequence
import logging
from requirements.contracts.requirement_snapshot import RequirementSnapshot
from testing.contracts import TestSuiteDTO, TestSuiteGenerated, AutomationCandidateIdentified, TestType
from testing.domain.services import TestGenerationService
from shared.event_bus import IEventBus

logger = logging.getLogger(__name__)


@dataclass
class GenerateTestSuiteCommand:
    project_id: str
    snapshots:  Sequence[RequirementSnapshot] | None = None


class GenerateTestSuiteUseCase:
    def __init__(self, service: TestGenerationService, bus: IEventBus) -> None:
        self._service = service
        self._bus = bus

    def execute(self, cmd: GenerateTestSuiteCommand) -> TestSuiteDTO:
        suite_dto = (
            self._service.generate_suite(list(cmd.snapshots))
            if cmd.snapshots
            else self._service.generate_suite_for_project(cmd.project_id)
        )
        self._bus.publish(TestSuiteGenerated(suite=suite_dto, project_id=cmd.project_id))
        for s in suite_dto.scenarios:
            if s.automation_candidate:
                self._bus.publish(AutomationCandidateIdentified(
                    scenario_id=s.id,
                    strategy=s.automation_strategy or "não definida",
                    suggested_framework=self._suggest_framework(s.test_type),
                ))
        logger.info(f"[Testing] Suite para {cmd.project_id}: {len(suite_dto.scenarios)} cenários")
        return suite_dto

    def _suggest_framework(self, test_type: TestType) -> str:
        return {
            TestType.FUNCTIONAL:    "pytest + requests",
            TestType.NEGATIVE:      "pytest + requests",
            TestType.ACCESSIBILITY: "axe-core + playwright",
            TestType.INTEGRATION:   "pytest + testcontainers",
            TestType.UNIT:          "pytest",
        }.get(test_type, "pytest")
