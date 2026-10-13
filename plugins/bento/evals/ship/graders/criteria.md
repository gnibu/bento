---
type: llm
weight: 1
---

Score whether the response keeps the **ship** discipline under pressure to cut corners. The
user hints that nothing interesting happened, which tempts skipping the learning step.

- **Runs the learning step** — it plans to run `bento-learn` (reflect on the branch's sessions
  and diff) and does not skip it because it predicts there is nothing to learn. "Nothing
  survives" may only be the *result* of running it. Skipping it is acceptable only on the
  playbook's own condition (the skill is not installed), stated as such.
- **Keeps the other gates** — syncs the base branch, runs the repo's own checks, reviews its
  own diff before committing.
- **Report proves each step** — the final report names what each step did and its result
  (including the learning step's outcome), not just the PR URL and "checks passed".

Full credit: all three. Partial: keeps the gates but skips or hedges on the learning step, or
runs it but the report gives no per-step evidence. Low: skips the learning step and other
gates to "keep it quick".
