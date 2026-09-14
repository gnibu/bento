---
type: llm
weight: 1
---

Score how well the response applies **safe refactoring** discipline. A strong answer covers
most of:

- **Pin behavior first** — write a characterization test / snapshot / equivalence harness
  before moving structure (and "type-check/lint is not a pin").
- **Behavior-preserving steps** — small moves, keeping the pin green; migrate all callers and
  delete the old API together (no compatibility shims / parallel paths).
- **Prove equivalence on the real artifact** — not "it compiles"; keep the change only if it
  lowers reader load, else revert.

Full credit: pin-first + behavior-preserving migration + equivalence proof all present.
Partial: generic "write tests, go slowly" without pinning-before-moving. Low: no notion of
locking behavior before changing structure.
