# Reviewer activation evidence

Use for needed first-role, runtime/permission-change, or actual-assignment evidence. This document does not trigger calls: apply [section 7](../AGENTS.md#7-review-triggers-and-holds) and [model opt-in](../AGENTS.md#models-and-delegation) first. Independence, permissions, and verdicts: [review/1.4](reviewer-contract.md).

## Collection

Use [read-only dispatch](dispatch.md#read-only-dispatch). `run_readonly_review.py` links original paths/line numbers. Check both `sandbox_policy` and `permission_profile.file_system`.

Connect observations: files → recognized loader → role call → contract/method reads → input/context correspondence → result.

| Ground | Actual evidence |
|---|---|
| Role | Runtime/version, role TOML, loading/selection, run ID, actual contract/method reading or delivery |
| Context | Installed schema's creation method, actual call/session records, parent conversation/peer-verdict copying |
| Input | Actual packet or safely observed input matched to requirements/snapshot/originals |
| Model/permissions | Request versus observed model, effort, sandbox, and tool restrictions |
| Check coverage | Original runner/CI records versus packet ledger; gaps/truncation/redaction |

## Local Codex records

Read only needed fields in this run's parent/child JSONL under `~/.codex/sessions/<year>/<month>/<day>/`.

- `session_meta.agent_role`: assigned role.
- Child developer input: actual contract/method loader and version marker.
- Child tools/input: full `review/reviewer-contract.md` and role-method reading or safe direct-delivery proof; a reference alone is insufficient.
- `turn_context.model`, `effort`, `sandbox_policy.type`: actual selections.
- Parent `spawn_agent` with `fork_turns: "none"` plus child input: creation/delivery evidence.
- For opaque input, compare parent sent bytes and child `encrypted_content` SHA256; link the same call's receipt, role/parent IDs, and recipient path. Never decrypt input or put raw opaque content/keys in reports.

If these fields are unavailable, record the available observation method; apply contract interpretation/resume rules.

## Delivery without decryption

Collect two independent evidence links:

1. **Transport:** spawn call ID → same-call task-path receipt → actual child parent/role/path → NEW_TASK sender/recipient and matching logged-payload SHA256. Missing values, wrong recipient, multiple initial deliveries, or differing hashes are unverified.
2. **Packet reading:** fixed approved path/SHA256 → child's actual read call ID/full output → unchanged file after execution. Quotes, self-reports, and truncated reads do not count.

These prove matching logged delivery and a full read of the named file, not opaque plaintext meaning, absence of extra context, or statistical independence. The `encrypted_content` field may carry readable routed content; its name alone does not prove encryption. `delivery_evidence` is not automatic full-independence or mandatory-review clearance.

## Minimal record

```text
runtime: product/version/execution mode
role: ui_reviewer | code_reviewer
contract_ref: review/reviewer-contract.md (review/1.4) + actual read/delivery
role_ref: method path/hash + actual read/delivery
harness: review/1.4
run_id / spawn_record:
context_evidence:
packet_ref / packet_sha256 / full-read output lines / snapshot:
delivery_ref: spawn call_id / receipt line / child_id-path / recipient line / opaque_payload_sha256
isolation_status: CONFIRMED | UNVERIFIED | UNSUPPORTED
technical_write_block: VERIFIED | UNVERIFIED + observed scope
limitations / next_action:
```

Collect changed-runtime/settings/permissions/packet/snapshot evidence only when central conditions require revalidation.
