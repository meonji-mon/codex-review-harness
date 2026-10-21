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

## Claude Code harness (`claude/`)

**Runtime status: UNVERIFIED.** Authenticated Claude Code reviewer execution, actual model/effort delivery, and integrated enforcement have not passed a live review. This configuration is published with that limitation; publication is not a reviewer PASS or actual-cleanup approval. No further login, model calls, deletion, or UI reviewer calls were used for this update.

A Claude Code port of the same rules, written in Korean: [CLAUDE.md](claude/CLAUDE.md) restates common duties and points to the Codex guides, reviewer contract, and skill scripts. Agent frontmatter records requested OpenCodex models/effort; actual routing and application require execution records. Skills are thin wrappers around the Codex installations.

`code-reviewer` has only `Read`, `Grep`, and `Glob`, with no Bash, MCP, edit, skill, or agent tools. For macOS execution evidence, [run_code_review.py](claude/scripts/run_code_review.py) prepares a separate macOS read-only Claude Code dispatcher and one native `code-reviewer`. The dispatcher requests Sol/low; reviewer model/effort default to its frontmatter (Astra/high), with explicit per-run overrides. Normal main permissions and settings stay unchanged by the runner. The worker's intended writable scope is its isolated run state and per-run Claude transcript namespace. Kernel queries inspect permissions without write probes. The collector is not a verified end-to-end review path yet. It uses the normal `ocx claude` authentication environment and never records credential values or selects accounts.

```sh
python3 claude/scripts/run_code_review.py --repo <absolute-repo> --brief <redacted-brief> --run-dir <new-private-directory-outside-repo> --reviewer-model claude-sonnet-5-5 --reviewer-effort high
python3 -B claude/tests/test_guards.py
python3 -B claude/tests/test_model_selection.py
```

### Model and effort selection

Claude Code supports `/model`, `/effort`, startup `--model`/`--effort`, and subagent frontmatter `model`/`effort`. The effort environment variable takes precedence over frontmatter. A gateway/custom ID may not receive all native capability controls; do not fabricate `behavesAs` or claim equivalent reasoning across models. See [official model settings](https://code.claude.com/docs/en/model-config#adjust-effort-level) and [subagent effort](https://code.claude.com/docs/en/sub-agents#choose-an-effort-level).

These commands only read metadata or preview settings; they do not invoke a model, log in, or change files:

```sh
python3 claude/scripts/run_code_review.py --list-models
python3 claude/scripts/run_code_review.py --print-model-picker
python3 claude/scripts/run_code_review.py --reviewer-model claude-opus-5-5 --reviewer-effort max --show-selection
```

The picker snippet uses the documented user-level `modelPicker.options` schema and adds advertised OpenCodex choices alongside built-ins. Merge only `modelPicker` into your user settings; keep permissions, hooks, credentials, and the default model. Labels do not prove routing or capability. It never sets `behavesAs` or fabricated capability flags. [Official picker schema](https://code.claude.com/docs/en/settings-reference#modelpicker)

The reviewer adapter accepts explicit catalog models and `low`, `medium`, `high`, `xhigh`, or `max`; availability of a level on the actual model remains unverified. Selecting a main model does not select another agent. Grok remains instruction-writing only, Terra is excluded, and automatic/combo routes are not code-reviewer choices. Unsupported selections fail without substitution. Model/effort overrides never broaden role permissions or run agents by themselves.

Run directories retain the fixed packet, hashes, native stream/transcripts, and kernel permission evidence. Execution success alone is not review clearance: inspect actual Agent calls, full contract/packet reads, OpenCodex request records for model/effort, the reviewer verdict, and unchanged source. Recheck affected scope with the original reviewer when needed. Unsupported platforms/routing or unknown settings cannot pass mandatory review. This execution path requires the installed Claude Code CLI options (verified against 2.1.293) and macOS sandbox support; it never falls back to another model.

Hooks remain supplementary. `git-guard.sh` recognizes absolute Git paths, global options, compound commands and common shell wrappers. It does not fully sandbox arbitrary programs. `reviewer-readonly-guard.sh` accepts a narrow local-read command list and rejects interpreters, compound commands, redirects and all `gh` calls, including implicit POST/GraphQL requests. Neither hook executes the command it inspects. Malformed input is denied; interpreter/helper failures exit 2. `impact-reminder.sh` remains a non-blocking reminder. These changes do not claim that UI/browser tools or other agents have been runtime-validated.

Install (review first; nothing here overwrites settings automatically):

```sh
cd claude
for f in $(find . -type f); do mkdir -p ~/.claude/$(dirname $f); sed -e "s|\${CODEX_HOME_DIR}|$HOME/.codex|g" -e "s|\${USER_HOME}|$HOME|g" $f > ~/.claude/$f; done
chmod +x ~/.claude/hooks/harness/*.sh
```

Then merge the two `PreToolUse` entries from `~/.claude/settings.hooks.json` into the existing `hooks.PreToolUse` array of `~/.claude/settings.json` (append; keep other hooks), validate with `python3 -m json.tool`, and start Claude Code with `ocx claude`. The collector currently has no completed authenticated reviewer run; isolated kernel permissions were observed, but reviewer model/effort and product verdict remain unverified. Normal Claude authentication must already work.

Existing files with the same names are overwritten by the loop above; skip files you maintain yourself. For a selective update, copy only reviewed changed files, including `guard.py` beside both hook entrypoints. Do not replace settings or copy private run records into the repository. Other agents' routing, effort and live hooks remain unverified until separately evidenced.
