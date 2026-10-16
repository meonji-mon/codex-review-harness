# Planning and assignment usage

Use for needed plan, assignment, optional-review, cleanup, or call-path formats. [AGENTS.md](../AGENTS.md) owns duties, [main modes](../AGENTS.md#main-modes), [plans](../AGENTS.md#applying-these-instructions), and [assignment](../AGENTS.md#models-and-delegation). [Reviewer contract](../review/reviewer-contract.md) owns review details.

## Plan examples

The main writes the plan, including an Astra main. Localize labels to the user's language. Four bullets mean four actual lines, not visual wrapping.

```text
- Goal: block non-owner access while preserving owner access
- Scope: authorization function, direct callers, and related tests
- Order: reproduce → minimal fix → required independent code review
- Verification: allowed, denied, and error paths; resolve review findings
```

Proceed after the explanation when approval is unnecessary. Small-work example: “I will update the requested copy and check its translations and actual screen.”

For a navigation bug, use the same four-line form: goal = preserve filters after Back; scope = list/filter state and related tests; order = reproduce and trace state before fixing; verification = original path and adjacent search/sort flows.
For high-risk screen changes, connect required UI review as well as code review under the central trigger.
Plan-change example: “Shared-state initialization causes the reset. I will fix its condition and check the two screens sharing that state.”

## Cleanup example

For a cleanup request or the generated-file trigger in [section 6](../AGENTS.md#generated-file-cleanup), use [maintenance cleanup usage](../guides/maintenance.md#cleanup-usage). The central rules determine owner, automatic categories, approval, and limits; this example grants no additional deletion or model scope.

```text
- Goal: reclaim space from verified disposable files
- Scope: approved cleanup targets; preserve current work, recovery history, and protected paths
- Order: inventory and usage/copy evidence → protection-only path checks → authorized cleanup
- Verification: compare project/protected-path baselines; report removed/moved bytes separately from free-space change
```

## Assignment examples

Apply the [central priority table](../AGENTS.md#models-and-delegation), without adding gates.

- A one-file payment/authorization change: risk first; main directly or a needed eligible high+ implementer, then required review. Claude appears only when selected for that role. Astra retains direct implementation authority.
- Unknown cause: establish reproduction/hypotheses first; small scope alone does not justify handing cause analysis to Sol Light.
- Overlapping writes: main sets ownership/order and serializes.
- Independent non-high-risk translation groups with clear Done when: delegate to Sol Light only if there is meaningful delegation value.
- Small edits/plans: main directly; no automatic effort escalation or planning agent.
- User-selected Claude: either Sonnet or Opus may fill any allowed role. A main-model choice does not select extra Claude subagents. Connect the central selection condition, rationale, and unknowns.
- Fixed-role/model mismatch: use eligible `worker`/`default` with a narrow brief, not a fixed-role TOML override. Review keeps its dedicated read-only path; Baton stays Sol Light.
- Ordinary copy/instruction edits: main checks the documents/relevant results and finishes. Model availability alone does not trigger review or demonstrations.

## Brief format

Add needed fields to the existing task message:

```text
Goal / Done when:
Owned files / prohibited scope / references:
Actual agent_type / model / effort / selection rationale:
Order / checks / expected results / failure boundary:
Original evidence / remaining issues:
```

Give Sol Light numbered action/check steps. For parallel writes, high risk, or capacity concerns, connect dependencies, approval, support, and capacity evidence.

| Role | Use/output |
|---|---|
| explorer / librarian | Local locations / official and upstream contracts |
| metis / plan / momus | Undefined-decision analysis / executable plan / completion-evidence review |
| sol_light_worker / luna_worker | Owned implementation, checks, issue report |
| worker / default | Narrow implementation or instruction/plan artifact with an eligible model |
| ui_reviewer / code_reviewer | Assigned review findings and evidence |
| cleanup_worker | Approved cleanup summary |

### User-selected Claude

Use this example only when the user selects this subagent role and delegation is needed.

```text
spawn_agent: agent_type=worker, model=anthropic/claude-opus-5-5, reasoning_effort=high, fork_turns=none
Goal / Done when: update one instruction file's examples; reread against central conditions
Owned file: <one absolute path>
Prohibited: other files, settings, remote writes, extra agent calls
User selection / delegation value: <role-specific choice and concrete benefit>
Failure boundary: report ambiguity/mismatch without guessing or editing
```

An instruction/plan owner writes only the assigned artifact, not product patches. One-file ownership is a brief constraint, not a technical sandbox. A full-access parent's child may have full access; compare actual permissions and changed files to records.

For user-selected Claude code review that is needed under section 7, use [read-only dispatch](../review/dispatch.md#read-only-dispatch):

```sh
python3 ${CODEX_HOME_DIR}/harness/run_readonly_review.py --roles code_reviewer --reviewer-model anthropic/claude-opus-5-5 --reviewer-effort high --cwd <absolute-project> --brief-file <brief> --output <new-report.json>
```

### Unreadable routed task input

Only for needed, user-selected Claude delegation: native encrypted V2 tasks have failed on this route. Do not repeat unchanged calls or decrypt input. Main prepares a fixed, approved narrow packet; a separate Claude dispatcher sends its path, SHA256, run ID, and role as a readable task. It assigns only the chosen worker and returns the original result, without changing main/global settings.

```text
Dispatcher: selected Claude/low, approved worker permissions
Worker: worker, selected Claude/high, fork_turns=none
Readable task: packet absolute path + SHA256 + run ID + role; read the whole packet first
Review: run_readonly_review.py manages Claude/low/read-only plus the dedicated reviewer
```

Per-run TOML file references alone did not fix transport. Verify readable spawn arguments, linked delivery, full packet reads, and actual model/effort/permissions. A hash/request alone is not input-application proof. Preserve failed/successful attempts, packets, changes, and original returns in the work record; see [Dispatch](../review/dispatch.md).

<a id="필요한-도구-사용법"></a>
## Tool usage

Use the installed CLI contracts at `${CODEX_HOME_DIR}/harness/README.md` and [review dispatch](../review/dispatch.md).

For Laya optional classification, submit one or two sentences after implementation direction is known. Read `treat_as` and callgraph risk:

| Classification/risk | Optional path |
|---|---|
| review/hard + MEDIUM | One optional code_reviewer; momus for a plan |
| review/hard + LOW/none | Main checks; optional review only with concrete need |
| ambiguous/unknown | Main checks; skip planning roles before repeated-failure cause reconsideration |
| clear + LOW/none | Main checks |

Connection failure, over 5 seconds, truncation, or empty input means unknown/ambiguous. This usage does not authorize server start/reset. Use the separately installed API-spec skill at `${CODEX_HOME_DIR}/skills/api-spec/SKILL.md` for format.

## Code graph queries

Use absolute `project_path`.

| Question | Query |
|---|---|
| Symbol | find_symbol |
| Direct callers/callees | callers / callees |
| A→B / screen→backend | path / screen_to_backend |
| Shared widget / existing-symbol impact | widget_usage / impact |

Resolve ambiguous names using returned `Class.member` or `path::name`. Supplement callbacks, Streams, Providers, and string RPCs with source search. TS caller counts are per calling function. At least 20 callers, 3 direct backend callers, or authentication patterns are HIGH signals; apply central duties rather than inferring approval.

On resume, connect source baseline, processes, unfinished work, next action, and original evidence to the existing message.
