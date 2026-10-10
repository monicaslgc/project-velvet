"""Coordinate triage, governance, and optional reconciliation without side effects."""
from __future__ import annotations
from dataclasses import dataclass
from enum import StrEnum
from .exception_triage import OrderException, TriageDecision, triage_exception
from .order_reconciliation import OrderSnapshot, ReconciliationResult, reconcile_orders
from .workflow_governance import ProposedAction, GovernanceDecision, evaluate_action

class WorkflowStatus(StrEnum):
    BLOCKED = "BLOCKED"
    HUMAN_REVIEW_REQUIRED = "HUMAN_REVIEW_REQUIRED"
    READY_FOR_HUMAN_REVIEW = "READY_FOR_HUMAN_REVIEW"

@dataclass(frozen=True)
class OperationalWorkflowInput:
    workflow_id: str
    exception: OrderException
    proposed_action: ProposedAction
    expected_snapshot: OrderSnapshot | None = None
    observed_snapshot: OrderSnapshot | None = None

@dataclass(frozen=True)
class OperationalWorkflowReport:
    workflow_id: str | None
    status: WorkflowStatus
    triage: TriageDecision
    governance: GovernanceDecision
    reconciliation: ReconciliationResult | None
    reasons: tuple[str, ...]

def run_operational_workflow(request: OperationalWorkflowInput) -> OperationalWorkflowReport:
    """Run checks in sequence; never perform the proposed action."""
    valid = (
        isinstance(request, OperationalWorkflowInput)
        and isinstance(request.workflow_id, str) and bool(request.workflow_id.strip())
        and isinstance(request.exception, OrderException)
        and isinstance(request.proposed_action, ProposedAction)
    )
    if not valid:
        triage = triage_exception(request.exception if isinstance(request, OperationalWorkflowInput) else None)
        governance = evaluate_action(request.proposed_action if isinstance(request, OperationalWorkflowInput) else None)
        return OperationalWorkflowReport(
            getattr(request, "workflow_id", None), WorkflowStatus.BLOCKED, triage, governance,
            None, ("Workflow envelope is invalid; automated progression is blocked.",),
        )

    triage = triage_exception(request.exception)
    governance = evaluate_action(request.proposed_action)
    reconciliation = None
    reasons: list[str] = []
    status = WorkflowStatus.READY_FOR_HUMAN_REVIEW

    has_expected = request.expected_snapshot is not None
    has_observed = request.observed_snapshot is not None
    if has_expected != has_observed:
        status = WorkflowStatus.BLOCKED
        reasons.append("Both reconciliation snapshots must be supplied together.")
    elif has_expected:
        reconciliation = reconcile_orders(request.expected_snapshot, request.observed_snapshot)
        if not reconciliation.valid:
            status = WorkflowStatus.BLOCKED
            reasons.append("Reconciliation input is invalid; manual investigation is required.")
        elif reconciliation.human_review_required:
            status = WorkflowStatus.HUMAN_REVIEW_REQUIRED
            reasons.append("High-severity reconciliation discrepancy requires human review.")
        elif reconciliation.discrepancies:
            reasons.append("Reconciliation found non-blocking discrepancies.")

    if not triage.valid or triage.assigned_team == "manual_review":
        status = WorkflowStatus.BLOCKED
        reasons.append("Exception triage is invalid or requires manual classification.")
    elif triage.human_review_required:
        if status != WorkflowStatus.BLOCKED:
            status = WorkflowStatus.HUMAN_REVIEW_REQUIRED
        reasons.append("Exception priority or risk requires human review.")

    if not governance.valid or governance.outcome.value == "MANUAL_REVIEW":
        status = WorkflowStatus.BLOCKED
        reasons.append("Governance could not safely classify the proposed action.")
    elif governance.approval_required:
        if status == WorkflowStatus.READY_FOR_HUMAN_REVIEW:
            status = WorkflowStatus.HUMAN_REVIEW_REQUIRED
        reasons.append("Proposed action requires human approval before any separate execution.")

    if not reasons:
        reasons.append("Workflow checks completed; no execution was performed.")
    return OperationalWorkflowReport(
        request.workflow_id, status, triage, governance, reconciliation, tuple(dict.fromkeys(reasons))
    )
