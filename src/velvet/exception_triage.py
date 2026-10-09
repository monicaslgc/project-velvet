"""Deterministic exception classification and routing for a synthetic portfolio demo."""
from __future__ import annotations
from dataclasses import dataclass
from enum import StrEnum
import math

class ExceptionCategory(StrEnum):
    PAYMENT_DELAY = "PAYMENT_DELAY"
    INVENTORY_MISMATCH = "INVENTORY_MISMATCH"
    SHIPMENT_DELAY = "SHIPMENT_DELAY"
    ADDRESS_VALIDATION = "ADDRESS_VALIDATION"

class Priority(StrEnum):
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"

@dataclass(frozen=True)
class OrderException:
    exception_id: str
    order_id: str
    category: str
    age_hours: float
    customer_impact: bool = False
    repeat_count: int = 1
    financial_risk: bool = False
    details: str = ""

@dataclass(frozen=True)
class TriageDecision:
    exception_id: str | None
    order_id: str | None
    category: str | None
    priority: Priority
    assigned_team: str
    recommended_action: str
    reasons: tuple[str, ...]
    human_review_required: bool
    valid: bool = True

ROUTING: dict[ExceptionCategory, tuple[str, str]] = {
    ExceptionCategory.PAYMENT_DELAY: ("payments_operations", "Check payment status and reconcile the provider reference before retrying."),
    ExceptionCategory.INVENTORY_MISMATCH: ("inventory_operations", "Compare reserved, available, and allocated quantities before changing stock."),
    ExceptionCategory.SHIPMENT_DELAY: ("fulfilment_operations", "Check the latest carrier milestone and whether the fulfilment SLA is breached."),
    ExceptionCategory.ADDRESS_VALIDATION: ("customer_operations", "Validate address data and request customer clarification if required."),
}

def triage_exception(exception: OrderException) -> TriageDecision:
    """Classify and route an exception without mutating orders or invoking external systems.

    P1: financial risk, 3+ occurrences, or customer impact at 24+ hours.
    P2: otherwise customer impact, age 12+ hours, or 2+ occurrences.
    P3: remaining valid exceptions. Unknown categories require manual review.
    """
    if (
        not isinstance(exception, OrderException)
        or not isinstance(exception.exception_id, str) or not exception.exception_id.strip()
        or not isinstance(exception.order_id, str) or not exception.order_id.strip()
        or not isinstance(exception.category, str) or not exception.category.strip()
        or not isinstance(exception.age_hours, (int, float))
        or isinstance(exception.age_hours, bool)
        or not math.isfinite(exception.age_hours)
        or exception.age_hours < 0
        or not isinstance(exception.repeat_count, int)
        or isinstance(exception.repeat_count, bool)
        or exception.repeat_count < 1
        or not isinstance(exception.customer_impact, bool)
        or not isinstance(exception.financial_risk, bool)
        or not isinstance(exception.details, str)
    ):
        return TriageDecision(
            getattr(exception, "exception_id", None), getattr(exception, "order_id", None),
            getattr(exception, "category", None), Priority.P1, "manual_review",
            "Verify the exception payload and source data before routing.",
            ("Required fields or values are invalid; automated routing is withheld.",),
            True, valid=False,
        )

    try:
        category = ExceptionCategory(exception.category)
    except ValueError:
        return TriageDecision(
            exception.exception_id, exception.order_id, exception.category,
            Priority.P1 if exception.financial_risk or exception.repeat_count >= 3 else Priority.P2,
            "manual_review", "Identify the exception type and confirm the correct owner before acting.",
            ("Unknown exception category; no category-specific action is safe to infer.",), True,
        )

    if exception.financial_risk or exception.repeat_count >= 3 or (
        exception.customer_impact and exception.age_hours >= 24
    ):
        priority = Priority.P1
    elif exception.customer_impact or exception.age_hours >= 12 or exception.repeat_count >= 2:
        priority = Priority.P2
    else:
        priority = Priority.P3

    team, action = ROUTING[category]
    reasons: list[str] = []
    if exception.financial_risk:
        reasons.append("Explicit financial risk is flagged.")
    if exception.repeat_count >= 3:
        reasons.append(f"Exception has occurred {exception.repeat_count} times.")
    if exception.customer_impact:
        reasons.append("Customer impact is flagged.")
    if exception.age_hours >= 24:
        reasons.append(f"Exception age is {exception.age_hours:g} hours (24-hour threshold).")
    elif exception.age_hours >= 12:
        reasons.append(f"Exception age is {exception.age_hours:g} hours (12-hour threshold).")
    if not reasons:
        reasons.append("No elevated-risk threshold was met; standard queue handling applies.")

    return TriageDecision(
        exception.exception_id, exception.order_id, category.value, priority, team, action,
        tuple(reasons), human_review_required=(priority == Priority.P1 or exception.financial_risk),
    )
