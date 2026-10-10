"""Run deterministic regression cases for the order-triage skill contract."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from velvet.exception_triage import OrderException, triage_exception


def evaluate_case(case: dict[str, Any]) -> tuple[bool, str]:
    case_id = case.get("case_id", "<missing-case-id>")
    try:
        exception = OrderException(**case["input"])
        decision = triage_exception(exception)
        actual = {
            "priority": decision.priority.value,
            "assigned_team": decision.assigned_team,
            "human_review_required": decision.human_review_required,
            "valid": decision.valid,
        }
        expected = case["expected"]
        mismatches = [
            f"{key}: expected {value!r}, got {actual.get(key)!r}"
            for key, value in expected.items()
            if actual.get(key) != value
        ]
        if mismatches:
            return False, f"{case_id}: " + "; ".join(mismatches)
        return True, f"{case_id}: all expected fields matched"
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        return False, f"{case_id}: invalid case or evaluator result: {exc}"


def main() -> int:
    path = Path(__file__).with_name("triage-skill-evaluation-cases.json")
    cases = json.loads(path.read_text(encoding="utf-8"))
    outcomes = [evaluate_case(case) for case in cases]
    passed = sum(ok for ok, _ in outcomes)
    print(
        f"Order-triage skill regression: {passed}/{len(outcomes)} passed "
        f"({passed / len(outcomes):.0%})"
    )
    for ok, message in outcomes:
        print(f"[{'PASS' if ok else 'FAIL'}] {message}")
    if passed != len(outcomes):
        print("Triage skill regression detected.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
