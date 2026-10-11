"""Trace the flagship colour-restock incident through every policy stage.

One fictional salon order loses a line because a colour shade is short. The
script prints, for each stage, the exact input and the structured decision, then
runs four different agent proposals through the same incident to show how the
proposal alone changes the outcome. Nothing is executed or modified.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from velvet.demo_dataset import validate_dataset  # noqa: E402
from velvet.exception_triage import OrderException, triage_exception  # noqa: E402
from velvet.operational_orchestrator import (  # noqa: E402
    OperationalWorkflowInput,
    run_operational_workflow,
)
from velvet.order_lifecycle import OrderEvent, OrderStatus, evaluate_event  # noqa: E402
from velvet.order_reconciliation import OrderSnapshot, reconcile_orders  # noqa: E402
from velvet.shared_scenarios import evaluate_shared_pack  # noqa: E402
from velvet.workflow_governance import ProposedAction, evaluate_action  # noqa: E402

ORDER_ID = "ord-4201"
EXCEPTION_ID = "exc-6201"
EVENT_ID = "evt-5201"
SNAPSHOT_SCENARIO = "colour-restock-line-dropped"
WORKFLOW_IDS = ("wf-8201", "wf-8202", "wf-8203", "wf-8204")


def build_incident(pack: dict) -> dict:
    """Evaluate the incident from the shared pack and return a JSON-ready trace."""
    event_record = next(r for r in pack["lifecycle_events"] if r["event_id"] == EVENT_ID)
    event = OrderEvent(
        event_id=event_record["event_id"], order_id=event_record["order_id"],
        from_status=OrderStatus(event_record["from_status"]),
        to_status=OrderStatus(event_record["to_status"]),
        expected_version=event_record["expected_version"],
    )
    lifecycle = evaluate_event(
        event, current_status=OrderStatus(event_record["current_status"]),
        current_version=event_record["current_version"],
        previously_seen_event_ids=event_record["previously_seen_event_ids"],
    )

    exception_record = next(r for r in pack["exceptions"] if r["exception_id"] == EXCEPTION_ID)
    exception = OrderException(**{k: v for k, v in exception_record.items() if k != "scenario_id"})
    triage = triage_exception(exception)

    pair = next(r for r in pack["snapshot_pairs"] if r["scenario_id"] == SNAPSHOT_SCENARIO)
    expected, observed = OrderSnapshot(**pair["expected"]), OrderSnapshot(**pair["observed"])
    reconciliation = reconcile_orders(expected, observed)

    workflows = []
    actions_by_id = {r["action_id"]: r for r in pack["proposed_actions"]}
    for workflow_id in WORKFLOW_IDS:
        workflow = next(r for r in pack["workflow_scenarios"] if r["workflow_id"] == workflow_id)
        action_record = actions_by_id[workflow["action_id"]]
        action = ProposedAction(**{k: v for k, v in action_record.items() if k != "scenario_id"})
        governance = evaluate_action(action)
        report = run_operational_workflow(OperationalWorkflowInput(
            workflow_id, exception, action, expected, observed,
        ))
        workflows.append({
            "workflow_id": workflow_id,
            "scenario_id": workflow["scenario_id"],
            "proposed_action": {"id": action.action_id, "type": action.action_type,
                                "description": action.description},
            "governance": {
                "outcome": governance.outcome.value,
                "allowed_to_execute": governance.allowed_to_execute,
                "approval_required": governance.approval_required,
            },
            "workflow_status": report.status.value,
            "reasons": list(report.reasons),
            "action_executed": False,
        })

    return {
        "incident": "colour-restock-incident",
        "synthetic_only": pack["synthetic_data_only"],
        "order_id": ORDER_ID,
        "stage_1_lifecycle": {
            "event": f"{event.from_status} -> {event.to_status}",
            "order_currently": event_record["current_status"],
            "decision": lifecycle.code.value,
            "reason": lifecycle.reason,
        },
        "stage_2_triage": {
            "category": exception.category,
            "age_hours": exception.age_hours,
            "repeat_count": exception.repeat_count,
            "customer_impact": exception.customer_impact,
            "priority": triage.priority.value,
            "assigned_team": triage.assigned_team,
            "human_review_required": triage.human_review_required,
            "reasons": list(triage.reasons),
        },
        "stage_3_reconciliation": {
            "matched": reconciliation.matched,
            "human_review_required": reconciliation.human_review_required,
            "discrepancies": [
                {"field": d.field, "expected": d.expected_value, "observed": d.observed_value,
                 "severity": d.severity.value}
                for d in reconciliation.discrepancies
            ],
            "source_data_changed": False,
        },
        "stage_4_proposals": workflows,
    }


def main() -> int:
    pack_path = ROOT / "datasets" / "operational-demo-pack.json"
    try:
        pack = json.loads(pack_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: unable to load synthetic demo pack: {exc}", file=sys.stderr)
        return 2
    errors = validate_dataset(pack)
    if errors:
        print("\n".join(f"DATASET ERROR: {error}" for error in errors), file=sys.stderr)
        return 2

    trace = build_incident(pack)

    # Guard against drift between this walkthrough and the shared runner.
    shared = {
        row["record_id"]: row["decision"]
        for row in evaluate_shared_pack(pack) if row["demo"] == "orchestration"
    }
    for item in trace["stage_4_proposals"]:
        if shared.get(item["workflow_id"]) != item["workflow_status"]:
            print("ERROR: shared runner and incident walkthrough disagree.", file=sys.stderr)
            return 1

    print(json.dumps(trace, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
