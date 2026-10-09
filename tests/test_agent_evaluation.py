import json
from pathlib import Path
from velvet.agent_evaluation import evaluate_cases

def load_cases():
    path = Path(__file__).parents[1] / "examples" / "agent-evaluation-cases.json"
    return json.loads(path.read_text(encoding="utf-8"))

def test_regression_suite_passes_all_baseline_cases():
    report = evaluate_cases(load_cases())
    assert report.total >= 7
    assert report.failed == 0
    assert report.passed == report.total
    assert report.pass_rate == 1.0

def test_regression_suite_detects_policy_drift():
    cases = load_cases()
    cases[0]["expected"]["outcome"] = "REQUIRE_APPROVAL"
    report = evaluate_cases(cases)
    assert report.failed == 1
    assert report.results[0].passed is False
    assert "expected 'REQUIRE_APPROVAL'" in report.results[0].message

def test_duplicate_case_ids_fail_as_test_failures():
    cases = load_cases()
    cases.append(dict(cases[0]))
    report = evaluate_cases(cases)
    assert report.failed == 1
    assert "duplicated" in report.results[-1].message

def test_empty_suite_has_zero_cases():
    report = evaluate_cases([])
    assert report.total == 0
    assert report.pass_rate == 1.0
