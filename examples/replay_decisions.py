"""Replay synthetic historical decisions against the current governance policy."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from velvet.decision_replay import replay_records  # noqa: E402


def main() -> int:
    path = ROOT / "examples/decision-records.json"
    try:
        records = json.loads(path.read_text(encoding="utf-8"))
        results = replay_records(records)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 1

    changed = [result for result in results if result.changed]
    print(f"Decision replay: {len(results)} record(s), {len(changed)} changed decision(s).")
    for result in results:
        state = "DRIFT" if result.changed else "UNCHANGED"
        print(f"{state} {result.record_id} | case={result.case_id} | recorded_policy={result.policy_version}")
        if result.changed:
            print(f"  changed fields: {', '.join(result.changed_fields)}")
            print(f"  recorded: {result.recorded_decision}")
            print(f"  replayed: {result.replayed_decision}")
    print("Read-only demo: replay does not execute actions or modify records.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
