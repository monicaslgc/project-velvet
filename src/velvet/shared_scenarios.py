"""Run shared synthetic scenarios through deterministic demo policies."""
from __future__ import annotations

from typing import Any

from .exception_triage import OrderException, triage_exception
from .order_lifecycle import OrderEvent, OrderStatus, evaluate_event
from .order_reconciliation import OrderSnapshot, reconcile_orders
from .workflow_governance import ProposedAction, evaluate_action
from .operational_orchestrator import (
    OperationalWorkflowInput, run_operational_workflow,
)
from .policy_impact import compare_policy_snapshots


def _exception(record: dict[str, Any]) -> OrderException:
    return OrderException(
        exception_id=record["exception_id"], order_id=record["order_id"],
        category=record["category"], age_hours=record["age_hours"],
        customer_impact=record["customer_impact"], repeat_count=record["repeat_count"],
        financial_risk=record["financial_risk"], details=record["details"],
    )


def _action(record: dict[str, Any]) -> ProposedAction:
    return ProposedAction(
        action_id=record["action_id"], action_type=record["action_type"],
        requested_by=record["requested_by"], description=record["description"],
    )


def _snapshot(record: dict[str, Any]) -> OrderSnapshot:
    return OrderSnapshot(**record)


def evaluate_shared_pack(data: dict[str, Any]) -> list[dict[str, str]]:
    """Evaluate shared records across six demos without mutating source data."""
    results: list[dict[str, str]] = []

    for record in data.get("lifecycle_events", []):
        event = OrderEvent(
            event_id=record["event_id"], order_id=record["order_id"],
            from_status=OrderStatus(record["from_status"]),
            to_status=OrderStatus(record["to_status"]),
            expected_version=record["expected_version"],
        )
        decision = evaluate_event(
            event, current_status=OrderStatus(record["current_status"]),
            current_version=record["current_version"],
            previously_seen_event_ids=record.get("previously_seen_event_ids", []),
        )
        results.append({
            "scenario_id": record["scenario_id"], "demo": "lifecycle",
            "record_id": record["event_id"], "decision": decision.code.value,
            "detail": decision.reason,
        })

    for record in data.get("exceptions", []):
        decision = triage_exception(_exception(record))
        results.append({
            "scenario_id": record["scenario_id"], "demo": "triage",
            "record_id": record["exception_id"], "decision": decision.priority.value,
            "detail": f"team={decision.assigned_team}; review_required={decision.human_review_required}; valid={decision.valid}",
        })

    snapshot_by_scenario = {}
    for record in data.get("snapshot_pairs", []):
        snapshot_by_scenario[record["scenario_id"]] = record
        decision = reconcile_orders(_snapshot(record["expected"]), _snapshot(record["observed"]))
        fields = ",".join(item.field for item in decision.discrepancies) or "none"
        results.append({
            "scenario_id": record["scenario_id"], "demo": "reconciliation",
            "record_id": record["order_id"],
            "decision": "MATCHED" if decision.matched else "REVIEW" if decision.human_review_required else "DISCREPANCY",
            "detail": f"valid={decision.valid}; fields={fields}",
        })

    exceptions_by_id = {record["exception_id"]: record for record in data.get("exceptions", [])}
    actions_by_id = {record["action_id"]: record for record in data.get("proposed_actions", [])}
    for workflow in data.get("workflow_scenarios", []):
        exception_record = exceptions_by_id[workflow["exception_id"]]
        action_record = actions_by_id[workflow["action_id"]]
        snapshot_record = snapshot_by_scenario.get(workflow.get("snapshot_scenario_id"))
        expected = _snapshot(snapshot_record["expected"]) if snapshot_record else None
        observed = _snapshot(snapshot_record["observed"]) if snapshot_record else None
        report = run_operational_workflow(OperationalWorkflowInput(
            workflow_id=workflow["workflow_id"],
            exception=_exception(exception_record),
            proposed_action=_action(action_record),
            expected_snapshot=expected,
            observed_snapshot=observed,
        ))
        results.append({
            "scenario_id": workflow["scenario_id"], "demo": "orchestration",
            "record_id": workflow["workflow_id"], "decision": report.status.value,
            "detail": "; ".join(report.reasons),
        })

    policy_groups: dict[str, list[dict[str, Any]]] = {}
    for record in data.get("policy_change_scenarios", []):
        policy_groups.setdefault(record["scenario_id"], []).append(record)
    for scenario_id, records in sorted(policy_groups.items()):
        baseline = [
            {"case_id": record["case_id"], "decision": record["baseline"]}
            for record in records
        ]
        candidate = [
            {"case_id": record["case_id"], "decision": record["candidate"]}
            for record in records
        ]
        report = compare_policy_snapshots(
            baseline, candidate, "baseline-demo", "candidate-demo"
        )
        risk = (
            "HIGH_RISK" if report.high_risk_count
            else "REVIEW" if any(change.risk == "MEDIUM" for change in report.changes)
            else "LOW_RISK"
        )
        detail = "; ".join(
            f"{change.category}/{change.risk}" for change in report.changes
        )
        results.append({
            "scenario_id": scenario_id,
            "demo": "policy_impact",
            "record_id": scenario_id,
            "decision": risk,
            "detail": detail,
        })

    for record in data.get("proposed_actions", []):
        decision = evaluate_action(_action(record))
        results.append({
            "scenario_id": record["scenario_id"], "demo": "governance",
            "record_id": record["action_id"], "decision": decision.outcome.value,
            "detail": f"allowed_to_execute={decision.allowed_to_execute}; approval_required={decision.approval_required}; valid={decision.valid}",
        })

    return results
