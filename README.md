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
  - `figure-it-out` — fallback for a task no playbook covers; frame it, then maybe capture it.
  - `authoring-a-playbook` — how to write a new bento playbook (gate, checklist, prove, eval).
  - `investigate` — evidence-first root-cause debugging; fix at the shared source.
  - `checkpoint` — capture in-progress state so work survives a reset or handoff.
  - `refactor` — change structure while holding behavior; pin first, prove equivalence.
  - `prototype` — throwaway spike to make a design decision cheaply; decide by observation.
  - `multi-phase-plan` — plan a large change as verifiable units before implementing.
  - `ship` — land a change: sync base, verify, review diff, commit/push/PR (git/file-only).
  - `qa` — exercise a change on its real surface (browser/CLI/API); report evidenced defects.
  - `spec` — turn vague intent into a precise, executable spec before building.
  - `cso` — security audit against common vuln classes; evidenced, confidence-calibrated.
  - `docs` — write/update docs to match current code; release notes.

## Install

**Claude-only (via marketplace):**

```bash
claude plugin marketplace add gnibu/bento
claude plugin install bento-core@bento     # + bento-forge@bento
/bento-setup                               # wires the always-on principles (one time)
```

Marketplace install gives you the **playbooks**; the always-on **principles** aren't a
plugin surface, so run `/bento-setup` (or `install.sh`) once to `@import` them into your
user `CLAUDE.md`.

**Cross-agent (Claude + Codex) in a repo:** vendor bento as a submodule so Codex can read
the files, then a directory-source marketplace for Claude + `AGENTS.md` pointers for Codex —
see `ARCHITECTURE.md` and `install/agents-md-snippet.md`.

Dev-load while iterating: `claude --plugin-dir plugins/bento-core`. See
`install/user-claude-md.md`.

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
