"""Execute the same synthetic cases under two policies and compare decisions."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from velvet.policy_impact import compare_policy_snapshots
from velvet.workflow_governance import (
    ActionType,
    DEFAULT_POLICY,
    GovernancePolicy,
    POLICY_VERSION,
    ProposedAction,
    evaluate_action,
)

ROOT = Path(__file__).resolve().parents[1]


def load_policy(path: Path) -> GovernancePolicy:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("candidate policy must be a JSON object")
    version = data.get("version")
    allowed = data.get("autonomous_allowed")
    approval = data.get("approval_required")
    if not isinstance(version, str) or not version.strip():
        raise ValueError("candidate policy requires a non-blank version")
    if not isinstance(allowed, list) or not all(isinstance(item, str) for item in allowed):
        raise ValueError("autonomous_allowed must be a list of action-type strings")
    if not isinstance(approval, list) or not all(isinstance(item, str) for item in approval):
        raise ValueError("approval_required must be a list of action-type strings")
    try:
        allowed_types = frozenset(ActionType(item) for item in allowed)
        approval_types = frozenset(ActionType(item) for item in approval)
    except ValueError as exc:
        raise ValueError(f"candidate policy contains an unknown action type: {exc}") from exc
    if allowed_types & approval_types:
        raise ValueError("an action type cannot be both autonomously allowed and approval-required")
    return GovernancePolicy(version, approval_types, allowed_types)


def decision_snapshot(cases: list[dict[str, Any]], policy: GovernancePolicy) -> list[dict[str, Any]]:
    snapshots: list[dict[str, Any]] = []
    for case in cases:
        if not isinstance(case, dict) or not isinstance(case.get("case_id"), str):
            raise ValueError("each evaluation case requires a string case_id")
        raw = case.get("input")
        if not isinstance(raw, dict):
            raise ValueError(f"case {case['case_id']} requires an input object")
        action = ProposedAction(
            action_id=raw.get("action_id"),
            action_type=raw.get("action_type"),
            requested_by=raw.get("requested_by"),
            description=raw.get("description"),
        )
        result = evaluate_action(action, policy)
        snapshots.append(
            {
                "case_id": case["case_id"],
                "decision": {
                    "outcome": result.outcome.value,
                    "allowed_to_execute": result.allowed_to_execute,
                    "approval_required": result.approval_required,
                    "valid": result.valid,
                    "reasons": list(result.reasons),
                },
            }
        )
    return snapshots


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fail-on-high-risk",
        action="store_true",
        help="return exit code 1 when the candidate relaxes a control or removes a case",
    )
    args = parser.parse_args()
    try:
        cases = json.loads((ROOT / "examples" / "agent-evaluation-cases.json").read_text(encoding="utf-8"))
        candidate = load_policy(ROOT / "examples" / "policy-candidate.json")
        if not isinstance(cases, list) or not cases:
            raise ValueError("evaluation cases must be a non-empty JSON array")
        baseline = GovernancePolicy(
            version=POLICY_VERSION,
            approval_required=DEFAULT_POLICY.approval_required,
            autonomous_allowed=DEFAULT_POLICY.autonomous_allowed,
        )
        before = decision_snapshot(cases, baseline)
        after = decision_snapshot(cases, candidate)
        report = compare_policy_snapshots(before, after, baseline.version, candidate.version)
    except (OSError, json.JSONDecodeError, ValueError, TypeError) as exc:
        print(f"ERROR: unable to evaluate policy regression: {exc}", file=sys.stderr)
        return 2

    print("Project Velvet — executable policy regression demo (synthetic cases)")
    print(f"Policies: {report.baseline_version} -> {report.candidate_version}")
    print(f"Same cases evaluated: {len(report.changes)}")
    for change in report.changes:
        print(f"[{change.risk}] {change.case_id}: {change.category}")
        for detail in change.details:
            print(f"  - {detail}")
    print(f"High-risk changes: {report.high_risk_count}")
    print("This example executes both configured policy sets against the same cases.")
    print("The candidate is intentionally unsafe; no actions are executed or deployed.")
    if args.fail_on_high_risk and report.high_risk_count:
        print("GATE: BLOCKED — high-risk changes require human review.")
        return 1
    print("GATE: review findings; this demo does not approve or deploy policy.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
