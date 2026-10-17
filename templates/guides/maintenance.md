# Maintenance and work-record usage

Use for Git storage, temporary images, and major/accumulated work records. Approval/recording: [section 2](../AGENTS.md#2-execution-and-approval); cleanup/preservation: [section 6](../AGENTS.md#6-worktree-preservation); reporting: [section 8](../AGENTS.md#8-reporting-and-instruction-maintenance).

## Git storage

Measure with `git count-objects -vH` before considering ordinary garbage collection. Verify orphan locks from running processes/recent logs before handling them.

## Git recording example

Use [section 6](../AGENTS.md#git-recording) for branch choice, approval, and recording duties. A documentation-only commit can use:

```text
docs: clarify Git recording defaults

Why: keep ordinary changes easy to save while preserving required review.
Verification: relevant documents reread; tests not run for this documentation-only change.
```

## Images and records

Check tracking, references, app assets, Notion use, and active comparisons before planning with the [cleanup skill](../skills/ai-cleanup/SKILL.md), installed at `${CODEX_HOME_DIR}/skills/ai-cleanup/SKILL.md`.

For work records, verify connection, write permission, destination, and the existing record for the same task. Connect changes, checks, screen tags/captures, version/build, and deployment state to originals under central approval.

## Cleanup usage

Use for an explicit cleanup request or the generated-file trigger in [section 6](../AGENTS.md#generated-file-cleanup). Follow its approval boundaries and the [main mode](../AGENTS.md#main-modes); use the [cleanup skill](../skills/ai-cleanup/SKILL.md) for its supported categories and commands. Its public configuration is an empty-scope example; retain personal scope and settings locally.

1. Inventory only the relevant roots: category, logical/allocated size, age, references, and current use. Tool/cache labels and Laya classifications identify candidates; they do not prove a file is disposable. For a redundant archive, verify every retained original against its member contents, for example with SHA-256.
2. Record relevant Git/worktree state and exact protected paths before execution. Apply the central recovery-history rule to IDE `LocalHistory`, rather than treating its cache-directory location as disposal evidence.
3. Query the installed Mole matcher and persistent whitelist through the shared cleanup protection helper. Register concrete absolute roots, plus anchored Android Studio/JetBrains version patterns from the skill's example; keep custom IDE paths local. Query roots, descendants, candidate ancestors, and an eligible sibling, even when a protected root is absent. Missing rules/query errors hold candidates. Broad IDE roots intentionally hold rebuildable cache siblings too. An unanchored `*/LocalHistory` pattern did not block its Google cache ancestor.
4. Use plans bound to source identity/content/tree and policy revision. Immediately before the authorized Trash move, persist recovery intent and rerun source/Git/copy checks. Keep changed or uncertain candidates with skip reasons. Journal errors stop further work; unsupported/cross-device/overwrite moves are refused. The skill describes the supported transfer and restore procedure.
5. Compare protected paths and project state afterward. Distinguish moved-to-Trash files, removed logical/allocated bytes, tool estimates, and net free-space change. Report old managed Trash without emptying it; central approval governs any separate permanent-deletion task. If a protected path is missing, stop and record the incident and actual recovery status. Reconcile interrupted journal entries against both locations rather than inferring success from an absent source.

For verification without cleanup or metadata writes, use the skill's `verify_non_destructive.py`. Its live-policy mode only queries Mole. Simulated transfer/journal tests do not establish actual move/restore or power-loss recovery, and do not replace required independent review.
