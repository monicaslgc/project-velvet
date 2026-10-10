"""Evaluate synthetic agent proposal outputs against schema and governance policy."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from velvet.agent_action_contract import evaluate_agent_proposal

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    cases_path = ROOT / "examples" / "agent-proposal-contract-cases.json"
    try:
        cases = json.loads(cases_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: unable to load proposal cases: {exc}", file=sys.stderr)
        return 2
    if not isinstance(cases, list) or not cases:
        print("ERROR: proposal case file must contain a non-empty JSON array.", file=sys.stderr)
        return 2

    failed = 0
    print("Project Velvet — agent proposal contract evaluation (synthetic cases)")
    for case in cases:
        case_id = case.get("case_id", "<missing-case-id>")
        report = evaluate_agent_proposal(case.get("proposal"))
        actual = {
            "schema_valid": report.schema_valid,
            "outcome": report.decision.outcome.value,
            "allowed_to_execute": report.decision.allowed_to_execute,
            "approval_required": report.decision.approval_required,
        }
        expected = case.get("expected", {})
        mismatches = [
            f"{key}: expected {value!r}, got {actual.get(key)!r}"
            for key, value in expected.items()
            if actual.get(key) != value
        ]
        passed = bool(case_id) and not mismatches
        failed += not passed
        print(f"[{'PASS' if passed else 'FAIL'}] {case_id}: {actual}")
        for issue in report.issues:
            print(f"  schema issue: {issue}")
        for mismatch in mismatches:
            print(f"  mismatch: {mismatch}")
        for reason in report.decision.reasons:
            print(f"  policy: {reason}")

    print(f"\n{len(cases) - failed}/{len(cases)} cases passed.")
    print("No model is called and no proposed action is executed.")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
