import json
from pathlib import Path

from examples.validate_demo_dataset import validate_dataset

def load_pack():
    return json.loads(Path("datasets/operational-demo-pack.json").read_text(encoding="utf-8"))

def test_shared_dataset_is_valid_and_cross_referenced():
    assert validate_dataset(load_pack()) == []

def test_dataset_must_be_explicitly_synthetic():
    data = load_pack()
    data["synthetic_data_only"] = False
    assert any("synthetic_data_only" in error for error in validate_dataset(data))

def test_dataset_rejects_unknown_order_references():
    data = load_pack()
    data["exceptions"][0]["order_id"] = "ord-does-not-exist"
    assert any("unknown order_id" in error for error in validate_dataset(data))

def test_dataset_rejects_duplicate_identifiers_within_collection():
    data = load_pack()
    data["orders"].append(dict(data["orders"][0]))
    assert any("duplicate primary identifiers" in error for error in validate_dataset(data))
