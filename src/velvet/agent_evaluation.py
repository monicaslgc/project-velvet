"""Small regression harness for deterministic agent-policy evaluators."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Callable, Iterable
from velvet.workflow_governance import ProposedAction, evaluate_action

@dataclass(frozen=True)
class CaseResult:
    case_id: str
    passed: bool
    expected: dict[str, Any]
    actual: dict[str, Any]
    message: str

@dataclass(frozen=True)
class EvaluationReport:
    total: int
    passed: int
    failed: int
    results: tuple[CaseResult, ...]

    @property
    def pass_rate(self) -> float:
        return self.passed / self.total if self.total else 1.0

def evaluate_cases(cases: Iterable[dict[str, Any]], evaluator: Callable[[ProposedAction], Any] = evaluate_action) -> EvaluationReport:
    """Compare expected fields against a deterministic evaluator's results."""
    results: list[CaseResult] = []
    seen_ids: set[str] = set()
    for index, case in enumerate(cases):
        case_id = case.get("case_id", f"case-{index + 1}")
        if not isinstance(case_id, str) or not case_id.strip() or case_id in seen_ids:
            results.append(CaseResult(str(case_id), False, {}, {}, "Case ID is blank or duplicated."))
            continue
        seen_ids.add(case_id)
        try:
            action = ProposedAction(**case["input"])
            decision = evaluator(action)
            actual = {
                "outcome": decision.outcome.value,
                "allowed_to_execute": decision.allowed_to_execute,
                "approval_required": decision.approval_required,
                "valid": decision.valid,
            }
            expected = case["expected"]
            mismatches = [
                f"{key}: expected {value!r}, got {actual.get(key)!r}"
                for key, value in expected.items() if actual.get(key) != value
            ]
            passed = not mismatches
            message = "All expected fields matched." if passed else "; ".join(mismatches)
        except (KeyError, TypeError, ValueError, AttributeError) as exc:
            expected, actual, passed = case.get("expected", {}), {}, False
            message = f"Invalid test case or evaluator result: {exc}"
        results.append(CaseResult(case_id, passed, expected, actual, message))
    passed_count = sum(item.passed for item in results)
    return EvaluationReport(len(results), passed_count, len(results) - passed_count, tuple(results))
