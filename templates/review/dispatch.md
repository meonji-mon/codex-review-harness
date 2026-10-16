# Review dispatch and handoff

Use only for section 7 required review or a concrete optional-review need, not model registration/instruction changes alone. [Triggers/holds](../AGENTS.md#7-review-triggers-and-holds), [model opt-in](../AGENTS.md#models-and-delegation), and [Reviewer contract](reviewer-contract.md) are authoritative.

## Prepare input

Add user outcome, preservation, changed files, and Done when to the existing brief. Link commit, staged/unstaged diff, related untracked files, settings/environment/build, and originals. UI starts from requirements/references/screens/interactions; code from requirements/diff/direct contracts/tests/traces. Describe failures as observations/reproduction conditions; link full attempts with [Packet template](packet-template.md).

Supply the reviewer contract, assigned [UI](ui-reviewer.md)/[code](code-reviewer.md) method, and narrow packet. Role TOMLs are reference loaders. Reuse actual-delivery records instead of reattaching supplied bodies. Use [Activation](activation.md) for the three role/creation/input grounds; unknown/unsupported grounds remain unknown/unsupported. Advisory inspection does not replace mandatory independent review.

Do not assign reviewers implementation, planning, or broad exploration, or change account/MCP/OpenCodex settings merely to apply this structure. For high-risk code, provide protection conditions and failure paths.

<a id="읽기-전용-실행-경로"></a>
## Read-only dispatch

In app `0.162.0-alpha.17.2`, role-file copying does not apply sandbox/profile settings. A full-access parent's `spawn_agent` alone cannot set read-only; use a separate read-only dispatcher.

From unchanged main permissions, code-only review is one command and the default role:

```sh
python3 ${CODEX_HOME_DIR}/harness/run_readonly_review.py --roles code_reviewer --cwd <absolute-project> --brief-file <brief> --output <new-report.json>
```

Only if both roles are needed, explicitly set `--roles ui_reviewer code_reviewer`. Omitting roles never adds UI. For requested loading checks, use `--smoke` instead of `--brief-file`.

The tool manages the read-only dispatcher and fresh-role calls. Compare requested roles, model/effort, and `fork_turns="none"` with actual children. Do not lower global/main permissions or write new dispatch scripts for each review. Report unsupported requests without substitution.

`--reviewer-model` accepts `gpt-6-astra`, `gpt-6.1-sol`, `anthropic/claude-sonnet-5-5`, or `anthropic/claude-opus-5-5`; `--reviewer-effort` sets requested effort. Default: Sol/high. The separate dispatcher is Sol/low for Astra/Sol review, or selected Claude/low for Claude review; always read-only, with unchanged main settings. For different models per role, use separate commands tied to the same snapshot.

Examples: `--roles code_reviewer --reviewer-model gpt-6-astra --reviewer-effort xhigh`; user-selected, needed Claude review: `--roles code_reviewer --reviewer-model anthropic/claude-sonnet-5-5 --reviewer-effort high`. Apply central selection/escalation conditions; do not default to low reviewer effort. CLI options, main model, or prior tests do not prove human selection/approval. Unsupported choices fail before execution; runtime unsupported/mismatched choices never pass or silently fall back. Observed model/effort are Codex routing values, not unverified provider-internal mappings.

Native encrypted V2 dispatch to a Claude worker has produced `unreadable_encrypted_agent_task`. Readable tasks from a Claude dispatcher were confirmed for worker/code-review paths. The review tool sends approved packet path/SHA256/run ID as a readable task. Verify dispatcher model/low/read-only, readable spawn reference, linked delivery, and full packet read. Per-run TOML path-only binding failed to resolve transport; successful code review did not use it. Never change global roles/main settings or decrypt content for this path.

Main supplies a redacted narrow brief. The tool fixes a packet with run ID, contract/method references, and brief; children read the whole file. `requested_reviewer` is a request; child `contexts` are observations. Packets/reports are owner-only, never overwritten. Bind brief/contract/output/current source; changed relevant state needs refreshed evidence under central conditions.

JSON `validation_result` proves execution/loading/delivery only. Product verdict, approval, and complete input independence remain separate.

### Recheck

If a V2 child cannot resume directly through CLI, restore the existing read-only parent first, then `followup_task` the original role path/ID with only changed scope. Do not create replacements automatically.

```sh
codex --no-daemon exec --sandbox read-only --model <original-dispatcher-model> -c 'model_reasoning_effort="low"' resume --json --skip-git-repo-check <original-parent-id> -
```

Link original reviewer ID, diff, current source/check ledger; observe same ID/model/permissions again. Preserve initial and recheck records separately in the persistent work-record location.

## Integrate results

Main's original checks/builds/interactions/captures belong in `checks_ref`. Default `evidence-only`; isolated UI needs `isolated-ui`, designated operation paths, and shared-state ownership.

Reviewers use the same snapshot. Static reads may run in parallel; shared simulators/browser/profilers run serially. Refresh affected judgments/checks after changes.

Compare original returns, evidence, and independence; merge duplicates and resolve conflicts from inputs/state/time. Another review's pass never erases a defect. Implementers fix; the original reviewer rechecks only changed/affected scope. If replaced, record the replacement and same-scope handoff. Supply missing evidence rather than extra roles/repetitions.

Report actual verdicts, key evidence, and why any role was omitted.
