# Shared synthetic demo dataset

This folder contains a small, linked, deterministic dataset that can be reused across Project Velvet demos. It is designed for portfolio walkthroughs and automated tests, not production use.

## Files
- `operational-demo-pack.json`: canonical cross-demo fixture pack.
- `SCENARIO_CATALOG.md`: scenario IDs, expected learning points, and which demos can use each scenario.

## Data principles
- All order IDs, exception IDs, event IDs, actors, source names, amounts, and operational details are fictional.
- No real customer, employee, supplier, payment, or platform data is included.
- Currency amounts use integer minor units (for EUR, cents).
- The data is intentionally mixed: valid, stale, inconsistent, high-risk, and unknown cases.
- Expected outcomes describe the current illustrative rules in this repository. They are not real-world operational policy.
- The pack is a shared source of examples; individual demos may keep smaller focused fixtures for quick starts. When fixtures diverge, update the pack and document why.

## Use
Read the JSON with Python's standard library:

```python
import json
from pathlib import Path

pack = json.loads(Path("datasets/operational-demo-pack.json").read_text(encoding="utf-8"))
print(len(pack["orders"]), len(pack["lifecycle_events"]))
```

Do not interpret a synthetic source label as an assertion that any real system is authoritative.
