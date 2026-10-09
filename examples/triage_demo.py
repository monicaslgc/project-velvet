"""Run the synthetic Order Exception Triage example."""
import json
from pathlib import Path
from velvet.exception_triage import OrderException, triage_exception

def main() -> None:
    scenarios = json.loads(Path(__file__).with_name("exceptions.json").read_text(encoding="utf-8"))
    for scenario in scenarios:
        decision = triage_exception(OrderException(**scenario))
        print(f"{decision.exception_id}: {decision.priority} -> {decision.assigned_team} (human review: {decision.human_review_required})")
        print(f"  Reason: {' '.join(decision.reasons)}")
        print(f"  Next step: {decision.recommended_action}")

if __name__ == "__main__":
    main()
