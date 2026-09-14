---
name: multi-phase-plan
description: |
  Plan a large change as a checklist of verifiable units before implementing. Use when work
  spans many files or several PRs and the approach isn't a one-shot. Triggers: "plan this",
  "break into phases", "multi-PR", "large change", "roadmap", "how should we sequence".
---

# Multi-phase plan

You own the plan, not the code. **The plan is the deliverable — do not implement here.** It's
a checklist an owner runs box by box and an auditor can check from the evidence.

## Steps (paste as todos)

1. **Skip if small.** One or two files with an obvious approach → say so and just do it. No
   plan.
2. **Settle unknowns by prototype first** (see `prototype`), not by guessing in the plan.
   Ask the operator only about a product/preference call no experiment can settle — and give
   options, don't block.
3. **Explore in subagents,** each returning file pointers, conventions, test commands, and
   entry points — not inlined dumps. Keeps the planning context clean.
4. **Lock the architecture before coding.** State the module boundaries, data flow, and the
   key interfaces/contracts the change assumes, and pressure-test them: what breaks at scale,
   which decisions are hard to reverse, where the design fights the existing system? Settle
   these now — a wrong contract discovered mid-build is the expensive kind.
5. **Write the plan as a checklist.** One section per PR; **one PR = one change with its own
   evidence.** Order sections by dependency (independent work first; dependent work after its
   parent).
6. **Every box names the evidence that checks it** — a file, a log line, a screenshot, a test
   run, or a SHA. A box is checked only when that evidence exists.
7. **State the verification rule per PR:** tests alone are not sufficient. A PR is verified
   only when its unit test, a live run on the real surface, and a regression check vs the
   current baseline all pass. Name the metric/scenario for each.
8. **Hand back.** Post the plan path and stop. Implementation starts only on the operator's
   explicit go, under whichever execution flow the plan names.

## Guardrails

- Do not implement in this playbook — planning only.
- No box is "done" on intent; only on named evidence.
- Keep it a how-to checklist; put reasoning and findings in appendices, not the steps.
