"""Execute the shared synthetic data pack across five demo policy modules."""
import json
from pathlib import Path

from velvet.demo_dataset import validate_dataset
from velvet.shared_scenarios import evaluate_shared_pack


def main() -> int:
    path = Path("datasets/operational-demo-pack.json")
    pack = json.loads(path.read_text(encoding="utf-8"))
    errors = validate_dataset(pack)
    if errors:
        for error in errors:
            print(f"DATASET ERROR: {error}")
        return 1

    results = evaluate_shared_pack(pack)
    print(f"Dataset: {pack['dataset_id']} v{pack['dataset_version']} (synthetic only)")
    print(f"Evaluated {len(results)} records across {len(set(row['demo'] for row in results))} demos")
    print()
    for row in results:
        print(f"[{row['demo']}] {row['scenario_id']} | {row['record_id']} | {row['decision']}")
        print(f"  {row['detail']}")
    print()
    print("Read-only evaluation complete: no order data changed and no action was executed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
