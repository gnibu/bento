# bento

A shared agent operating framework — a reusable "way of working" a project adopts as its
baseline, with the project's own specifics layered on top. Works across agents (Claude Code
and Codex). Layered:

```
L0  Claude Code + Anthropic skills        (given)
L1  bento  → shared way of working         (a pinned dependency each repo installs)
L2  project layer → how THIS repo works    (the repo's own skills + instructions, on top)
```

Precedence: **L2 > L1.** The project's own rules win; bento fills the gaps. See
`ARCHITECTURE.md` for the full design.

## Four pillars

- **`principles/PRINCIPLES.md`** — always-on standing rules (autonomy, prove-on-artifact,
  subtract-before-add). Delivered via a `CLAUDE.md` `@import`.
- **`conventions/instruction-layer.md`** — how to author a repo's L2: instruction-file
  pricing, pointer form, where each fact goes, task-triggered links, "no match → design one".
- **`plugins/bento-core/`** — triggered playbooks (skills), each a pasteable checklist that
  proves its work on a real artifact:
  - `eval-blind` — compare models/prompts without bias leaking into the verdict.
  - `hillclimb` — tune a metric one variable at a time, keep-or-revert, logged.
  - `figure-it-out` — fallback for a task no playbook covers; frame it, then maybe capture it.
  - `authoring-a-playbook` — how to write a new bento playbook (gate, checklist, prove, eval).
  - `investigate` — evidence-first root-cause debugging; fix at the shared source.
  - `checkpoint` — capture in-progress state so work survives a reset or handoff.
  - `refactor` — change structure while holding behavior; pin first, prove equivalence.
  - `prototype` — throwaway spike to make a design decision cheaply; decide by observation.
  - `multi-phase-plan` — plan a large change as verifiable units before implementing.
  - `ship` — land a change: sync base, verify, review diff, commit/push/PR (defers to the
    repo's AGENTS.md for base branch, PR, and ticket policy).
  - `qa` — exercise a change on its real surface (browser/CLI/API); report evidenced defects.
  - `spec` — turn vague intent into a precise, executable spec before building.
  - `cso` — security audit against common vuln classes; evidenced, confidence-calibrated.
  - `docs` — write/update docs to match current code; release notes.
  - `bento-setup` — wire bento into the environment (principles, Codex block, hooks).
- **`plugins/bento-forge/`** — the learning engine and generator:
  - `bento-improve` — Reflect → Route → Propose: route each session's learnings to their
    cheapest correct home (L1 bento / L2 repo), with an eval-gated keep-or-revert. Ships the
    **autorun** subsystem (bank at `Stop`, surface ripened at `SessionStart`, PR on your yes).
  - `bento-init` — *(stub)* bootstrap a fresh repo's L2; use potion off-the-shelf until built.

Quality is built in: an **eval harness** (`claude plugin eval` with with/without ablation +
a `tool_used` firing indicator) proves whether a skill actually changes behavior — see
`plugins/bento-core/evals/`.

## Install

**Claude-only (via marketplace):**

```bash
claude plugin marketplace add gnibu/bento
claude plugin install bento-core@bento     # + bento-forge@bento
/bento-setup                               # wire principles + hooks (interactive; --yes for defaults)
```

Marketplace install gives Claude the **playbooks**; `/bento-setup` wires what a plugin can't:
the always-on **principles** (`@import` into your user `CLAUDE.md`), the **Codex pointer
block** (`AGENTS.md`), and the **learn hooks** (Stop + SessionStart). It asks scope
(personal/committed) and auto-PR (off/on); `--yes` takes defaults, `--purge` unwires.

**Cross-agent (Claude + Codex) in a repo:** vendor bento as a submodule so Codex can read the
files, then a directory-source marketplace for Claude + `AGENTS.md` pointers for Codex — see
`ARCHITECTURE.md` and `install/agents-md-snippet.md`.

Dev-load while iterating: `claude --plugin-dir plugins/bento-core`. See
`install/user-claude-md.md`.

## Update (self-update)

bento is versioned; pull the latest and reconcile the wiring. Same repo, two install modes:

- **Marketplace install (Claude-only):**
  ```bash
  claude plugin update bento-core@bento     # + bento-forge@bento; restart to apply
  ```
- **Vendored (`.bento` submodule, cross-agent):**
  ```bash
  git submodule update --remote .bento      # pull latest bento
  git add .bento && git commit -m "chore: bump .bento"
  ```
- **After either, re-run `/bento-setup`** — idempotent; reconciles the principles import, the
  `AGENTS.md` block, and the hooks with the new version (e.g. picks up a renamed script).

Pin/roll back by checking the submodule out at a specific bento SHA (or a `plugin@version`).

**Content self-update:** bento also improves *itself* — `bento-improve` routes generic
learnings back into bento (L1) as PRs. That's the framework evolving from real use, not just
version bumps.

## Not built yet (deliberately)

- **`bento-init`** (greenfield L2 generation) — use potion off-the-shelf until it's outgrown.
- More playbooks — add only when a real recurring task needs one, never speculatively.
- Eval cases for the ported playbooks (ship/qa/spec/cso/docs) — the harness exists; cases for
  eval-blind and hillclimb are in place, the rest are follow-ups.

## Credits

Inspired by, not copied from: **poteto** (Cursor) and **potion** (A. Sibiril). See
`CREDITS.md`.
