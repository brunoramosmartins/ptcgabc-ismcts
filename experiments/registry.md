# Experiment Registry

Every experiment MUST be registered here BEFORE running. One row per experiment.

## Schema

| Field | Meaning |
|---|---|
| ID | `EXP-XXX` (zero-padded, monotonically increasing) |
| Phase | Which roadmap phase requested it |
| Hypothesis | H1 / H2 / H3 / H4 / exploratory / variance |
| Objective | One sentence — what question does it answer? |
| Configuration | Agents, seeds, N matches, deck version, git tag |
| Expected result | What outcome would confirm/reject the hypothesis? |
| Actual result | Filled in after the run — Wilson CI, p-value, verdict |

## Ledger

| ID | Phase | Hypothesis | Objective | Configuration | Expected | Actual |
|---|---|---|---|---|---|---|
| _ | _ | _ | _ | _ | _ | _ |
