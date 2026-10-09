"""Check skill requirement-to-regression-case traceability."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from velvet.skill_contracts import validate_skill_contracts  # noqa: E402


def main() -> int:
    contract_path = ROOT / "contracts/ai-workflow-governance.json"
    cases_path = ROOT / "examples/agent-evaluation-cases.json"
    contracts = json.loads(contract_path.read_text())
    cases = json.loads(cases_path.read_text())
    issues = validate_skill_contracts(contracts, cases)
    if issues:
        for issue in issues:
            print(f"FAIL: {issue}")
        print(f"Skill contract check failed with {len(issues)} issue(s).")
        return 1
    total = len(contracts["contracts"])
    mapped = sum(len(item["case_ids"]) for item in contracts["contracts"])
    print(f"PASS: {total} governance requirements map to {mapped} regression-case references.")
    print("Scope: mapping integrity only; this does not prove natural-language requirements are complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
