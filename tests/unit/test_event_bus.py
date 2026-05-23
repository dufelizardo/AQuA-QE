import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from shared.event_bus import InProcessEventBus
from requirements.contracts.events import RequirementCreated, RequirementApproved
from tests.conftest import make_snapshot


class TestInProcessEventBus:
    def test_handler_called_on_publish(self):
        bus = InProcessEventBus()
        calls = []
        bus.subscribe(RequirementCreated, lambda e: calls.append(e))
        event = RequirementCreated(snapshot=make_snapshot(), session_id="s1")
        bus.publish(event)
        assert len(calls) == 1 and calls[0] is event

    def test_multiple_handlers_all_called(self):
        bus = InProcessEventBus()
        calls1, calls2 = [], []
        bus.subscribe(RequirementCreated, lambda e: calls1.append(e))
        bus.subscribe(RequirementCreated, lambda e: calls2.append(e))
        bus.publish(RequirementCreated(snapshot=make_snapshot(), session_id="s1"))
        assert len(calls1) == 1 and len(calls2) == 1

    def test_failing_handler_does_not_stop_others(self):
        bus = InProcessEventBus()
        calls = []

        def bad_handler(e):
            raise RuntimeError("boom")

        bus.subscribe(RequirementCreated, bad_handler)
        bus.subscribe(RequirementCreated, lambda e: calls.append(e))
        bus.publish(RequirementCreated(snapshot=make_snapshot(), session_id="s1"))
        assert len(calls) == 1

    def test_no_handler_no_error(self):
        bus = InProcessEventBus()
        bus.publish(RequirementCreated(snapshot=make_snapshot(), session_id="s1"))

    def test_handler_only_for_subscribed_type(self):
        bus = InProcessEventBus()
        calls = []
        bus.subscribe(RequirementCreated, lambda e: calls.append("created"))
        bus.subscribe(RequirementApproved, lambda e: calls.append("approved"))
        bus.publish(RequirementApproved(requirement_id="r1", project_id="p1", approved_by="u1"))
        assert calls == ["approved"]

    def test_no_cross_contamination_between_buses(self):
        bus1, bus2 = InProcessEventBus(), InProcessEventBus()
        calls1, calls2 = [], []
        bus1.subscribe(RequirementCreated, lambda e: calls1.append(e))
        bus2.subscribe(RequirementCreated, lambda e: calls2.append(e))
        bus1.publish(RequirementCreated(snapshot=make_snapshot(), session_id="s1"))
        assert len(calls1) == 1 and len(calls2) == 0
