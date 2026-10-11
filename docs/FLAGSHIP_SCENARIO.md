# Flagship scenario: colour-restock incident

This page traces one fictional incident through every stage of the project, with the exact inputs and outputs. All records come from the [synthetic demo pack](../datasets/operational-demo-pack.json); the walkthrough is reproduced by `python examples/show_colour_restock_incident.py`, and each result below is asserted in [test_colour_restock_incident.py](../tests/test_colour_restock_incident.py).

## The story

A salon account places a restock order (`ord-4201`): six lines of professional colour, developer, and care products, EUR 184.50. One shade turns out to be short. Over about a day the order system and the warehouse drift apart, an out-of-order status event arrives, and an automated assistant proposes several ways to respond. The question the project answers is: **what is the assistant allowed to do, and what must a person decide?**

Everything here is fictional and illustrative. The thresholds and routing are this repository's demo rules, not any company's operating policy.

## Stage 1: lifecycle check

A warehouse event claims the order moved `PROCESSING -> SHIPPED`. The order system still shows `CONFIRMED`.

| Input | Decision |
|---|---|
| `evt-5201`, from `PROCESSING` to `SHIPPED`, order currently `CONFIRMED` at the expected version | `BLOCKED_INVALID_TRANSITION`: the event's source status does not match the order's current status |

The event is not applied and nothing is inferred about what really happened. Module: [order_lifecycle](../src/velvet/order_lifecycle.py).

## Stage 2: exception triage

The inventory system raises a reservation-versus-availability mismatch for one shade. It has now happened three times and is 26 hours old, and the customer is affected.

| Signal | Value |
|---|---|
| Category | `INVENTORY_MISMATCH` |
| Repeats / age / customer impact | 3 / 26 hours / yes |
| Result | **P1**, routed to `inventory_operations`, human review required |

Reasons reported: repeated 3 times, customer impact flagged, age over the 24-hour threshold. Module: [exception_triage](../src/velvet/exception_triage.py).

## Stage 3: reconciliation

The order system and the warehouse each report the order.

| Field | Order system | Warehouse | Severity |
|---|---|---|---|
| Total (minor units) | 18450 | 15375 | HIGH |
| Item count | 6 | 5 | MEDIUM |
| Status | CONFIRMED | CONFIRMED | matches |

A line was dropped (EUR 30.75). The comparison reports both discrepancies and requires human review; it does not decide which system is right and does not repair either one. Module: [order_reconciliation](../src/velvet/order_reconciliation.py).

## Stage 4: four agent proposals, one incident

The same incident is run with four different proposed actions. Only the proposal changes.

| Workflow | Proposed action | Governance | Workflow status |
|---|---|---|---|
| `wf-8201` | Read-only: inspect reservation history | `ALLOW` (may run) | `HUMAN_REVIEW_REQUIRED` |
| `wf-8202` | Customer communication: draft a partial-shipment notice | `REQUIRE_APPROVAL` | `HUMAN_REVIEW_REQUIRED` |
| `wf-8203` | Inventory mutation: propose a stock correction | `REQUIRE_APPROVAL` | `HUMAN_REVIEW_REQUIRED` |
| `wf-8204` | `AUTO_SUBSTITUTE_SHADE`: swap the shade without customer confirmation | `MANUAL_REVIEW` | `BLOCKED` |

What this shows:

1. **Allowed is not the same as ready.** The read-only inspection is permitted, yet the incident still needs a person because triage and reconciliation both raised flags. A harmless proposal cannot hide a risky situation.
2. **Side effects wait for approval.** Notifying the customer or changing stock is only ever a proposal; `action_executed` is `false` in every case.
3. **Unknown actions fail closed.** The substitution is not a supported action type, so it is blocked instead of being treated as the nearest known action. A shade swap changes what the customer receives, which is exactly the kind of decision that should not be inferred.
4. **Strictest outcome wins.** Across all four workflows the final status is the most restrictive result from any stage, as verified for every combination in the [scenario matrix](../tests/test_orchestrator_scenario_matrix.py).

Module: [operational_orchestrator](../src/velvet/operational_orchestrator.py).

## Run it

```bash
python examples/show_colour_restock_incident.py
python examples/run_shared_dataset.py
pytest tests/test_colour_restock_incident.py
```

## What this does not claim

It is a deterministic policy demonstration. There is no live inventory, order, or messaging system, no model making the proposals, and no approval workflow; a real implementation would need durable audit storage, authenticated approvals, and an execution layer. See the [scope boundaries](../README.md#scope-boundaries).
