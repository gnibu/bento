# Path A — fallback: your own sub-agents

Gather the diff (the scope command) and the full text of every file it touches. A diff alone
hides the callers and the invariants; most false findings come from reviewing hunks in
isolation.

Fan out one sub-agent per dimension, concurrently (one pass yourself for the quick tier, or if
your host has no sub-agents). Drop a dimension the diff clearly doesn't touch; add one the user asked for:

- **correctness** — logic errors, off-by-one, wrong branch, error paths, null/undefined,
  async mistakes, transaction and ordering bugs.
- **contracts & callers** — every caller of every changed signature; migrations vs. readers;
  config keys vs. their allow-lists; API/response shape changes.
- **concurrency & state** — races, shared mutable state, idempotency, retries, tenant leakage.
- **reuse & simplicity** — code that duplicates an existing helper, or could be simpler.
- **security & data** — authz gaps, tenant isolation, injection, secrets in logs or args.

Give each the stance explicitly: *assume this diff is broken and find where; a finding you
cannot point at a specific line for is not a finding.* Require the CLI output shape —
`- [P1] Title — path/file.ts:12-15` plus a paragraph of rationale — so phase 2 is identical.

