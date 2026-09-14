---
name: ship
description: |
  Land a change safely: sync base, verify, review the diff, then commit/push/PR. Use when
  finishing a piece of work. Triggers: "ship it", "land this", "open a PR", "create a PR",
  "commit and push", "ready to merge".
---

# Ship

Take work from "done on my machine" to a reviewable PR, git/file-only so it runs the same
under any agent. Consolidates commit + PR into one flow. Nothing lands without passing the
repo's own checks and your own diff review.

## Steps (paste as todos)

1. **Read the repo's conventions first.** Its `AGENTS.md`/`CLAUDE.md` states the policy this
   playbook must honor — base branch, commit style, PR rules, and any ticket/tracker workflow
   (create-a-ticket, move-status). Follow it; those rules are capability, not authorization.
2. **Sync the base branch.** Use the base the repo names (its default/integration branch — not
   `main` if the repo integrates elsewhere, e.g. `develop`). Fetch and merge/rebase it into
   your branch; resolve conflicts before anything else.
3. **Verify — the repo's own checks.** Run whatever exists: tests, lint, type-check, build
   (`just check`, `npm test`, `pytest`, etc. — discover from the repo, don't assume). Fix
   failures. Green is the gate; "it compiles" is not.
4. **Review your own diff.** Read `git diff <base>...HEAD` end to end. Check: scope matches
   the task (no stray files, no debug code, no secrets), and every change is intended.
5. **Version + changelog, if the repo has them.** Bump the version and add a changelog entry
   matching the repo's convention. Skip cleanly if neither exists.
6. **Commit** in conventional style, one logical change per commit. If a commit hook
   reformats files, re-stage and retry.
7. **Ticket, per the repo's policy** (step 1). If the repo says to open/track a ticket and one
   isn't already in context, create it and follow its status/branch rules. No tracker → skip.
8. **Push and open the PR** against the base branch, with a title/body derived from the actual
   diff (not the branch name). Create a PR only when the user asked — a commit is not a PR
   request. Use the repo's forge (`gh`, or another the repo names).
9. **Prove it.** Report the PR URL and that checks passed. If CI runs, note its status.

## Guardrails

- Pushing, merging, and opening PRs are irreversible/outward — do them only on explicit
  request, and never merge or force-push without being asked.
- One change per PR. If the diff spans unrelated concerns, split it.
- Don't invent version/changelog machinery a repo doesn't have.
