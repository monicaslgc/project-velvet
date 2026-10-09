"""Run the synthetic policy-version impact comparison."""
import json
from pathlib import Path

from velvet.policy_impact import compare_policy_snapshots

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / "examples/policy-version-comparison.json").read_text(encoding="utf-8"))
REPORT = compare_policy_snapshots(DATA["baseline"], DATA["candidate"], DATA["baseline_version"], DATA["candidate_version"])
print(f"Policy comparison: {REPORT.baseline_version} -> {REPORT.candidate_version}")
print(f"Cases compared: {len(REPORT.changes)} | high-risk changes: {REPORT.high_risk_count} | unchanged: {REPORT.unchanged_count}")
for change in REPORT.changes:
    print(f"[{change.risk}] {change.case_id}: {change.category}")
    for detail in change.details:
        print(f"  - {detail}")
print("Review all HIGH-risk changes before considering a policy release. This report does not approve or deploy policy changes.")
