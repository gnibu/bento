---
description: Improve an existing project layer (L2) — mine signal, propose a patch, prove keep-or-revert. Never regenerate.
---

# bento improve (stub — phase 2/3)

Evolve an existing L2 instead of regenerating it. The engine already exists: this is
Rose's `rose-session-learn` (Reflect → Route → Propose, with its pricing model and
recurrence-gated autorun) **generalized** — widen its Route table's sinks from Rose-only
(`AGENTS.md`/docs/skills) to **L1 principles vs L2 project layer**, respecting L2 > L1.

**Not built yet.** Reuse `rose-session-learn` as the reference implementation; do not
rebuild the router. The routing + pricing rules it applies live in
`conventions/instruction-layer.md` — the single source for "which sink, how terse".

When implemented:

1. Widen the sink table to L1 vs L2; propose a patch, never regenerate over hand edits
   (needs the "last generated" baseline from `/bento-init` for a 3-way merge).
2. Start from a quality signal: never-invoked / high-cost-low-use skills, and
   `claude plugin eval` with/without (which skills actually move outcomes).
3. Mine only PR reviews since the last run (incremental tribal knowledge).
4. Require the eval arm to prove keep-or-revert — hillclimb applied to the skills themselves.
5. In a team repo, the proposed L2 patch still lands via normal PR review.
