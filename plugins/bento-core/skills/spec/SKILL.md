---
name: spec
description: |
  Turn a vague intent into a precise, executable spec before building. Use when the ask is
  fuzzy or underspecified and jumping to code would guess wrong. Triggers: "spec this out",
  "write a spec", "nail down requirements", "what exactly should this do".
---

# Spec

Convert "I want X" into a spec precise enough that implementation is mechanical and success is
checkable. The spec is the deliverable — don't implement here.

## Steps (paste as todos)

1. **State the goal and the user** in one or two lines — what changes, for whom, and why now.
2. **Resolve the unknowns.** Settle empirical questions by a quick `prototype`, not by
   guessing. Ask the user only genuine product/preference calls no experiment can settle —
   and offer options, don't block.
3. **Write the behavior contract.** The observable behavior: inputs, outputs, states, and the
   edge cases (empty, error, boundary, unauthorized). Concrete, not aspirational.
4. **Define done as checkable acceptance criteria** — each a condition you could verify on the
   real artifact (a test, a screenshot, a value). If you can't check it, it's not a criterion.
5. **Note constraints and non-goals** — what's explicitly out of scope, and any hard
   limits (perf, compat, data boundaries).
6. **Hand off.** Write the spec to a file; stop. Implementation starts from it (`multi-phase-plan`
   if large, otherwise directly).

## Guardrails

- Don't implement — this produces the spec, not the code.
- Every acceptance criterion must be verifiable on a real artifact; drop vague ones.
- Keep unknowns out of the spec: resolve them (prototype/ask) or list them as explicit open
  questions, never silently assume.
