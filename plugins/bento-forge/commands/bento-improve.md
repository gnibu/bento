---
description: Reflect on a session and route each reusable learning to its cheapest correct home (L1 bento or L2 repo). Evolve an existing instruction layer — diff and propose, never regenerate. Idempotent; prove skill edits with the eval harness.
---

# bento improve

The learning engine. Turn what a session surfaced into durable improvements, each routed to
one home. Generalizes a session-learning router to two layers: **L1 (bento, generic)** and
**L2 (this repo, specific)**. This is *improve* — evolve what exists, diff and propose; for a
greenfield repo with no layer, see `bento-init`.

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
- Apply on explicit go-ahead. Leave commits/PRs to the user.
- **For a skill/playbook edit, prove it:** baseline `claude plugin eval` → apply the edit →
  re-run → keep only on a real lift beyond noise (`--runs 3+`), else revert. Log kept/reverted
  (this is `hillclimb` applied to the instruction layer itself).

## Autorun (optional, recurrence-gated)

A guarded Stop hook can run Reflect+Route headless, bank each candidate in a local ledger,
and open a PR only once the same learning has recurred across several independent sessions —
a single session can't tell a pattern from a one-off, so recurrence is the filter and the PR
is the approval gate that replaces the interactive apply.

This is implemented, not just described. The bundle lives beside this command:

```
scripts/stop-nudge.sh      Stop-hook entry: nudge, or (BENTO_IMPROVE_AUTORUN=1) spawn the worker
scripts/worker.sh          detached retrospective: digest → reflect → ledger → promote (branch + PR)
scripts/digest.sh          transcript → learnable signal, gated on friction
scripts/ledger.sh          local per-key recurrence ledger (keys|add|pending|ripe|show|promote|path)
scripts/secret-scan.sh     fail-closed credential filter on candidates before they are banked
prompts/reflect.md         read-only Reflect+Route prompt (this command's steps 1–2)
prompts/promote.md         write-enabled Propose prompt for ripe candidates (this command's step 3)
references/stop-hook.md    how to wire the hook (personal, opt-in)
references/autorun.md      the full pipeline, gate, ledger, tunables, safety model
scripts/test-*.sh          self-checks: `bash scripts/test-parse.sh` etc.
```

Repo/host-neutral: base branch, tracker integration, and the repo-adoption marker are all
env-parameterized (`references/autorun.md` → Tunables). Nothing is hardcoded to a repo.
Preview what the ledger would file with `scripts/worker.sh --preview-issue`.
