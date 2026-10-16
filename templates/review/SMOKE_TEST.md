# Reviewer loading check

Use only when the user requests role-loading verification or a runtime change creates a concrete need. Apply [section 7](../AGENTS.md#7-review-triggers-and-holds), [model opt-in](../AGENTS.md#models-and-delegation), and [Reviewer contract](reviewer-contract.md). This document alone does not trigger calls.

Check only the requested/needed installed reviewer roles for actual loading, selected model/effort, read-only permissions, and supported isolation. This is not a product PASS/BLOCK review.

## Scope and evidence

Main reads `AGENTS.md`, `review/reviewer-contract.md`, `review/activation.md`, `review/dispatch.md`, the selected `agents/<role>.toml`, and needed `config.toml` agent entries, all under `${CODEX_HOME_DIR}/`. Record paths of applicable project `AGENTS.override.md` or same-named role files.

Reviewer material: `${CODEX_HOME_DIR}/review/SMOKE_EVIDENCE.md`. Inspect only this run's parent/child rollouts under `sessions/`.

## Procedure

For a full-access main, use the dedicated read-only path. A verified read-only parent may call roles directly and compare original records.

```sh
python3 ${CODEX_HOME_DIR}/harness/run_readonly_review.py --roles code_reviewer --smoke --cwd <absolute-workspace> --output <new-report.json>
```

Only when both roles are requested/needed, replace roles with `--roles ui_reviewer code_reviewer`.

1. Read scoped files.
2. Call each selected role once with supported explicit model/effort and `fork_turns="none"`; default Sol/high unless central selection specifies otherwise.
3. Have it read the fixture and return role ID, marker, and whether product files changed.
4. Match the parent/child originals using [Activation](activation.md). Record failed/unknown observations and apply central stopping rules.

## Record

Fill every relevant row with evidence or `UNVERIFIED`; evidence collection does not imply independent review clearance.

| Item | Result | Path/field/session evidence |
|---|---|---|
| Files | | |
| Selected role registration | | |
| Actual role call (`session_meta.agent_role`) | | |
| Applied loader and full contract/method read/delivery | | |
| Child model/effort (`turn_context`) | | |
| Sandbox and filesystem read-only | | |
| Context creation and parent-conversation copying | | |
| Procedural independence | CONFIRMED / UNVERIFIED / UNSUPPORTED | |
| Read marker | | |

Briefly state unknown items and reasons.
