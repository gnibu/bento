# bento improve

The learning engine. Turn what a session surfaced into durable improvements, each routed to
one home. Generalizes a session-learning router to two layers: **L1 (bento, generic)** and
**L2 (this repo, specific)**. This is *improve* — evolve what exists, diff and propose; for a
greenfield repo with no layer, see `bento-init`.

Resolve `<forge>` before running helpers: use `.bento/plugins/bento-forge` from the
consumer repo in Codex/vendored mode, or `${CLAUDE_PLUGIN_ROOT}` for an installed Claude
plugin. The shared instructions and scripts live in that same plugin directory.

## 1. Reflect

Scan the session for signal, citing the turn/command:

- **Friction** — anything slow, retried, or failed before it worked. Trace the *root cause*.
- **Operator corrections** — a redirect/reminder is a signal even with no error: something you
  should have done or offered yourself. Fix the missing behavior, not the one instance.
- **Surfaced bugs** — code that misbehaved (silent failures, wrong checks, missing guards).
- **Reusable gotchas** — a command, env quirk, or non-obvious pattern the next agent trips on.
- **Repeatable workflows** — a multi-step procedure that will recur.

**Reuse gate (hard filter):** keep a candidate only if you can name a concrete recurring
trigger. Default to dropping. Surfacing nothing is a valid outcome — don't manufacture
learnings. Ignore anything already documented (grep first).

## 2. Route — one destination per learning

Pick the cheapest correct home. Price the sink first (see `.bento/conventions/instruction-layer.md`).

**By kind:**
- Code bug / wrong logic → fix the **source** + a test. The fix is the learning.
- Cross-role procedure → **existing docs** + a task-triggered link from the instruction file.
- Agent orchestration / tool choice / review behavior → a **skill** (amend the owner; create
  one only if none fits — see `authoring-a-playbook`).
- Code-scoped gotcha / command / env quirk → the **nearest `AGENTS.md`** to that code.
- Human-facing architecture / decision → **docs** (or an ADR).
- One-off → **drop it.**

**By layer:**
- Generic (helps any repo, any agent) → **L1: bento** — a principle, convention, or playbook.
- Repo-specific → **L2: this repo's** instruction layer.

Never bank a team-useful learning in **private memory** — it's per-operator and reaches no
one else. Private memory is the last resort, only for genuinely personal, cross-project
preferences.

## 3. Propose, then apply

- Show the concrete diff per learning, grouped by destination, **before** touching anything.
- Apply on explicit go-ahead. Leave commits/PRs to the user (or to `ship`, when it called you).
- **Preserve generated-file ownership.** If `.bento-state/baseline.json` lists the
  destination, build a proposal from its last-generated text plus this learning,
  then run `python3 "<forge>/scripts/l2-state.py" --repo . merge <proposal.json>`
  to preview; append `--apply` only after approval. `<forge>` is the plugin root resolved
  above. The helper merges current / baseline / proposed and advances the baseline only
  on success. Show the **merged diff**, not just the proposal.
  Never edit a managed file directly or replace its baseline with hand-edited text.
  A conflict writes nothing: revise the proposal for review or leave it unapplied.
  No baseline, or an unlisted destination → ordinary targeted diff-and-propose;
  never invent a baseline for existing L2. See
  `<forge>/references/bento-init.md` for the proposal format and recovery rules.
- **For a skill/playbook edit, prove it:** baseline `claude plugin eval` → apply the edit →
  re-run → keep only on a real lift beyond noise (`--runs 3+`), else revert. Log kept/reverted
  (this is `hillclimb` applied to the instruction layer itself).
  Revert the corresponding baseline change too if a managed-file edit is rejected.

## When to run

No hook runs this — it is a deliberate step, run two ways:

- **At PR time** — the `ship` playbook calls it before final verification and diff review.
  Reflect on this session **and** the full branch diff (committed and uncommitted), so
  learnings from earlier sessions that shaped it are covered too. Apply approved L2 edits in
  the consumer repo; `ship` verifies and reviews them with the full change, then commits them
  separately in that PR.
  Report L1 proposals for a separate bento PR. Do not edit the consumer's `.bento` submodule,
  installed plugin copy, or submodule pin for an L1 learning. Nothing survives the reuse gate
  → say so in one line and let `ship` continue.
- **Manually** — `/bento-improve` (Claude) or `$bento-forge:bento-improve` (Codex), for
  sessions that end without a PR (debugging, investigation). Same steps; committing the
  result is the user's call.
