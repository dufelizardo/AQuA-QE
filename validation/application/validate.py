from __future__ import annotations
from dataclasses import dataclass
import logging
from requirements.contracts.requirement_snapshot import RequirementSnapshot
from validation.contracts import (
    ValidationReportDTO, ValidationCompleted, CriticalIssueDetected,
    RequirementBlockedByValidation, IssueSeverity,
)
from validation.domain.services import ValidationService
from shared.event_bus import IEventBus

logger = logging.getLogger(__name__)


@dataclass
class ValidateRequirementCommand:
    snapshot: RequirementSnapshot


class ValidateRequirementUseCase:
    def __init__(self, service: ValidationService, bus: IEventBus) -> None:
        self._service = service
        self._bus = bus

    def execute(self, cmd: ValidateRequirementCommand) -> ValidationReportDTO:
        report = self._service.validate(cmd.snapshot)
        self._bus.publish(ValidationCompleted(
            report=report, requirement_id=report.requirement_id, has_blockers=report.has_blockers(),
        ))
        for issue in report.issues:
            if issue.severity == IssueSeverity.CRITICAL:
                self._bus.publish(CriticalIssueDetected(requirement_id=report.requirement_id, issue=issue))
        if report.has_blockers():
            self._bus.publish(RequirementBlockedByValidation(
                requirement_id=report.requirement_id,
                blocker_count=report.issue_count_by_severity()[IssueSeverity.CRITICAL],
            ))
        logger.info(f"[Validation] {report.requirement_id}: {len(report.issues)} issue(s), blockers={report.has_blockers()}")
        return report
