import json
from pathlib import Path

from velvet.exception_triage import OrderException, triage_exception


def load_cases():
    path = (
        Path(__file__).parents[1]
        / "examples"
        / "triage-skill-evaluation-cases.json"
    )
    return json.loads(path.read_text(encoding="utf-8"))


def test_triage_skill_regression_cases_match_policy():
    cases = load_cases()
    assert len(cases) >= 6
    for case in cases:
        decision = triage_exception(OrderException(**case["input"]))
        actual = {
            "priority": decision.priority.value,
            "assigned_team": decision.assigned_team,
            "human_review_required": decision.human_review_required,
            "valid": decision.valid,
        }
        for field, expected in case["expected"].items():
            assert actual[field] == expected, (
                f"{case['case_id']}: {field} expected {expected!r}, "
                f"got {actual[field]!r}"
            )


def test_untrusted_free_text_does_not_override_triage_policy():
    case = next(
        item
        for item in load_cases()
        if item["case_id"] == "free-text-cannot-change-category-policy"
    )
    decision = triage_exception(OrderException(**case["input"]))
    assert decision.assigned_team == "customer_operations"
    assert decision.priority.value == "P3"
    assert decision.human_review_required is False
