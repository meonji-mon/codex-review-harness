# Codex instruction and review documents

Canonical English instructions and review documentation for a personal Codex setup. The [Korean summary](templates/instructions/summary.ko.md) is reference only; it does not change duties, approval boundaries, or exceptions.

## Authority and contents

- [AGENTS.md](templates/AGENTS.md): common duties, main modes, approval, preservation, and review triggers.
- [Agent harness](templates/instructions/agent-harness.md): scoped planning, assignment, and cleanup examples.
- [Maintenance guide](templates/guides/maintenance.md): cleanup inventory, usage/copy evidence, ancestor protection, and result reporting.
- [Reviewer contract](templates/review/reviewer-contract.md): `review/1.4` findings, evidence, and independence requirements.
- [Review dispatch](templates/review/dispatch.md): actual read-only execution, delivery evidence, and rechecks.

Astra mains retain direct planning, implementation, verification, and optional-review judgment. Claude/Grok require the user's selection for the relevant task/role. Ordinary instruction edits do not trigger agents or reviewer demonstrations. Approval, security, high-risk review, and preservation remain governed by `AGENTS.md`.

Cleanup instructions do not grant blanket deletion permission. Protected recovery history, including IDE `LocalHistory`, also blocks recursive deletion of its ancestors. Tool classifications are candidate hints; usage/reference or retained-copy evidence and the central approval rules still apply. Removed/moved bytes and net free-space change are separate measurements.

## Documentation-only synchronization

This update synchronizes the installed instruction documents and their linked guide/review contracts. Personal paths and account identifiers use the existing `${VAR}` placeholders from [.env.example](.env.example).

Runtime helpers under `harness/` and skills under `skills/` are external prerequisites, not bundled implementations. Examples such as `run_readonly_review.py`, `laya_classify.py`, `preflight.py`, `ui_change_detect.py`, and `ai_cleanup.py` require the corresponding verified local installation and contract. Missing helpers do not imply support or clearance; use the central missing-capability and required-review rules.

The bundled `templates/agents/*.toml` and `config.agents.toml` remain legacy examples and were not changed in this documentation-only update. They contain older inline role instructions. Do not install them as the current `review/1.4` runtime without reconciling the role contract and verifying actual permissions. A role-file `read-only` declaration alone is not execution evidence.

[Sources](templates/review/SOURCES.md) records historical design references. The [loading-check procedure](templates/review/SMOKE_TEST.md) is optional documentation, not an automatic test or a new execution claim. No agents or role checks were run for this publication.

## Rendering and applying documents

1. Review the templates and adapt personal preferences, tools, branding, and device names to your environment.
2. Create a local `.env` using the variable names in [.env.example](.env.example). Keep real values out of Git and never invent credentials or service identifiers for actual execution.
3. Review [render.py](render.py) before running it: its normal rendering path removes the existing `build/` tree and writes rendered templates there. `--install` additionally overwrites files under `CODEX_HOME_DIR`, including the legacy role TOMLs.
4. For a documentation-only update, copy only the reviewed rendered Markdown documents into the corresponding Codex paths. Preserve existing role files, runtime helpers, configuration, sessions, and worktrees. Do not use the full installer for this purpose.

The document destinations are `AGENTS.md`, `guides/`, `instructions/`, and `review/` under `CODEX_HOME_DIR`. Referenced helper and skill paths remain separate installations.

This synchronization was checked with in-memory placeholder rendering, local-link/anchor validation, privacy scans, and Git diff checks. The renderer/installer, cleanup tools, and agent-loading checks were not executed. Existing user files were not deleted.
