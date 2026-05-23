from __future__ import annotations
import logging
from knowledge.acl import KnowledgeACL
from requirements.contracts.i_requirement_reader import IRequirementReader

logger = logging.getLogger(__name__)


def make_knowledge_handlers(acl: KnowledgeACL, reader: IRequirementReader):

    def on_requirement_approved_learn(event) -> None:
        try:
            snapshot = reader.get_snapshot(event.requirement_id)
            acl.learn_from_requirement(snapshot, domain="default")
        except Exception as exc:
            logger.warning(f"[Knowledge] learn_from_requirement falhou: {exc}")

    def on_test_suite_learn(event) -> None:
        try:
            for scenario in event.suite.scenarios:
                acl.learn_from_test_scenario(scenario, domain="default")
        except Exception as exc:
            logger.warning(f"[Knowledge] learn_from_test_scenario falhou: {exc}")

    return on_requirement_approved_learn, on_test_suite_learn
