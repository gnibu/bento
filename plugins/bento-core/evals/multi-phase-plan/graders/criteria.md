---
type: llm
weight: 1
---

Score how well the response applies **multi-phase planning** discipline. A strong answer
covers most of:

- **Plan is the deliverable** — produce the plan/checklist first, don't start implementing.
- **One PR = one verifiable unit** — split into sections ordered by dependency, each PR a
  single change with its own evidence.
- **Every box names its evidence** — a file, log line, screenshot, test, or SHA checks each
  box; state a per-PR verification rule (tests alone insufficient: unit + live + regression).
- **Settle unknowns by prototype first**, not by guessing in the plan.

Full credit: plan-as-deliverable + one-PR-per-unit + evidence-per-box all present. Partial: a
vague "break it into steps" without verifiable units or evidence. Low: jumps to implementing.
