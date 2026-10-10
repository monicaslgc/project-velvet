"""Validate the shared synthetic dataset without external dependencies."""
import json
from pathlib import Path
from velvet.demo_dataset import COLLECTIONS, validate_dataset

DATA_PATH = Path("datasets/operational-demo-pack.json")

def main() -> int:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    errors = validate_dataset(data)
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print(f"PASS: {data['dataset_id']} ({data['dataset_version']})")
    for collection in COLLECTIONS:
        print(f"- {collection}: {len(data[collection])} records")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
