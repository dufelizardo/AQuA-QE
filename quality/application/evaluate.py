from __future__ import annotations
from dataclasses import dataclass
import logging
from quality.contracts import QualityReportDTO, QualityGatePassed, QualityGateFailed, GateStatus, PolicyViolationDetected, PolicyRule
from quality.domain.services import QualityGateService
from shared.event_bus import IEventBus

logger = logging.getLogger(__name__)


@dataclass
class EvaluateQualityGateCommand:
    project_id: str


class EvaluateQualityGateUseCase:
    def __init__(self, service: QualityGateService, bus: IEventBus) -> None:
        self._service = service
        self._bus = bus

    def execute(self, cmd: EvaluateQualityGateCommand) -> QualityReportDTO:
        report = self._service.evaluate(cmd.project_id)
        if report.is_approved():
            self._bus.publish(QualityGatePassed(report=report, project_id=cmd.project_id))
        else:
            self._bus.publish(QualityGateFailed(
                report=report, project_id=cmd.project_id,
                blocking_violations=tuple(v for v in report.policy_violations if "BLOQUEANTE" in v),
            ))
        for dim in report.dimension_scores:
            if dim.status == GateStatus.FAILED:
                self._bus.publish(PolicyViolationDetected(
                    project_id=cmd.project_id, rule=PolicyRule(dim.dimension, 0.0, True), actual_score=dim.score,
                ))
        return report
