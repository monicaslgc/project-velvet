# Shipment Review Walkthrough

This example links exception triage, order reconciliation, action governance, and orchestration around one fictional delayed shipment.

## Scenario

Order `ord-4105` has a shipment-delay exception aged 30 hours with customer impact. The expected order status is `CONFIRMED`, while a second synthetic snapshot reports `SHIPPED`. A proposed customer update is included in the scenario.

## How the workflow evaluates it

1. **Triage** assigns operational priority based on the supplied category, age, and customer-impact fields.
2. **Reconciliation** reports the status mismatch without assuming which snapshot is authoritative.
3. **Governance** identifies customer communication as an approval-gated action.
4. **Orchestration** combines the findings into one structured report and preserves the human-review requirement.

## Run it

From the repository root:

```bash
python examples/show_shipment_review.py
python examples/run_shared_dataset.py
pytest tests/test_exception_triage.py tests/test_order_reconciliation.py tests/test_workflow_governance.py tests/test_operational_orchestrator.py
```

## Expected behavior

The report includes the triage result, the status discrepancy, and the reason customer communication cannot proceed autonomously. No message is sent, no order is modified, and no external system is contacted.

## Boundaries

The records and rules are synthetic. The example demonstrates how deterministic decisions can be combined; it does not establish real operating policies, measure business outcomes, or provide a live commerce integration.
