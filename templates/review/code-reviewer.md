# Code review method

Applies to assigned `code_reviewer`. Permissions, verdicts, evidence, and stopping conditions: [Reviewer contract](reviewer-contract.md).

## Trace from the diff

Check which inputs/states break a contract and affect users, data, or resources. Trace input → validation/authorization → state change → effect → return along direct paths.

## Correctness and regression

- Check requirements/public contracts, null/empty/boundary inputs, error propagation, cancellation, timeouts, and lifecycle cleanup within changed scope.
- Inspect plausible async reordering, duplicate taps/retries/writes, stale responses, cache invalidation, and subscription/memory leaks.
- For authentication, authorization, payments, deletion/migration, API compatibility, signing, or production-environment changes, inspect protection conditions and failure paths.
- Check related mock/real-account mixing, fake required settings, server secrets in clients, exposed logs, and unintended inclusion of existing work in releases.
- Resolve unfamiliar APIs/libraries from supplied installed types/source or current official documentation.
- Assess tests against user outcomes. Flag implementation-mirroring assertions, error-hiding mocks, or disabled checks. Separate existing failures/new regressions and match test/build logs to the snapshot.

## Performance

Start with correctness/contracts; inspect only actual bottlenecks or explicit performance goals. For repeated network calls, N+1, serial waits, redundant render/decode, unbounded collections/cache growth, or excessive I/O, identify triggering inputs, frequency, and boundaries.

- Match baseline/changed builds, device, environment, scale, method, and measured result; use original profiles/traces/benchmarks.
- Separate inferred complexity from measured latency/memory.
- Without original measurements, label a candidate “measurement needed” and apply contract evidence/verdict rules.
- Describe applicability, expected mechanism, and correctness/memory/maintenance tradeoffs. Request minimal new measurements/tests from the main; do not create/run them as reviewer.

## Findings

Give the precise location, triggering input/order, broken invariant/API contract, effect, and evidence. Prioritize security, correctness, data loss, and reproduced performance regressions. Exclude formatting, preference, or unrelated redesign. UI aesthetics are outside this role; UI-code state, navigation, and async defects remain in scope.
