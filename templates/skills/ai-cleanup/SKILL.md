---
name: ai-cleanup
description: Plan, trash, encrypt, verify, and restore AI-created backups, test/scratch outputs, build artifacts, and unused images under the central cleanup scope.
---

# Cleanup usage

[AGENTS.md sections 2, 6, and 9](../../AGENTS.md) own applicability, owner, approval categories, confirmation, preservation, and reporting. Use these commands only within that scope.

Script: `python3 ${CODEX_HOME_DIR}/skills/ai-cleanup/ai_cleanup.py`.
Local configuration: adjacent `cleanup.toml`, adapted from [cleanup.example.toml](cleanup.example.toml). The example has no candidate globs, image extensions, project roots, archive destination, or recipient. It grants no cleanup permission.
Records: `~/.codex/maintenance/cleanup-plan-*.json`, `cleanup.jsonl`, `archive-<plan_id>.json`, and the managed Trash `restore.json`.

## Setup and non-destructive checks

Requires Python 3.11+, Git, an installed Mole matcher, and its persistent whitelist. Moving/restoring also requires the supported macOS exclusive-rename API and a same-filesystem destination. Archive/backup stages additionally require age, gitleaks, zstd, authenticated gh, a verified private destination, and local keys.

Merge only reviewed entries from [mole-whitelist.example](mole-whitelist.example) into the existing `~/.config/mole/whitelist`, after rendering `USER_HOME` to an absolute path. Preserve existing entries; add project, SDK, simulator, and custom IDE/recovery roots locally. Keep the actual whitelist, configuration, keys, manifests, journals, and personal evidence out of Git.

From this skill directory:

```sh
python3 -B verify_non_destructive.py
CLEANUP_TEST_LIVE_MOLE=1 python3 -B verify_non_destructive.py
```

The first command uses memory-only transfer/journal I/O. The second also queries the installed Mole policy without running cleanup. The runner rejects real filesystem mutations, native move calls, and subprocesses other than the fixed protection query. It does not prove actual move/restore or power-loss recovery. Independent review of destructive paths remains required under section 7; these tests do not grant execution clearance.

## Automatic path

```sh
python3 ${CODEX_HOME_DIR}/skills/ai-cleanup/ai_cleanup.py --auto
```

The script plans/processes automatic categories and checks the daily limit from the last `stage: auto` record. Link `summary`, destination, `restore` command, and `confirm_tier_by_category`.

Trash: `~/.Trash/ai-cleanup-<id>/`; fallback `~/.codex/maintenance/trash/ai-cleanup-<id>/`. Automatic execution moves files only. Old managed Trash is reported and never permanently deleted by this script; permanent deletion is a separate task under central approval. Restore works only while recorded data exists and passes verification; there is no guaranteed retention period. Plan and dry-run modes write local metadata, so use the test runner when no filesystem mutations are allowed.

## Protection and move records

`cleanup_safety.py` queries the installed Mole matcher and persistent whitelist, including protected ancestors. Configured `never_touch` roots are checked in both directions as well. Missing policy, missing required IDE rules, query errors, or policy changes hold candidates. Version-independent Android Studio/JetBrains roots intentionally preserve their entire system directories, including rebuildable indexes. Broad existing protections may also hold otherwise eligible generated outputs.

New plans bind device/inode, parent identity, nanosecond metadata, tree membership, content SHA-256, and policy/configuration/code revision. Legacy plans require replanning. Source/Git/copy checks run again immediately before moving. Moves refuse cross-device copy-and-delete, unsupported platforms, and destination overwrites.

Each `restore.json` entry is flushed/fsynced as `intent` before moving, then updated after destination verification. A record-write failure stops further work. Interrupted intents preserve both locations for reconciliation; an absent source alone is not success. Restore checks actual locations, expected content/identity, and the original parent, and never overwrites. Legacy restore records explicitly retain their missing historical identity evidence.

## Plan, archive, verify, move

1. **Plan:** no stage argument or `--stage plan`; `--no-images` skips project/generated-image inspection. Read `plan_id`, counts/bytes, `needs_user_confirm`, `limits_exceeded`, and `tools`.
2. **Archive:** `--stage archive --plan <file>`. Stream tar → zstd → age, scan manifests, upload to the configured private destination, and verify the re-download.
3. **Verify:** `--stage verify --plan <file>`. Match re-downloaded SHA-256 and privately decrypted member lists. Missing prerequisites preserve the originals.
4. **Move:** `--stage delete --plan <file> --confirm <plan_id>`. `--only-category backup` narrows the selection; `--allow-large` requires approved large scope. Central approval/stopping/preservation rules apply.

For a required pre-change backup, use `--stage backup --path <files-or-folders> --reason <reason>` with the same encrypted upload and verification. Restore only needed files using the configured key; keep private keys out of source and output.

## Images and output

Inspect image names and sets in source/documents/manifests. Dynamic paths remain uncertain. A retained imagegen copy needs matching SHA-256.

Report the plan ID/file, category/action counts and bytes, confirmation scope, skip reasons, actual destination, and `--stage restore --id <id>`. Preserve original failures and distinguish simulated checks from real filesystem evidence.
