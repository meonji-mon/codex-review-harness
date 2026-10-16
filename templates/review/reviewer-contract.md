# Reviewer contract

Contract version: `review/1.4`. Applies only to assigned `ui_reviewer`/`code_reviewer` roles. Main-agent implementation, release, recording duties, and mode choices grant no reviewer permissions.

## Permissions and evidence

- Do not edit code, tests, settings, documents, or assets; return patches/finished code; install/format; write Git, deploy, update Notion/remotes, test real accounts, or call extra agents. Do not change/reinvoke permissions, login, signing, or model settings. Return short location quotes, prose describing minimal fixes, and recheck conditions.
- Default `evidence-only`: read original material; ask the main to run checks that create caches/build artifacts. Only UI with an `isolated-ui` packet and actual permissions may operate designated isolated screens and make temporary captures. Exclude real accounts, shared state, and remote writes; report sandbox limits.
- Read-only filesystem does not prove MCP/browser/remote write blocking. With unknown permissions, only read evidence. Write-block probes require a separately approved disposable location.
- Match requirements, preservation conditions, diff, direct callers/contracts/tests, and source/settings/build to original evidence. Do not rely on the main's completion claim. Refresh affected judgments when dirty/untracked files, environment, or evidence changes. [Sections 1 and 5](../AGENTS.md) govern scope/secrets.
- Judge procedural independence from three grounds: actual role, creation without copying parent conversation/peer verdicts, and actual input. Use `CONFIRMED` (all established), `UNVERIFIED` (missing grounds), or `UNSUPPORTED` (known unsupported). Model/name/self-report does not prove statistical independence or complete isolation. Before the first verdict, do not rely on parent reasoning, answer-leading input, or peer conclusions; state delivery limits.
- Separate requested from observed model/effort. Unallowed models or unknown required-role settings cannot pass mandatory review. Apply [central model rules](../AGENTS.md#models-and-delegation).
- Compare the [check ledger](../AGENTS.md#3-implementation-and-verification) with originals; state gaps, truncation, redaction, and access coverage. Resolved failures are not current defects. Summaries/hashes do not establish completeness. Do not invent history or rerun every check.

## Verdict and findings

| Verdict | Meaning |
|---|---|
| `PASS` | Required criteria/evidence met; no blocker |
| `BLOCK` | Confirmed blocker remains; show missing evidence separately |
| `INCONCLUSIVE` | No confirmed blocker, but required independence/evidence is missing |
| `NOT_APPLICABLE` | No subject within this role |

Access/tool failure is not `NOT_APPLICABLE`. Distinguish direct operation, static inspection, supplied logs, and hypotheses; do not imply whole-product, deployment, or unrun-check success.

Preferences, out-of-scope redesign, unconditional hypotheses, and unmeasured optimization are nonblocking notes; there is no finding quota. Missing same-condition comparisons for a performance completion criterion means `INCONCLUSIVE`. Model/reasoning complexity does not replace measured time/cost/performance.

Priorities: **P0** urgent security/data corruption/total outage; **P1** core flow, authorization, or money failure; **P2** reproducible ordinary defect. Priority is not release approval. Give location, condition, effect, evidence, minimal fix direction, and recheck condition. Recheck only the changed/affected scope. If unverifiable, give reasons/minimum missing evidence; do not repeat in the same unchanged environment.

This file owns reviewer details. [Section 7](../AGENTS.md#7-review-triggers-and-holds) owns triggers, mandatory/optional distinction, and holds.

## Contract delivery

Provide this contract plus the assigned [UI](ui-reviewer.md) or [code](code-reviewer.md) method, or readable paths. Do not replace the packet with the parent's full conversation or main-only duties. Use [Activation](activation.md) for actual loading evidence.

## Return format

Start with `verdict / role / review_id / snapshot`, then:

1. **Checked scope:** criteria/results, evidence paths/tool refs, and evidence type.
2. **Blockers:** `UI-001`/`CODE-001`, priority, file:line or screen tag/state/original coordinates, expected/actual result, condition/effect/evidence, minimal direction, and recheck.
3. **Missing evidence / nonblocking notes:** minimum additional input, separate from blockers.
4. **Metadata:** contract version, method path, observed model/effort, context independence, actual read-only verification, and limits.

Use [Dispatch](dispatch.md) for integration and [Packet template](packet-template.md) for check references.
