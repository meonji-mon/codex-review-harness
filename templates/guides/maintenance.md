# Maintenance and work-record usage

Use for Git storage, temporary images, and major/accumulated work records. Approval/recording: [section 2](../AGENTS.md#2-execution-and-approval); cleanup/preservation: [section 6](../AGENTS.md#6-worktree-preservation); reporting: [section 8](../AGENTS.md#8-reporting-and-instruction-maintenance).

## Git storage

Measure with `git count-objects -vH` before considering ordinary garbage collection. Verify orphan locks from running processes/recent logs before handling them.

## Images and records

Check tracking, references, app assets, Notion use, and active comparisons before planning with the separately installed cleanup skill at `${CODEX_HOME_DIR}/skills/ai-cleanup/SKILL.md`.

For work records, verify connection, write permission, destination, and the existing record for the same task. Connect changes, checks, screen tags/captures, version/build, and deployment state to originals under central approval.

## Cleanup usage

Use for an explicit cleanup request or the generated-file trigger in [section 6](../AGENTS.md#generated-file-cleanup). Follow its approval boundaries and the [main mode](../AGENTS.md#main-modes); use the separately installed cleanup skill at `${CODEX_HOME_DIR}/skills/ai-cleanup/SKILL.md` for its supported categories.

1. Inventory only the relevant roots: category, logical/allocated size, age, references, and current use. Tool/cache labels and Laya classifications identify candidates; they do not prove a file is disposable. For a redundant archive, verify every retained original against its member contents, for example with SHA-256.
2. Record relevant Git/worktree state and exact protected paths before execution. Apply the central recovery-history rule to IDE `LocalHistory`, rather than treating its cache-directory location as disposal evidence.
3. For Mole, inspect the installed whitelist loader and matcher. Register concrete absolute protected roots. Query protection for each root, its descendants, and candidate ancestors, even when the protected root is currently absent; also check an eligible sibling. An unanchored `*/LocalHistory` pattern did not block removal of its Google cache ancestor. Use protection-only queries, without calling deletion functions.
4. Recheck the selected objects' identity/content and usage/copy evidence before using the authorized cleanup route. Keep changed or uncertain candidates in the record with their skip reasons; use the central confirmation path where required.
5. Compare protected paths and project state afterward. Distinguish moved-to-Trash files, removed logical/allocated bytes, tool estimates, and net free-space change. If a protected path is missing, stop further cleanup and record the incident and actual recovery status.
