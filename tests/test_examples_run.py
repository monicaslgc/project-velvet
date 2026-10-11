"""Every runnable example is executed, so documented commands cannot silently rot.

Two scripts return a non-zero exit code on their bundled sample *by design*
(they only succeed when the result is READY_FOR_HUMAN_REVIEW). Registering the
expected code for every script, including those two, means a new example cannot
be added without a deliberate decision about how it should behave.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"

EXPECTED_EXIT = {
    "analyze_policy_impact.py": 0,
    "audit_demo.py": 0,
    "check_skill_contracts.py": 0,
    "evaluate_agent_policy.py": 0,
    "evaluate_agent_proposals.py": 0,
    "evaluate_policy_regression.py": 0,
    "evaluate_triage_skill.py": 0,
    "governance_demo.py": 0,
    "reconciliation_demo.py": 0,
    "release_readiness_report.py": 1,   # sample candidate policy is intentionally unsafe: BLOCKED
    "replay_decisions.py": 0,
    "run_demo.py": 0,
    "run_operational_workflow.py": 1,   # sample proposal needs approval: HUMAN_REVIEW_REQUIRED
    "run_shared_dataset.py": 0,
    "show_colour_restock_incident.py": 0,
    "show_shipment_review.py": 0,
    "triage_demo.py": 0,
    "validate_demo_dataset.py": 0,
}


def run(script, *args):
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"), PYTHONIOENCODING="utf-8")
    return subprocess.run(
        [sys.executable, str(EXAMPLES / script), *args],
        cwd=ROOT, env=env, capture_output=True, text=True, encoding="utf-8", timeout=60,
    )


def test_every_example_script_is_registered_with_an_expected_exit_code():
    on_disk = {p.name for p in EXAMPLES.glob("*.py")}
    assert on_disk == set(EXPECTED_EXIT), (
        f"unregistered: {sorted(on_disk - set(EXPECTED_EXIT))}; missing: {sorted(set(EXPECTED_EXIT) - on_disk)}")


@pytest.mark.parametrize("script", sorted(EXPECTED_EXIT))
def test_example_runs_with_its_documented_exit_code_and_prints_something(script):
    result = run(script)
    assert result.returncode == EXPECTED_EXIT[script], result.stderr or result.stdout
    assert result.stdout.strip(), "an example that prints nothing demonstrates nothing"
    assert "Traceback" not in result.stderr


def test_policy_regression_gate_flag_exits_non_zero_for_the_unsafe_candidate():
    assert run("evaluate_policy_regression.py", "--fail-on-high-risk").returncode == 1


def test_examples_never_claim_to_have_executed_a_business_action():
    for script in ("run_operational_workflow.py", "show_shipment_review.py", "show_colour_restock_incident.py"):
        out = run(script).stdout.lower()
        assert "action_executed\": true" not in out and "action executed: true" not in out
