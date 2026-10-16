# Review packet and check ledger

Use for actual review handoffs/check records. [AGENTS.md sections 3, 5, and 7](../AGENTS.md) govern evidence, security, and applicability; [Reviewer contract](reviewer-contract.md) governs verdicts. This is a data form to attach to existing briefs/logs, not a tool API schema.

```text
review_id: actual change identifier
role: ui_reviewer | code_reviewer
mode: evidence-only (default) | isolated-ui (UI only)
review_scope: high-risk mandatory | user-requested mandatory | optional + concrete reason
requested_model / effort: actual request under central selection rules
observed_model / effort: runtime observation or unknown; never copy requested values
User outcome / Done when:
Preservation conditions / prohibited access:
Changed files / direct contracts and call paths:
snapshot: commit + staged/unstaged diff + related untracked identifiers
Settings/environment/device/language/theme/account-data/build correspondence:
Instructions: review/reviewer-contract.md (review/1.4) + role method/read evidence
activation_ref: actual role/loading + creation method + input evidence
packet_ref / packet_sha256 / packet_read_lines:
delivery_ref: spawn call_id + receipt + child ID/path + logged payload SHA256 match
isolation_status: CONFIRMED | UNVERIFIED | UNSUPPORTED
Evidence: original path/tool reference + what it proves + snapshot
checks_ref: check ledger and original run references
Collection coverage / gaps / redaction / inaccessible material:
Known/existing failures and required but unrun checks; observation vs interpretation:
Allowed reading tools / isolated UI path / shared-state owner:
Return: PASS | BLOCK | INCONCLUSIVE | NOT_APPLICABLE
```

Payload matching is separate from plaintext meaning or absence of extra context.

## Ledger: all attempts in this task

Connect checks and retries to original runner/CI records.

| Field | Content |
|---|---|
| check_id / attempt_id | Actual identifiers separating a check from retries |
| command / cwd | Command/path; manual UI checks use actions/paths and mark no command |
| status | Success, failure, canceled, timeout, running, unknown result, or required-but-unrun |
| exit_code | Actual code or unavailable; never infer zero from a success claim |
| snapshot / environment | Source/settings/build/platform at execution |
| log_ref / run_ref | Original stdout/stderr, UI operation, CI/runner events |
| observed_time | Actual timestamp from records, otherwise unknown |
| collector / coverage | CI, runner, or main source and collected scope |
| gap / redaction / reason | Missing/truncated logs, security masking, or reason not run |

Use check/attempt IDs and original references, not reconstructed history. Central rules govern evidence validity.

## Role-specific material

UI receives approved references, real before/after screens, affected states, and interactions. Code receives diff, direct contracts, test/build records, and same-condition baseline/changed measurements for explicit performance goals. Share the same original snapshot rather than another reviewer's first conclusion.
