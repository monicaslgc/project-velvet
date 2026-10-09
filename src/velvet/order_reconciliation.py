""""Compare order snapshots and report discrepancies without changing source data."""
from __future__ import annotations
from dataclasses import dataclass
from enum import StrEnum

class DiscrepancySeverity(StrEnum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

@dataclass(frozen=True)
class OrderSnapshot:
    order_id: str
    status: str
    total_minor_units: int
    currency: str
    item_count: int
    source: str

@dataclass(frozen=True)
class Discrepancy:
    field: str
    expected_value: str | int
    observed_value: str | int
    severity: DiscrepancySeverity
    reason: str

@dataclass(frozen=True)
class ReconciliationResult:
    order_id: str | None
    matched: bool
    discrepancies: tuple[Discrepancy, ...]
    human_review_required: bool
    valid: bool = True
    reason: str = ""

FIELD_POLICY = {
    "status": (DiscrepancySeverity.HIGH, "Order lifecycle states disagree between sources."),
    "total_minor_units": (DiscrepancySeverity.HIGH, "Order totals disagree; monetary values must be reconciled before financial action."),
    "currency": (DiscrepancySeverity.HIGH, "Currency differs between sources; do not compare totals as equivalent."),
    "item_count": (DiscrepancySeverity.MEDIUM, "Item counts disagree between sources."),
}

def reconcile_orders(expected: OrderSnapshot, observed: OrderSnapshot) -> ReconciliationResult:
    """Compare two snapshots; never infer which source is authoritative or repair data."""
    if not isinstance(expected, OrderSnapshot) or not isinstance(observed, OrderSnapshot):
        return ReconciliationResult(None, False, (), True, False, "Both inputs must be OrderSnapshot values.")
    for snapshot in (expected, observed):
        if (not isinstance(snapshot.order_id, str) or not snapshot.order_id.strip()
            or not isinstance(snapshot.status, str) or not snapshot.status.strip()
            or not isinstance(snapshot.currency, str) or len(snapshot.currency.strip()) != 3
            or not isinstance(snapshot.source, str) or not snapshot.source.strip()
            or not isinstance(snapshot.total_minor_units, int) or isinstance(snapshot.total_minor_units, bool) or snapshot.total_minor_units < 0
            or not isinstance(snapshot.item_count, int) or isinstance(snapshot.item_count, bool) or snapshot.item_count < 0):
            return ReconciliationResult(snapshot.order_id if isinstance(snapshot.order_id, str) else None, False, (), True, False, "Snapshot contains invalid required fields.")
    if expected.order_id != observed.order_id:
        return ReconciliationResult(None, False, (), True, False, "Order IDs differ; comparing snapshots is unsafe.")
    discrepancies = []
    for field, (severity, reason) in FIELD_POLICY.items():
        left, right = getattr(expected, field), getattr(observed, field)
        if left != right:
            discrepancies.append(Discrepancy(field, left, right, severity, reason))
    return ReconciliationResult(
        order_id=expected.order_id,
        matched=not discrepancies,
        discrepancies=tuple(discrepancies),
        human_review_required=any(d.severity == DiscrepancySeverity.HIGH for d in discrepancies),
        reason="Snapshots match on all checked fields." if not discrepancies else f"Found {len(discrepancies)} discrepancy field(s); no source was changed.",
    )
