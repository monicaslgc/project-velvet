# Documentation index

All data in this project is synthetic. Paths are relative to this folder.

## Understand the project

| Document | Purpose |
|---|---|
| [LOGIC_GUIDE.md](LOGIC_GUIDE.md) | How each workflow decides, what the statuses mean, and where the safety boundaries sit |
| [DEMO_REFERENCE.md](DEMO_REFERENCE.md) | Every demo and policy in detail, with the commands to run them |
| [diagrams/](diagrams/) | Mermaid flow for each workflow; start with [architecture-overview.mmd](diagrams/architecture-overview.mmd) |

## Follow a scenario

| Document | Purpose |
|---|---|
| [WORKFLOW_WALKTHROUGH.md](WORKFLOW_WALKTHROUGH.md) | Guided route through the linked scenarios and design decisions |
| [SHIPMENT_REVIEW_WALKTHROUGH.md](SHIPMENT_REVIEW_WALKTHROUGH.md) | The shipment-delay scenario, end to end |
| [CASE_STUDY_WALKTHROUGH.md](CASE_STUDY_WALKTHROUGH.md) | Case studies with limitations |
| [CASE_USE_EXAMPLES.md](CASE_USE_EXAMPLES.md) | Five synthetic operational stories, expected outcomes, and commands |

## Contracts and change control

| Document | Purpose |
|---|---|
| [AGENT_PROPOSAL_CONTRACT.md](AGENT_PROPOSAL_CONTRACT.md) | Strict structured-output validation, separate from policy authorization |
| [GOVERNANCE_BOUNDARY_CONSISTENCY.md](GOVERNANCE_BOUNDARY_CONSISTENCY.md) | The proposal validator and core policy agree on versioned decisions |
| [POLICY_VERSIONING.md](POLICY_VERSIONING.md) | Version labels, candidate evaluation, regression cases, human release review |

## Contribute

| Document | Purpose |
|---|---|
| [EXTENDING_THE_DEMOS.md](EXTENDING_THE_DEMOS.md) | Checklist for adding rules, scenarios, regression tests, contracts, and diagrams |
| [../datasets/SCENARIO_CATALOG.md](../datasets/SCENARIO_CATALOG.md) | Stable scenario IDs |
