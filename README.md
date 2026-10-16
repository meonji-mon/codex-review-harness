# Codex instructions, review documents, and cleanup safety helpers

Canonical English instructions and review documentation for a personal Codex setup. The [Korean summary](templates/instructions/summary.ko.md) is reference only; it does not change duties, approval boundaries, or exceptions.

## Authority and contents

- [AGENTS.md](templates/AGENTS.md): common duties, main modes, approval, preservation, and review triggers.
- [Agent harness](templates/instructions/agent-harness.md): scoped planning, assignment, and cleanup examples.
- [Maintenance guide](templates/guides/maintenance.md): cleanup inventory, usage/copy evidence, ancestor protection, and result reporting.
- [Cleanup skill](templates/skills/ai-cleanup/SKILL.md): shared Mole protection, rechecked Trash moves, durable recovery journals, and non-destructive regression checks.
- [Reviewer contract](templates/review/reviewer-contract.md): `review/1.4` findings, evidence, and independence requirements.
- [Review dispatch](templates/review/dispatch.md): actual read-only execution, delivery evidence, and rechecks.

Astra mains retain direct planning, implementation, verification, and optional-review judgment. Claude/Grok require the user's selection for the relevant task/role. Ordinary instruction edits do not trigger agents or reviewer demonstrations. Approval, security, high-risk review, and preservation remain governed by `AGENTS.md`.

Cleanup instructions do not grant blanket deletion permission. Protected recovery history, including IDE `LocalHistory`, also blocks recursive deletion of its ancestors. The shared helper queries Mole's installed matcher and persistent whitelist; missing required protections hold candidates. Automatic cleanup never empties Trash. Tool classifications are candidate hints; usage/reference or retained-copy evidence and central approval still apply. Removed/moved bytes and net free-space change are separate measurements.

## Bundled scope and local configuration

Canonical instruction documents use the existing `${VAR}` placeholders from [.env.example](.env.example). The cleanup skill includes the runtime modules and a [configuration example](templates/skills/ai-cleanup/cleanup.example.toml) with empty candidate scope and archive credentials. Actual configuration, whitelist contents, keys, manifests, journals, and personal verification records are excluded.

Helpers under `harness/` and skills other than `ai-cleanup` remain external prerequisites. Examples such as `run_readonly_review.py`, `laya_classify.py`, `preflight.py`, and `ui_change_detect.py` require verified local installations. Missing helpers do not imply support or clearance; use the central missing-capability and required-review rules. The bundled cleanup helper still requires an installed Mole matcher and a reviewed local policy.

The bundled `templates/agents/*.toml` and `config.agents.toml` remain unchanged legacy examples with older inline role instructions. Do not install them as the current `review/1.4` runtime without reconciling the role contract and verifying actual permissions. A role-file `read-only` declaration alone is not execution evidence.

[Sources](templates/review/SOURCES.md) records historical design references. The [loading-check procedure](templates/review/SMOKE_TEST.md) is optional documentation, not an automatic test or a new execution claim. No agents or role checks were run for this publication.

## Rendering and applying reviewed files

1. Review the templates and adapt personal preferences, tools, branding, and device names to your environment.
2. Create a local `.env` using the variable names in [.env.example](.env.example). Keep real values out of Git and never invent credentials or service identifiers for actual execution.
3. Review [render.py](render.py) before running it: its normal rendering path removes the existing `build/` tree and writes rendered templates there. `--install` additionally overwrites files under `CODEX_HOME_DIR`, including the legacy role TOMLs.
4. Copy only reviewed files for the intended scope. Preserve existing role files, configuration, sessions, and worktrees. For cleanup, adapt `cleanup.example.toml` to an ignored local `cleanup.toml` and merge reviewed whitelist additions without replacing existing protections. Follow the skill's setup and central approval/review conditions before execution. Do not use the full installer for a selective update.

Document destinations are `AGENTS.md`, `guides/`, `instructions/`, and `review/` under `CODEX_HOME_DIR`; the cleanup package belongs in `skills/ai-cleanup/`. Other referenced helpers/skills remain separate installations.

## Non-destructive verification and limits

```sh
python3 -B templates/skills/ai-cleanup/verify_non_destructive.py
CLEANUP_TEST_LIVE_MOLE=1 python3 -B templates/skills/ai-cleanup/verify_non_destructive.py
```

The default suite uses in-memory transfer/journal I/O; live-policy mode additionally queries installed Mole protections. The runner blocks real filesystem mutations and native move calls. These checks do not establish actual Trash moves, restores, cross-volume behavior, or power-loss recovery. They do not replace required independent review or grant merge, release, or cleanup execution approval; central conditions still apply.

The renderer/installer, actual cleanup/move/restore stages, app shutdown, and agent-loading checks are outside this publication's verification scope. No personal whitelist or operational evidence is bundled.
