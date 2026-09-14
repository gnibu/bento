---
description: Generate this repo's project layer (L2) from its code, docs, and PR-review history. Greenfield only.
---

# bento init (stub — phase 2)

Bootstrap an L2 (`.claude/` skills + `AGENTS.md`) for a repo that has none, grounded in the
codebase's real conventions, with a human checkpoint per phase.

**Not built yet.** Until it is, use **potion** off-the-shelf for the generate job
(<https://github.com/aureliensibiril/potion>) — inspiration, not copied.

Guardrails when this is implemented:

- Greenfield only. If an L2 already exists, refuse and point to `/bento-improve` — never
  regenerate over hand edits.
- Human checkpoint per phase; commit the result into *that* repo (it's team L2, not bento).
- Record a "last generated" baseline so `improve` can do a 3-way merge later.
