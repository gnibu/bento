---
name: bento-ship
description: |
  Land a change safely: sync base, verify, review the diff (self + adversarial), then
  commit/push/PR. Use when finishing a piece of work. Triggers: "ship it", "land this", "open a PR", "create a PR",
  "commit and push", "ready to merge".
---

# Ship

Take work from "done on my machine" to a reviewable PR, git/file-only so it runs the same
under any agent. Consolidates commit + PR into one flow. Nothing lands without passing the
repo's own checks, your own diff review, and an adversarial review by the other model family.

## Steps (paste as todos)

1. **Read the repo's conventions first.** Its `AGENTS.md`/`CLAUDE.md` states the policy this
   playbook must honor — base branch, commit style, PR rules, and any ticket/tracker workflow
   (create-a-ticket, move-status). Follow it; those rules are capability, not authorization.
2. **Sync the base branch.** Use the base the repo names (its default/integration branch — not
   `main` if the repo integrates elsewhere, e.g. `develop`). Fetch and merge/rebase it into
   your branch; resolve conflicts before anything else.
3. **Capture learnings.** Run `/bento-learn` on every session of this
   worktree's branch (Claude and Codex) and the full branch diff, including uncommitted changes.
   Apply approved repo-specific (L2) learnings to this branch; commit them separately from
   the task change. Report generic (L1) proposals separately for a bento PR. Do not edit
   the installed `bento-*` skills for an L1 learning.
   Nothing survives → move on. Skip if `bento-learn` isn't installed.
4. **Version + changelog, if the repo has them.** Bump the version and add a changelog entry
   matching the repo's convention. Skip cleanly if neither exists.
5. **Verify — the repo's own checks.** Run whatever exists: tests, lint, type-check, build
   (`just check`, `npm test`, `pytest`, etc. — discover from the repo, don't assume). Fix
   failures. Green is the gate; "it compiles" is not.
6. **Review your own diff.** Read `git diff <base>...HEAD` and the staged and unstaged diffs,
   including changes from steps 3–4. Check: scope matches the task (no stray files, no debug
   code, no secrets), and every change is intended.
7. **Commit** in conventional style, one logical change per commit. Keep approved L2 learning
   edits in their own commit in this PR. If a commit hook reformats files, re-stage, rerun
   steps 5–6 on the changed files, and retry.
8. **Adversarial review, unless already done.** Read the reviewed sha from
   `"$(git rev-parse --git-path adversarial-review.head)"`:
   - it equals `HEAD` → already reviewed, skip;
   - it is an ancestor of `HEAD` and `git rev-list --merges <sha>..HEAD` is empty → review only
     the commits since `<sha>`;
   - otherwise (missing, rebased away, base merged in) → review the whole branch.

   Run `/bento-adversarial-review` in **ship mode** on that scope. It commits verified fixes
   and returns questions for findings that need a human. If there are any, stop once before
   pushing and ask them; implement each answer as its own verified commit, then re-run the
   review on the commits since the reviewed sha without stopping again. Unanswered questions
   go under `## Open review questions` in the PR body. Record the reviewed sha (per the
   skill) only once every question is answered or in the PR body. Skip only if the user says
   "skip adversarial review" or the skill isn't installed.
9. **Ticket, per the repo's policy** (step 1). If the repo says to open/track a ticket and one
   isn't already in context, create it and follow its status/branch rules. No tracker → skip.
10. **Push and open the PR** against the base branch, with a title/body derived from the
    actual diff (not the branch name). Create a PR only when the user asked — a commit is not
    a PR request. Use the repo's forge (`gh`, or another the repo names).
11. **Prove it.** Report the PR URL and that checks passed. If CI runs, note its status.

## Guardrails

- Pushing, merging, and opening PRs are irreversible/outward — do them only on explicit
  request, and never merge or force-push without being asked.
- One change per PR. If the diff spans unrelated concerns, split it.
- Don't invent version/changelog machinery a repo doesn't have.
