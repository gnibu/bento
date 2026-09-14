# bento

Ben's personal agent kit — how I work, packed into portable compartments that follow me
into every project. One marketplace, layered:

```
L0  Claude Code + Anthropic skills     (given)
L1  bento-core → how I work            (this repo; principles + playbooks)
L2  project layer → how THIS repo works (generated/improved into each repo, later)
```

Precedence: **L2 > L1.** A project's own rules win; bento fills the gaps.

## What's here (phase 1)

- `principles/PRINCIPLES.md` — always-on standing rules (autonomy, prove-on-artifact,
  subtract-before-add). Delivered via the user `CLAUDE.md` import.
- `conventions/instruction-layer.md` — how to author a repo's L2: instruction-file pricing,
  pointer form, where each fact goes, task-triggered links, "no match → design one".
- `plugins/bento-core/skills/` — triggered playbooks:
  - `eval-blind` — compare models/prompts without bias leaking into the verdict.
  - `hillclimb` — tune a metric one variable at a time, keep-or-revert, logged.

Install + dev-load: see `install/user-claude-md.md`.

## Not built yet (deliberately)

- More playbooks (bug-fix, ship, refactor…) — add when a real recurring task needs one,
  not speculatively.
- `bento-forge` — `generate` (bootstrap a fresh repo's L2) and `improve` (evolve an
  existing L2). `improve` will be the `rose-session-learn` routing engine generalized to
  L1/L2 sinks, not a rebuild. `generate` can use potion off-the-shelf until it's outgrown.
- Per-skill `claude plugin eval` cases (with/without ablation) to prove each skill moves
  behavior.

## Credits

Inspired by, not copied from: **poteto** (Cursor) and **potion** (A. Sibiril). See the
IX-4908 plan in Rose (`docs/plans/ix4908-poteto-mode-patterns.md`) for the reasoning and
the inspiration-not-copy rule.
