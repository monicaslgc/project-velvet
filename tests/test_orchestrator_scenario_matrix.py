"""Scenario matrix: independent check outcomes must combine to the strictest status.

Each axis contributes a severity (0 = READY, 1 = HUMAN_REVIEW, 2 = BLOCKED). The
orchestrator must report the maximum of the three, and a passing sub-check must
never lower a status set by another one.
"""
from itertools import product

import pytest

from velvet.exception_triage import OrderException
from velvet.operational_orchestrator import OperationalWorkflowInput, WorkflowStatus, run_operational_workflow
from velvet.order_reconciliation import OrderSnapshot
from velvet.workflow_governance import ProposedAction

SEVERITY_TO_STATUS = {
    0: WorkflowStatus.READY_FOR_HUMAN_REVIEW,
    1: WorkflowStatus.HUMAN_REVIEW_REQUIRED,
    2: WorkflowStatus.BLOCKED,
}

# axis value -> (builder argument, severity)
TRIAGE = {
    "routine": (dict(category="SHIPMENT_DELAY", age=2, impact=False), 0),
    "high_priority": (dict(category="SHIPMENT_DELAY", age=30, impact=True), 1),
    "unknown_category": (dict(category="MYSTERY_EXCEPTION", age=2, impact=False), 2),
}
ACTION = {
    "read_only": ("READ_ONLY", 0),
    "approval_required": ("CUSTOMER_COMMUNICATION", 1),
    "unknown_action": ("DO_ANYTHING", 2),
}
RECONCILIATION = {
    "none": ("none", 0),
    "matching": ("matching", 0),
    "non_blocking_item_count": ("item_count", 0),
    "high_severity_status": ("status", 1),
    "partial_pair": ("partial", 2),
    "different_orders": ("different_orders", 2),
}


def build(triage_key, action_key, recon_key):
    triage_args, _ = TRIAGE[triage_key]
    action_type, _ = ACTION[action_key]
    mode, _ = RECONCILIATION[recon_key]

    expected = OrderSnapshot("ord-1", "PROCESSING", 1299, "EUR", 2, "source-a")
    observed = OrderSnapshot("ord-1", "PROCESSING", 1299, "EUR", 2, "source-b")
    pair = (None, None)
    if mode == "matching":
        pair = (expected, observed)
    elif mode == "item_count":
        pair = (expected, OrderSnapshot("ord-1", "PROCESSING", 1299, "EUR", 3, "source-b"))
    elif mode == "status":
        pair = (expected, OrderSnapshot("ord-1", "SHIPPED", 1299, "EUR", 2, "source-b"))
    elif mode == "partial":
        pair = (expected, None)
    elif mode == "different_orders":
        pair = (expected, OrderSnapshot("ord-2", "PROCESSING", 1299, "EUR", 2, "source-b"))

    return OperationalWorkflowInput(
        "wf-matrix",
        OrderException("ex-1", "ord-1", triage_args["category"], triage_args["age"],
                       customer_impact=triage_args["impact"]),
        ProposedAction("act-1", action_type, "workflow-agent", "Matrix scenario"),
        *pair,
    )


COMBINATIONS = list(product(TRIAGE, ACTION, RECONCILIATION))


@pytest.mark.parametrize("triage_key,action_key,recon_key", COMBINATIONS)
def test_status_is_the_strictest_applicable_outcome(triage_key, action_key, recon_key):
    expected_severity = max(TRIAGE[triage_key][1], ACTION[action_key][1], RECONCILIATION[recon_key][1])
    report = run_operational_workflow(build(triage_key, action_key, recon_key))
    assert report.status == SEVERITY_TO_STATUS[expected_severity]


@pytest.mark.parametrize("triage_key,action_key,recon_key", COMBINATIONS)
def test_no_combination_executes_an_unapproved_action(triage_key, action_key, recon_key):
    report = run_operational_workflow(build(triage_key, action_key, recon_key))
    if ACTION[action_key][1] > 0:
        assert report.governance.allowed_to_execute is False
    if report.status != WorkflowStatus.READY_FOR_HUMAN_REVIEW:
        assert report.reasons, "a non-ready status must explain itself"


@pytest.mark.parametrize("triage_key,action_key,recon_key", COMBINATIONS)
def test_every_triggered_check_is_explained(triage_key, action_key, recon_key):
    report = run_operational_workflow(build(triage_key, action_key, recon_key))
    text = " ".join(report.reasons).lower()
    if TRIAGE[triage_key][1] == 2:
        assert "manual classification" in text
    if ACTION[action_key][1] == 2:
        assert "could not safely classify" in text
    if ACTION[action_key][1] == 1:
        assert "human approval" in text
    if RECONCILIATION[recon_key][0] == "status":
        assert "reconciliation discrepancy" in text
    if RECONCILIATION[recon_key][0] == "partial":
        assert "snapshots must be supplied together" in text
