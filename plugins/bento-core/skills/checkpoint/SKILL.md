---
name: checkpoint
description: |
  Capture in-progress state so work survives a context reset or handoff. Use when pausing,
  saving progress, or before a long/risky step. Triggers: "save progress", "checkpoint",
  "pause here", "resume later", "hand this off".
---

# Checkpoint

Write down enough that a fresh session (you or someone else) can resume without re-deriving
what you already know. State lives in the repo, not in your head.

## Steps (paste as todos)

1. **State the goal** and the done-condition in one line.
2. **Record what's done** — the decisions made and why, with pointers (files, commits,
   PRs), not prose recaps.
3. **Record what's next** — the immediate next action, concretely enough to run. Include the
   command or the file:line to start from.
4. **Flag blockers and open questions** — anything waiting on a decision, a dependency, or
   an irreversible step you deliberately paused before.
5. **Leave no landmine.** Note any half-applied change, dirty state, or running process the
   next session must know about.
6. **Write it where it's found** — a task file, a PR/issue comment, or the repo's checkpoint
   location; not private memory. Keep run-specific detail out of reusable docs.

## Guardrails

- A checkpoint is for *resuming*, not a diary. Cut anything that doesn't change the next
  action or a decision.
- Don't checkpoint secrets or production data — pointers, not payloads.
