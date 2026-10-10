"""Run the read-only Project Velvet release-readiness gate."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from velvet.release_readiness import build_release_readiness_report  # noqa: E402


def read_json(relative_path: str):
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


def main() -> int:
    try:
        report = build_release_readiness_report(
            read_json("examples/agent-evaluation-cases.json"),
            read_json("contracts/ai-workflow-governance.json"),
            read_json("examples/decision-records.json"),
            read_json("examples/policy-version-comparison.json"),
        )
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: unable to produce release-readiness report: {exc}", file=sys.stderr)
        return 2

    print("Project Velvet — release readiness")
    print(f"Policy comparison: {report.baseline_version} -> {report.candidate_version}")
    print(f"Overall status: {report.status}")
    for name, check in report.checks.items():
        print(f"\n[{check.status}] {name}: {check.summary}")
        for detail in check.details:
            print(f"  - {detail}")
    print(
        "\nThis report is a read-only gate over synthetic evidence. "
        "Human approval is still required; no action or deployment is performed."
    )
    return 0 if report.ready_for_human_review else 1


if __name__ == "__main__":
    raise SystemExit(main())
