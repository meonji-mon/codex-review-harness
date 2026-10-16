# Reviewer input adapters

Use only to organize input for an already selected reviewer model. [Models/delegation](../AGENTS.md#models-and-delegation), [Reviewer contract](reviewer-contract.md), and [Main modes](../AGENTS.md#main-modes) control selection, permissions, verdicts, and applicability. This is not an assignment table. [SOURCES.md](SOURCES.md) retains sources and prior research.

## Input examples

| Selected model | Input arrangement |
|---|---|
| Luna | Small groups of changed files, direct contracts, required criteria, and original evidence; link boundary cases to inputs/states |
| Sol | Changed code, direct callers, contracts, tests, and failure paths; completion criteria cover async order, permission/data boundaries, state, and regression |
| Astra | User outcome, invariants, scope, required evidence, and stopping conditions first; connect images/flows/code to the assigned role |

Confirm model IDs, efforts, runtime version/profile/catalog, and actual calls. Use supported IDs such as `gpt-6.1-sol`/`gpt-6-astra` in packets.

## Comparison material

Keep requirements, diff, evidence, permissions, and completion criteria constant; connect chosen model/effort to actual results. Useful observations: missed defects, false blockers, unsupported claims, unauthorized writes, rechecks, and original time/token/cost records. Apply central limits and the separately installed CLI data contracts at `${CODEX_HOME_DIR}/harness/README.md` before comparison claims.
