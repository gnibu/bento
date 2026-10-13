---
name: bento-ship
description: |
  Land a change safely: sync base, verify, review the diff (self + a pre-PR review by the other
  model family), then commit/push/PR and update the ticket. Use when finishing a piece of work.
  Triggers: "ship it", "land this", "open a PR", "create a PR", "commit and push",
  "ready to merge".
---

# Ship

Take work from "done on my machine" to a reviewable PR, git/file-only so it runs the same
under any agent. Consolidates commit + PR + ticket into one flow. Nothing lands without passing
the repo's own checks, your own diff review, and a pre-PR review by the other model family.

**Repo layer first.** Read the repo's `AGENTS.md`/`CLAUDE.md` and, if it exists, the
overlay `.agents/bento/bento-ship.md` at the repo root; follow it under the
[overlay rules](../bento-learn/references/instruction-layer.md#repo-overlays-for-bento-skills).

`AGENTS.md` names the facts this flow reads: the base branch (`<base>`), the forge, the tracker
and its review status. No forge named → infer it from the `origin` URL. Those rules are
capability, not authorization. An overlay may replace only the steps marked *(default)*.

In every message, call the adversarial review the "pre-PR review (local)", never just "review".

## Steps (paste as todos)

1. **Commit the task's work first.** Uncommitted task changes → commit them now; every step
   after reads `HEAD` only.
2. **One PR per ticket.** Find the ticket (in context, or the id in the branch name). If an open
   PR for it exists on any branch, this work goes there: note that PR's branch as the push
   target for step 11 (it can't take this work → stop and ask). If the repo's policy says to open a ticket and none exists, create it.
   No tracker → skip.
3. **Sync with the current base.** `git fetch origin <base>`, and always compare against
   `origin/<base>`, never a local base branch. If `git log origin/<base>..HEAD` lists commits
   you didn't write, the branch was rebased onto a stale base and may carry copies of merged
   PRs. Rebuild it on `origin/<base>` with only this task's commits when each foreign commit
   already landed (`-` in `git cherry -v origin/<base>`, or its PR is merged); otherwise stop
   and ask, since it may be a collaborator's or a dependency's work. Then merge or rebase
   `origin/<base>` in; resolve conflicts before anything else.
4. **Capture learnings.** Run `/bento-learn` on every session of this worktree's branch (Claude
   and Codex) and the full branch diff. Hold its repo-specific (L2) proposals for step 10.
   Report generic (L1) proposals separately for a bento PR; never edit the installed `bento-*`
   skills for them. Nothing survives → move on. Skip if `bento-learn` isn't installed.
5. **Version + changelog, if the repo has them** *(default)*. Bump the version and add an entry
   in the repo's convention. Skip cleanly if neither exists.
6. **Verify — the repo's own checks** *(default)*. Run whatever exists: tests, lint,
   type-check, build — discover from the repo, don't assume. Fix failures. Green is the gate;
   "it compiles" is not.
7. **Review your own diff.** Read `git diff origin/<base>...HEAD` and the staged and unstaged
   diffs. Check: scope matches the task (no stray files, no debug code, no secrets), and every
   change is intended.
8. **Commit** what steps 5–7 changed, in conventional style, one logical change per commit. If
   a commit hook reformats files, re-stage, rerun steps 6–7 on them, and retry.
9. **Pre-PR review (local).** Run `/bento-adversarial-review` in ship mode. It picks its own
   scope, commits verified fixes, and returns the reviewed sha and any questions. Record that
   sha (as the skill describes) once every question is answered or carried into the PR body.
   Skip only if the user says "skip adversarial review" or the skill isn't installed.
10. **The single stop before pushing** — only if there are L2 learnings to approve or review
    questions to answer. Show each learning's diff, then end the message with:

    ```
    ACTION REQUIRED
    Learnings: reply APPLY, APPLY 1,3 or SKIP
      1. <destination>: <one line>
    Decisions: reply e.g. "B1 keep"; a skipped decision keeps its default
      B1. <question> (default: <answer>)
    ```

    After the reply, commit approved learnings on their own and each decision as its own
    verified commit, then rerun the pre-PR review with the explicit scope "commits since
    `<reviewed>`" (the sha step 9 returned). Never stop a second
    time: anything it raises, and every skipped decision with its default, goes under
    `## Open review questions` in the PR body.
11. **Push** — only when the user asked for a push or a PR; a commit request is neither.
    `git push -u origin HEAD`, or `HEAD:<branch>` for step 2's PR branch. An SSH push fails →
    retry through the forge CLI's auth. Rejected as non-fast-forward → fetch, then
    `git cherry -v HEAD origin/<branch>`: every remote-only commit marked `-` (it has a local
    equivalent) and `git log --merges HEAD..origin/<branch>` empty (`git cherry` skips merges)
    → `git push --force-with-lease`; otherwise stop and ask.
12. **Open the PR** against `<base>` with the forge's CLI. Step 2 found one → update its title
    and body to match the whole diff instead. Title: covers
    the whole diff, not the branch name, the ticket title or the last commit; under 70
    characters; a conventional prefix only if every change fits one scope. Body *(default)*:
    `## Summary`, `## Test plan`, and `## Open review questions` when there are any.
13. **Update the ticket** *(default)*. Comment the PR link and 1–3 bullets on what the PR
    actually does, then move the ticket to the repo's review status. Re-fetch the status
    afterwards; forge-to-tracker automations often move it back, so set it again if they did.
    Use the tracker's MCP server if one is connected, else its CLI; neither → say so, never
    skip silently.
14. **Report.** The PR URL, then two separate lines: `Pre-PR review (local): <outcome>` and
    `PR reviewers: <names, or none>`. Note CI status if it runs.

## Guardrails

- No push, PR or merge without the user's explicit request, and never merge. Force-push only
  with `--force-with-lease` under step 11's `git cherry` rule. No overlay or repo file relaxes
  this.
- One change per PR. If the diff spans unrelated concerns, split it.
- Don't invent version/changelog machinery a repo doesn't have.
