"""Print actual module outputs for the linked shipment-delay review scenario."""
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
from velvet.order_reconciliation import OrderSnapshot, reconcile_orders  # noqa: E402
from velvet.shared_scenarios import evaluate_shared_pack  # noqa: E402
from velvet.workflow_governance import ProposedAction, evaluate_action  # noqa: E402


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

    exception_record = next(
        row for row in pack["exceptions"] if row["exception_id"] == "exc-6101"
    )
    action_record = next(
        row for row in pack["proposed_actions"] if row["action_id"] == "act-7102"
    )
    snapshots = next(
        row for row in pack["snapshot_pairs"] if row["scenario_id"] == "status-disagreement"
    )
    workflow = next(
        row for row in pack["workflow_scenarios"]
        if row["scenario_id"] == "shipment-delay-customer-review"
    )

    exception = OrderException(
        exception_id=exception_record["exception_id"],
        order_id=exception_record["order_id"],
        category=exception_record["category"],
        age_hours=exception_record["age_hours"],
        customer_impact=exception_record["customer_impact"],
        repeat_count=exception_record["repeat_count"],
        financial_risk=exception_record["financial_risk"],
        details=exception_record["details"],
    )
    action = ProposedAction(
        action_id=action_record["action_id"],
        action_type=action_record["action_type"],
        requested_by=action_record["requested_by"],
        description=action_record["description"],
    )
    expected = OrderSnapshot(**snapshots["expected"])
    observed = OrderSnapshot(**snapshots["observed"])

    triage = triage_exception(exception)
    reconciliation = reconcile_orders(expected, observed)
    governance = evaluate_action(action)
    orchestration = run_operational_workflow(
        OperationalWorkflowInput(
            workflow_id=workflow["workflow_id"],
            exception=exception,
            proposed_action=action,
            expected_snapshot=expected,
            observed_snapshot=observed,
        )
    )

    result = {
        "scenario_id": workflow["scenario_id"],
        "synthetic_only": pack["synthetic_data_only"],
        "input": {
            "order_id": exception.order_id,
            "exception": {
                "id": exception.exception_id,
                "category": exception.category,
                "age_hours": exception.age_hours,
                "customer_impact": exception.customer_impact,
            },
            "snapshot_status": {
                "expected": expected.status,
                "observed": observed.status,
            },
            "proposed_action": {
                "id": action.action_id,
                "type": action.action_type,
            },
        },
        "triage": {
            "priority": triage.priority.value,
            "assigned_team": triage.assigned_team,
            "human_review_required": triage.human_review_required,
            "reasons": list(triage.reasons),
        },
        "reconciliation": {
            "matched": reconciliation.matched,
            "human_review_required": reconciliation.human_review_required,
            "discrepancies": [
                {
                    "field": item.field,
                    "expected": item.expected_value,
                    "observed": item.observed_value,
                    "severity": item.severity.value,
                    "reason": item.reason,
                }
                for item in reconciliation.discrepancies
            ],
            "source_data_changed": False,
        },
        "governance": {
            "outcome": governance.outcome.value,
            "allowed_to_execute": governance.allowed_to_execute,
            "approval_required": governance.approval_required,
            "reasons": list(governance.reasons),
        },
        "orchestration": {
            "status": orchestration.status.value,
            "reasons": list(orchestration.reasons),
            "action_executed": False,
        },
    }

    # Guard this walkthrough against silent drift in the scenario's key safety result.
    shared_results = evaluate_shared_pack(pack)
    linked = next(
        row for row in shared_results
        if row["demo"] == "orchestration" and row["scenario_id"] == workflow["scenario_id"]
    )
    if linked["decision"] != orchestration.status.value:
        print("ERROR: linked runner and direct walkthrough disagree.", file=sys.stderr)
        return 1

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
