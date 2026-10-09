"""Run the synthetic workflow governance examples."""
import json
from pathlib import Path
from velvet.workflow_governance import ProposedAction, evaluate_action

def main() -> None:
    fixture = Path(__file__).with_name("governance.json")
    actions = json.loads(fixture.read_text(encoding="utf-8"))
    for item in actions:
        decision = evaluate_action(ProposedAction(**item))
        print(
            f"{decision.action_id}: {decision.outcome.value} "
            f"(allowed_to_execute={decision.allowed_to_execute}, "
            f"approval_required={decision.approval_required})"
        )
        for reason in decision.reasons:
            print(f"  - {reason}")

if __name__ == "__main__":
    main()
