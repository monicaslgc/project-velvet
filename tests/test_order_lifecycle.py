import pytest
from velvet.order_lifecycle import DecisionCode, OrderEvent, OrderStatus, evaluate_event

def event(**overrides):
    data = {"event_id":"evt-001", "order_id":"ord-001", "from_status":OrderStatus.CREATED, "to_status":OrderStatus.CONFIRMED, "expected_version":0}
    data.update(overrides)
    return OrderEvent(**data)

def test_allowed_transition_proposes_next_version_without_mutating_state():
    decision = evaluate_event(event(), current_status=OrderStatus.CREATED, current_version=0)
    assert decision.code == DecisionCode.ALLOWED
    assert decision.proposed_status == OrderStatus.CONFIRMED
    assert decision.proposed_version == 1

def test_duplicate_event_is_a_no_op():
    decision = evaluate_event(event(), current_status=OrderStatus.CREATED, current_version=0, previously_seen_event_ids={"evt-001"})
    assert decision.code == DecisionCode.DUPLICATE_EVENT
    assert decision.proposed_status is None

def test_stale_version_requires_review():
    decision = evaluate_event(event(expected_version=2), current_status=OrderStatus.CREATED, current_version=0)
    assert decision.code == DecisionCode.VERSION_CONFLICT
    assert decision.human_review_required is True

def test_source_status_must_match_authoritative_status():
    decision = evaluate_event(event(from_status=OrderStatus.CONFIRMED, to_status=OrderStatus.PROCESSING), current_status=OrderStatus.CREATED, current_version=0)
    assert decision.code == DecisionCode.BLOCKED_INVALID_TRANSITION

def test_terminal_status_cannot_transition():
    decision = evaluate_event(event(from_status=OrderStatus.DELIVERED, to_status=OrderStatus.PROCESSING), current_status=OrderStatus.DELIVERED, current_version=0)
    assert decision.code == DecisionCode.BLOCKED_INVALID_TRANSITION

@pytest.mark.parametrize("version", [-1, True, 1.5])
def test_invalid_expected_version_fails_closed(version):
    decision = evaluate_event(event(expected_version=version), current_status=OrderStatus.CREATED, current_version=0)
    assert decision.code == DecisionCode.INVALID_INPUT
    assert decision.human_review_required is True

def test_cancelled_order_is_terminal():
    decision = evaluate_event(event(from_status=OrderStatus.CANCELLED, to_status=OrderStatus.CONFIRMED), current_status=OrderStatus.CANCELLED, current_version=0)
    assert decision.code == DecisionCode.BLOCKED_INVALID_TRANSITION
