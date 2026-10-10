from velvet.exception_triage import OrderException
from velvet.order_reconciliation import OrderSnapshot
from velvet.operational_orchestrator import OperationalWorkflowInput, WorkflowStatus, run_operational_workflow
from velvet.workflow_governance import ProposedAction

def request(*, category="SHIPMENT_DELAY", age=2, impact=False, action_type="READ_ONLY",
            expected=None, observed=None, workflow_id="wf-001"):
    return OperationalWorkflowInput(
        workflow_id, OrderException("ex-1", "ord-1", category, age, customer_impact=impact),
        ProposedAction("act-1", action_type, "workflow-agent", "Inspect order context"), expected, observed,
    )

def snapshots(status="PROCESSING", observed_status=None):
    return (OrderSnapshot("ord-1", status, 1299, "EUR", 2, "source-a"),
            OrderSnapshot("ord-1", observed_status or status, 1299, "EUR", 2, "source-b"))

def test_read_only_workflow_with_matching_snapshots_reaches_review_ready():
    expected, observed = snapshots()
    report = run_operational_workflow(request(expected=expected, observed=observed))
    assert report.status == WorkflowStatus.READY_FOR_HUMAN_REVIEW
    assert report.reconciliation is not None and report.reconciliation.matched
    assert report.governance.allowed_to_execute is True

def test_side_effecting_action_requires_human_review():
    report = run_operational_workflow(request(action_type="ORDER_MUTATION"))
    assert report.status == WorkflowStatus.HUMAN_REVIEW_REQUIRED
    assert report.governance.approval_required is True
    assert report.governance.allowed_to_execute is False

def test_unknown_exception_blocks_workflow():
    report = run_operational_workflow(request(category="MYSTERY_EXCEPTION"))
    assert report.status == WorkflowStatus.BLOCKED
    assert report.triage.assigned_team == "manual_review"

def test_high_severity_reconciliation_mismatch_requires_review():
    expected, observed = snapshots(observed_status="SHIPPED")
    report = run_operational_workflow(request(expected=expected, observed=observed))
    assert report.status == WorkflowStatus.HUMAN_REVIEW_REQUIRED
    assert report.reconciliation.human_review_required

def test_partial_reconciliation_pair_blocks():
    expected, _ = snapshots()
    report = run_operational_workflow(request(expected=expected))
    assert report.status == WorkflowStatus.BLOCKED
    assert report.reconciliation is None

def test_high_priority_customer_impact_requires_review():
    report = run_operational_workflow(request(age=24, impact=True))
    assert report.status == WorkflowStatus.HUMAN_REVIEW_REQUIRED

def test_unknown_action_fails_closed():
    report = run_operational_workflow(request(action_type="DO_ANYTHING"))
    assert report.status == WorkflowStatus.BLOCKED
    assert report.governance.allowed_to_execute is False


def test_blocker_takes_precedence_over_high_priority_and_approval_required_action():
    report = run_operational_workflow(request(
        category="MYSTERY_EXCEPTION",
        age=30,
        impact=True,
        action_type="CUSTOMER_COMMUNICATION",
    ))
    assert report.status == WorkflowStatus.BLOCKED
    assert report.triage.assigned_team == "manual_review"
    assert report.governance.approval_required is True
    assert any("manual classification" in reason for reason in report.reasons)
    assert any("requires human approval" in reason for reason in report.reasons)


def test_high_severity_reconciliation_and_customer_communication_both_require_review():
    expected, observed = snapshots(observed_status="SHIPPED")
    report = run_operational_workflow(request(
        expected=expected,
        observed=observed,
        action_type="CUSTOMER_COMMUNICATION",
    ))
    assert report.status == WorkflowStatus.HUMAN_REVIEW_REQUIRED
    assert report.reconciliation is not None
    assert report.reconciliation.human_review_required is True
    assert report.governance.approval_required is True
    assert any("reconciliation discrepancy" in reason for reason in report.reasons)
    assert any("human approval" in reason for reason in report.reasons)


def test_non_blocking_item_count_discrepancy_does_not_escalate_by_itself():
    expected, _ = snapshots()
    observed = OrderSnapshot("ord-1", "PROCESSING", 1299, "EUR", 3, "source-b")
    report = run_operational_workflow(request(expected=expected, observed=observed))
    assert report.status == WorkflowStatus.READY_FOR_HUMAN_REVIEW
    assert report.reconciliation is not None
    assert report.reconciliation.discrepancies[0].field == "item_count"
    assert report.reconciliation.human_review_required is False


def test_invalid_exception_payload_blocks_even_when_action_is_read_only():
    malformed = OrderException("ex-1", "ord-1", "SHIPMENT_DELAY", float("nan"))
    payload = OperationalWorkflowInput(
        "wf-001", malformed,
        ProposedAction("act-1", "READ_ONLY", "workflow-agent", "Inspect order context"),
    )
    report = run_operational_workflow(payload)
    assert report.status == WorkflowStatus.BLOCKED
    assert report.triage.valid is False
    assert report.governance.allowed_to_execute is True
    assert any("triage is invalid" in reason for reason in report.reasons)


def test_blank_workflow_id_blocks_otherwise_valid_request():
    report = run_operational_workflow(request(workflow_id="   "))
    assert report.status == WorkflowStatus.BLOCKED
    assert report.workflow_id == "   "
    assert "Workflow envelope is invalid; automated progression is blocked." in report.reasons
