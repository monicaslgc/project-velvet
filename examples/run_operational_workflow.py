"""Run the synthetic end-to-end operational workflow demonstration."""
import json
from pathlib import Path
from velvet.exception_triage import OrderException
from velvet.order_reconciliation import OrderSnapshot
from velvet.operational_orchestrator import OperationalWorkflowInput, run_operational_workflow
from velvet.workflow_governance import ProposedAction

def main() -> int:
    data = json.loads(Path("examples/operational-workflow.json").read_text(encoding="utf-8"))
    exception = OrderException(**data["exception"])
    action = ProposedAction(**data["proposed_action"])
    expected = OrderSnapshot(**data["expected_snapshot"]) if data.get("expected_snapshot") else None
    observed = OrderSnapshot(**data["observed_snapshot"]) if data.get("observed_snapshot") else None
    report = run_operational_workflow(OperationalWorkflowInput(data.get("workflow_id"), exception, action, expected, observed))
    print(f"Workflow: {report.workflow_id}")
    print(f"Status: {report.status.value}")
    print(f"Triage: {report.triage.priority.value} -> {report.triage.assigned_team}")
    print(f"Governance: {report.governance.outcome.value}; approval_required={report.governance.approval_required}")
    print(f"Reconciliation: {'not run' if report.reconciliation is None else 'matched' if report.reconciliation.matched else 'discrepancies found'}")
    for reason in report.reasons:
        print(f"- {reason}")
    print("No order was changed and no action was executed.")
    return 0 if report.status.value == "READY_FOR_HUMAN_REVIEW" else 1

if __name__ == "__main__":
    raise SystemExit(main())
