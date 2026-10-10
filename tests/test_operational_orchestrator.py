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
