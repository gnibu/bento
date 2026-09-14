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

Two hooks run Reflect+Route headless and split the loop by what each hook can do —
**bank at Stop, surface at SessionStart** — so it needs no env var and behaves the
same on Claude and Codex:

- **Stop** reflects on the finished session and banks each candidate in a local ledger,
  silently. Always-on; it never opens a PR. Trivial sessions ("say hi") are skipped.
- **SessionStart** reads the ledger (no LLM) and, when a learning has recurred across
  enough independent sessions, injects a model-visible prompt to review the ripe learnings
  and open a PR. A single session can't tell a pattern from a one-off, so recurrence is the
  filter and **your yes to that prompt is the approval gate** that replaces the interactive
  apply. Fully hands-off? `BENTO_IMPROVE_AUTO_PR=1` lets the Stop worker open the PR itself.

This is implemented, not just described. The bundle lives beside this command:

```
scripts/session-stop.sh    Stop-hook entry: skip trivial, else spawn the worker (reflect + bank)
scripts/session-start.sh   SessionStart-hook entry: surface ripe learnings, model-visible (no LLM)
scripts/worker.sh          detached retrospective: digest → reflect → ledger; promote only if AUTO_PR
scripts/digest.sh          transcript → learnable signal, gated on friction
scripts/ledger.sh          local per-key recurrence ledger (keys|add|pending|ripe|show|promote|path)
scripts/secret-scan.sh     fail-closed credential filter on candidates before they are banked
prompts/reflect.md         read-only Reflect+Route prompt (this command's steps 1–2)
prompts/promote.md         write-enabled Propose prompt for ripe candidates (this command's step 3)
references/stop-hook.md    how to wire both hooks (personal, opt-in)
references/autorun.md      the full pipeline, gate, ledger, tunables, safety model
scripts/test-*.sh          self-checks: `bash scripts/test-parse.sh` etc.
```

Repo/host-neutral: base branch, tracker integration, and the repo-adoption marker are all
env-parameterized (`references/autorun.md` → Tunables). Nothing is hardcoded to a repo.
Preview what the ledger would file with `scripts/worker.sh --preview-issue`.
