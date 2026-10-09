"""Run the versioned governance regression suite."""
import json
import sys
from pathlib import Path
from velvet.agent_evaluation import evaluate_cases

def main() -> int:
    path = Path(__file__).with_name("agent-evaluation-cases.json")
    cases = json.loads(path.read_text(encoding="utf-8"))
    report = evaluate_cases(cases)
    print(f"Agent policy regression: {report.passed}/{report.total} passed ({report.pass_rate:.0%})")
    for result in report.results:
        status = "PASS" if result.passed else "FAIL"
        print(f"[{status}] {result.case_id}: {result.message}")
    if report.failed:
        print(f"Regression detected: {report.failed} case(s) failed.", file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
