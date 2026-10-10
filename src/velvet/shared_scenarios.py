"""Run shared synthetic scenarios through the existing deterministic demo policies."""
from __future__ import annotations

from typing import Any

from .exception_triage import OrderException, triage_exception
from .order_lifecycle import DecisionCode, OrderEvent, OrderStatus, evaluate_event
from .order_reconciliation import OrderSnapshot, reconcile_orders
from .workflow_governance import ProposedAction, evaluate_action


def evaluate_shared_pack(data: dict[str, Any]) -> list[dict[str, str]]:
    """Evaluate lifecycle, triage, reconciliation, and governance records read-only.

    The caller is responsible for validating the pack first. No source records are
    mutated and no proposed action is executed.
    """
    results: list[dict[str, str]] = []

    for record in data.get("lifecycle_events", []):
        current = OrderStatus(record["current_status"])
        event = OrderEvent(
            event_id=record["event_id"],
            order_id=record["order_id"],
            from_status=OrderStatus(record["from_status"]),
            to_status=OrderStatus(record["to_status"]),
            expected_version=record["expected_version"],
        )
        decision = evaluate_event(
            event,
            current_status=current,
            current_version=record["current_version"],
            previously_seen_event_ids=record.get("previously_seen_event_ids", []),
        )
        results.append({
            "scenario_id": record["scenario_id"],
            "demo": "lifecycle",
            "record_id": record["event_id"],
            "decision": decision.code.value,
            "detail": decision.reason,
        })

    for record in data.get("exceptions", []):
        decision = triage_exception(OrderException(
            exception_id=record["exception_id"],
            order_id=record["order_id"],
            category=record["category"],
            age_hours=record["age_hours"],
            customer_impact=record["customer_impact"],
            repeat_count=record["repeat_count"],
            financial_risk=record["financial_risk"],
            details=record["details"],
        ))
        results.append({
            "scenario_id": record["scenario_id"],
            "demo": "triage",
            "record_id": record["exception_id"],
            "decision": decision.priority.value,
            "detail": f"team={decision.assigned_team}; review_required={decision.human_review_required}; valid={decision.valid}",
        })

    for record in data.get("snapshot_pairs", []):
        decision = reconcile_orders(
            OrderSnapshot(**record["expected"]),
            OrderSnapshot(**record["observed"]),
        )
        fields = ",".join(item.field for item in decision.discrepancies) or "none"
        results.append({
            "scenario_id": record["scenario_id"],
            "demo": "reconciliation",
            "record_id": record["order_id"],
            "decision": "MATCHED" if decision.matched else "REVIEW" if decision.human_review_required else "DISCREPANCY",
            "detail": f"valid={decision.valid}; fields={fields}",
        })

    for record in data.get("proposed_actions", []):
        decision = evaluate_action(ProposedAction(
            action_id=record["action_id"],
            action_type=record["action_type"],
            requested_by=record["requested_by"],
            description=record["description"],
        ))
        results.append({
            "scenario_id": record["scenario_id"],
            "demo": "governance",
            "record_id": record["action_id"],
            "decision": decision.outcome.value,
            "detail": f"allowed_to_execute={decision.allowed_to_execute}; approval_required={decision.approval_required}; valid={decision.valid}",
        })

    return results
