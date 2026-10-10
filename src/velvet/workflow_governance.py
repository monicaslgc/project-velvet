"""Deterministic autonomy and approval policy for synthetic workflow demos."""
from __future__ import annotations
from dataclasses import dataclass
from enum import StrEnum

# Bump this identifier when the governance rules or their meaning changes.
# Snapshot comparison uses explicit fixture versions; this constant labels the
# deterministic evaluator implemented in this module.
POLICY_VERSION = "governance-v1"


class ActionType(StrEnum):
    READ_ONLY = "READ_ONLY"
    INTERNAL_DRAFT = "INTERNAL_DRAFT"
    CUSTOMER_COMMUNICATION = "CUSTOMER_COMMUNICATION"
    FINANCIAL_TRANSACTION = "FINANCIAL_TRANSACTION"
    ORDER_MUTATION = "ORDER_MUTATION"
    INVENTORY_MUTATION = "INVENTORY_MUTATION"
    EXTERNAL_SYSTEM_CHANGE = "EXTERNAL_SYSTEM_CHANGE"

class GovernanceOutcome(StrEnum):
    ALLOW = "ALLOW"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"
    MANUAL_REVIEW = "MANUAL_REVIEW"

@dataclass(frozen=True)
class ProposedAction:
    action_id: str
    action_type: str
    requested_by: str
    description: str

@dataclass(frozen=True)
class GovernanceDecision:
    action_id: str | None
    action_type: str | None
    outcome: GovernanceOutcome
    allowed_to_execute: bool
    approval_required: bool
    reasons: tuple[str, ...]
    valid: bool = True

APPROVAL_REQUIRED = {
    ActionType.CUSTOMER_COMMUNICATION,
    ActionType.FINANCIAL_TRANSACTION,
    ActionType.ORDER_MUTATION,
    ActionType.INVENTORY_MUTATION,
    ActionType.EXTERNAL_SYSTEM_CHANGE,
}

def evaluate_action(action: ProposedAction | None) -> GovernanceDecision:
    """Evaluate a proposed action without executing it or calling external systems.

    Read-only inspection and internal draft preparation may proceed autonomously.
    Customer-facing communication and all side-effecting action classes require
    explicit human approval. Invalid payloads and unknown action types fail closed.
    This evaluator does not implement an approval mechanism or execute actions.
    """
    if (
        not isinstance(action, ProposedAction)
        or not isinstance(action.action_id, str) or not action.action_id.strip()
        or not isinstance(action.action_type, str) or not action.action_type.strip()
        or not isinstance(action.requested_by, str) or not action.requested_by.strip()
        or not isinstance(action.description, str) or not action.description.strip()
    ):
        return GovernanceDecision(
            getattr(action, "action_id", None), getattr(action, "action_type", None),
            GovernanceOutcome.MANUAL_REVIEW, False, True,
            ("Required action fields are missing or malformed; autonomous execution is withheld.",),
            valid=False,
        )
    try:
        action_type = ActionType(action.action_type)
    except ValueError:
        return GovernanceDecision(
            action.action_id, action.action_type, GovernanceOutcome.MANUAL_REVIEW,
            False, True,
            ("Unknown action type; the policy cannot safely infer its risk or permissions.",),
        )
    if action_type in APPROVAL_REQUIRED:
        return GovernanceDecision(
            action.action_id, action_type.value, GovernanceOutcome.REQUIRE_APPROVAL,
            False, True,
            (f"{action_type.value} can create external or business-impacting side effects.",
             "A human must approve the proposal before any separate execution system acts."),
        )
    return GovernanceDecision(
        action.action_id, action_type.value, GovernanceOutcome.ALLOW, True, False,
        ("Action is limited to read-only inspection or internal draft preparation.",
         "This decision authorizes only the scoped proposal; it does not execute it."),
    )
