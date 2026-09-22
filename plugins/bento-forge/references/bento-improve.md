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
- Apply on explicit go-ahead. Leave commits/PRs to the user.
- **Preserve generated-file ownership.** If `.bento-state/baseline.json` lists the
  destination, build a proposal from its last-generated text plus this learning,
  then run `python3 "<forge>/scripts/l2-state.py" --repo . merge <proposal.json>`
  to preview; append `--apply` only after approval. `<forge>` is the plugin root resolved
  above. The helper merges current / baseline / proposed and advances the baseline only
  on success. Show the **merged diff**, not just the proposal.
  Never edit a managed file directly or replace its baseline with hand-edited text.
  A conflict writes nothing: revise the proposal for review or leave it unapplied.
  Unattended promotion skips conflicting learnings and records why in its PR body.
  No baseline, or an unlisted destination → ordinary targeted diff-and-propose;
  never invent a baseline for existing L2. See
  `<forge>/references/bento-init.md` for the proposal format and recovery rules.
- **For a skill/playbook edit, prove it:** baseline `claude plugin eval` → apply the edit →
  re-run → keep only on a real lift beyond noise (`--runs 3+`), else revert. Log kept/reverted
  (this is `hillclimb` applied to the instruction layer itself).
  Revert the corresponding baseline change too if a managed-file edit is rejected.

### Reviewing candidates surfaced by SessionStart

When SessionStart names banked candidate keys, do not merely repeat the notification or
wait for recurrence:

1. Resolve `<forge>`, then read each record with
   `"<forge>/scripts/ledger.sh" show <key>`. The default human-review threshold is one;
   `BENTO_IMPROVE_THRESHOLD` applies only to unattended auto-promotion.
2. Re-verify the evidence and proposed sink against the current repo. For candidates that
   are one-offs, already handled, or routed incorrectly, run
   `"<forge>/scripts/ledger.sh" dismiss <key>` so they do not return next session.
3. Show the concrete diff for every surviving candidate. Do not edit yet.
4. Apply and verify only after explicit approval. Committing, pushing, and opening a PR
   remain separate user actions unless they were explicitly requested.

Keep an accepted candidate pending until its durable change exists. The ledger is the retry
mechanism; a notification is not proof that the learning was applied.

## Autorun (human-reviewed by default, recurrence-gated when unattended)

Two hooks run Reflect+Route headless and split the loop by what each hook can do —
**bank at Stop, surface at SessionStart** — so it needs no env var and behaves the
same on Claude and Codex:

- **Stop** persistently queues the finished session, reflects after quiescence, and banks
  each candidate in a local ledger, silently. If the detached process is lost, a later
  SessionStart re-arms the pending analysis. Trivial sessions ("say hi") are skipped.
- **SessionStart** reads the ledger (no LLM) and injects a model-visible prompt for every
  valid candidate by default, including the keys needed for the review flow above. **Your
  yes to the proposed diff is the approval gate** that replaces interactive apply.
  Recurrence is a separate safeguard for fully unattended changes:
  `BENTO_IMPROVE_AUTO_PR=1` lets the Stop worker open a PR only after the auto-promotion
  threshold is met.
- **Update checks** are also requested at SessionStart, at most every 30 days. The agent
  checks upstream first and offers a manual update only if a newer version is confirmed.
  Worker children have these checks disabled so they preserve the user's reminder window.
  See `references/autorun.md` → Tunables for the interval and timestamp path.

This is implemented, not just described. The bundle lives beside this command:

```
scripts/session-stop.sh    Stop-hook entry: skip trivial, else durably enqueue reflection
scripts/session-start.sh   recover pending jobs + surface candidates + update-check instructions
scripts/pending-session.sh persistent debounce/recovery handoff to the worker
scripts/worker.sh          detached retrospective: digest → reflect → ledger; promote only if AUTO_PR
scripts/digest.sh          transcript → learnable signal, gated on friction
scripts/ledger.sh          local ledger (keys|add|pending|ripe|show|promote|dismiss|path)
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
