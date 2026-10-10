"""Strict, model-independent contract for proposed agent action payloads."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .workflow_governance import GovernanceDecision, ProposedAction, evaluate_action

REQUIRED_FIELDS = frozenset({"action_id", "action_type", "requested_by", "description"})


@dataclass(frozen=True)
class AgentProposalReport:
    """Schema conformance and policy decision for one untrusted agent proposal."""

    schema_valid: bool
    decision: GovernanceDecision
    issues: tuple[str, ...]


def evaluate_agent_proposal(payload: Any) -> AgentProposalReport:
    """Validate a proposal's exact shape, then apply governance without executing it.

    Unknown action types are schema-valid but are sent to manual review by policy.
    Missing, malformed, non-object, or extra-field payloads fail closed and are
    never treated as permission to act. This function does not call an LLM.
    """
    if not isinstance(payload, dict):
        decision = evaluate_action(None)  # The governance evaluator fails closed.
        return AgentProposalReport(False, decision, ("Proposal must be a JSON object.",))

    keys = set(payload)
    missing = sorted(REQUIRED_FIELDS - keys)
    unexpected = sorted(str(key) for key in keys - REQUIRED_FIELDS)
    issues: list[str] = []
    if missing:
        issues.append(f"Missing required field(s): {', '.join(missing)}.")
    if unexpected:
        issues.append(f"Unexpected field(s): {', '.join(unexpected)}.")

    for field in sorted(REQUIRED_FIELDS & keys):
        value = payload[field]
        if not isinstance(value, str) or not value.strip():
            issues.append(f"Field '{field}' must be a non-empty string.")

    if issues:
        decision = evaluate_action(None)
        return AgentProposalReport(False, decision, tuple(issues))

    action = ProposedAction(
        action_id=payload["action_id"],
        action_type=payload["action_type"],
        requested_by=payload["requested_by"],
        description=payload["description"],
    )
    return AgentProposalReport(True, evaluate_action(action), ())
