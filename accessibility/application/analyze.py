from __future__ import annotations
from dataclasses import dataclass
import logging
from requirements.contracts.i_requirement_reader import IRequirementReader
from accessibility.contracts import ConformanceLevel, AccessibilityReportDTO, AccessibilityReportGenerated, WCAGViolationDetected, ConformanceLevelAchieved
from accessibility.domain.services import AccessibilityService
from shared.event_bus import IEventBus

logger = logging.getLogger(__name__)


@dataclass
class AnalyzeAccessibilityCommand:
    project_id:   str
    target_level: ConformanceLevel = ConformanceLevel.AA


class AnalyzeAccessibilityUseCase:
    def __init__(self, service: AccessibilityService, reader: IRequirementReader, bus: IEventBus) -> None:
        self._service = service
        self._reader  = reader
        self._bus     = bus

    def execute(self, cmd: AnalyzeAccessibilityCommand) -> AccessibilityReportDTO:
        snapshots = list(self._reader.get_project_snapshots(cmd.project_id, approved_only=True))
        report = self._service.analyze(snapshots, cmd.target_level)
        self._bus.publish(AccessibilityReportGenerated(report=report, project_id=cmd.project_id))
        for issue in report.wcag_issues:
            if not issue.resolved:
                self._bus.publish(WCAGViolationDetected(requirement_id=issue.requirement_id, issue=issue))
        self._bus.publish(ConformanceLevelAchieved(project_id=cmd.project_id, level=report.conformance_level_achieved))
        logger.info(f"[Accessibility] {cmd.project_id}: nível {report.conformance_level_achieved.value}")
        return report
