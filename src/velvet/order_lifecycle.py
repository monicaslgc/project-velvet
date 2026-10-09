"""Deterministic order-event policy for synthetic portfolio demonstrations."""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Iterable


class OrderStatus(StrEnum):
    CREATED = "CREATED"
    CONFIRMED = "CONFIRMED"
    PROCESSING = "PROCESSING"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


class DecisionCode(StrEnum):
    ALLOWED = "ALLOWED"
    INVALID_INPUT = "INVALID_INPUT"
    DUPLICATE_EVENT = "DUPLICATE_EVENT"
    VERSION_CONFLICT = "VERSION_CONFLICT"
    BLOCKED_INVALID_TRANSITION = "BLOCKED_INVALID_TRANSITION"


ALLOWED_TRANSITIONS: dict[OrderStatus, frozenset[OrderStatus]] = {
    OrderStatus.CREATED: frozenset({OrderStatus.CONFIRMED, OrderStatus.CANCELLED}),
    OrderStatus.CONFIRMED: frozenset({OrderStatus.PROCESSING, OrderStatus.CANCELLED}),
    OrderStatus.PROCESSING: frozenset({OrderStatus.SHIPPED, OrderStatus.CANCELLED}),
    OrderStatus.SHIPPED: frozenset({OrderStatus.DELIVERED}),
    OrderStatus.DELIVERED: frozenset(),
    OrderStatus.CANCELLED: frozenset(),
}


@dataclass(frozen=True)
class OrderEvent:
    event_id: str
    order_id: str
    from_status: OrderStatus
    to_status: OrderStatus
    expected_version: int


@dataclass(frozen=True)
class Decision:
    code: DecisionCode
    event_id: str | None
    order_id: str | None
    reason: str
    proposed_status: OrderStatus | None = None
    proposed_version: int | None = None
    human_review_required: bool = False


def evaluate_event(
    event: OrderEvent,
    *,
    current_status: OrderStatus,
    current_version: int,
    previously_seen_event_ids: Iterable[str] = (),
) -> Decision:
    """Evaluate one event without mutating state or performing external side effects."""
    if (
        not isinstance(event, OrderEvent)
        or not isinstance(event.event_id, str) or not event.event_id.strip()
        or not isinstance(event.order_id, str) or not event.order_id.strip()
        or not isinstance(event.from_status, OrderStatus)
        or not isinstance(event.to_status, OrderStatus)
        or not isinstance(event.expected_version, int)
        or isinstance(event.expected_version, bool)
        or event.expected_version < 0
        or not isinstance(current_version, int)
        or isinstance(current_version, bool)
        or current_version < 0
        or not isinstance(current_status, OrderStatus)
    ):
        return Decision(DecisionCode.INVALID_INPUT, getattr(event, "event_id", None), getattr(event, "order_id", None), "Required identifiers, statuses, or version values are invalid.", human_review_required=True)

    if event.event_id in set(previously_seen_event_ids):
        return Decision(DecisionCode.DUPLICATE_EVENT, event.event_id, event.order_id, "The event ID has already been seen in the supplied evaluation context.")

    if event.expected_version != current_version:
        return Decision(DecisionCode.VERSION_CONFLICT, event.event_id, event.order_id, f"Expected version {event.expected_version}, but current version is {current_version}.", human_review_required=True)

    if event.from_status != current_status:
        return Decision(DecisionCode.BLOCKED_INVALID_TRANSITION, event.event_id, event.order_id, f"Event source status {event.from_status} does not match current status {current_status}.")

    if event.to_status not in ALLOWED_TRANSITIONS[event.from_status]:
        return Decision(DecisionCode.BLOCKED_INVALID_TRANSITION, event.event_id, event.order_id, f"Transition {event.from_status} -> {event.to_status} is not allowed.")

    return Decision(DecisionCode.ALLOWED, event.event_id, event.order_id, "Event satisfies the transition policy.", proposed_status=event.to_status, proposed_version=current_version + 1)
