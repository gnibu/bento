---
type: llm
weight: 1
---

Score the response's concrete initialization workflow, not keyword density.
Full credit requires all of:

- Inspect code, documentation, and merged PR review comments as separate evidence
  sources, flag unavailable sources, and corroborate historical reviews in code.
- Check for an existing instruction layer and route it to /bento:learn rather
  than regenerate it. Explain the potion off-the-shelf option without stopping
  at the old claim that /bento:init is unimplemented.
- Separate human approval of evidence, file design, and the exact generated diff.
  No writing final files or committing before the appropriate checkpoint.
- Use AGENTS.md as shared routing content with a CLAUDE.md import and pointers
  from Codex to shared skills, avoiding duplicated instruction bodies.
- Record generated text in .bento-state/baseline.json for later three-way merging
  against current hand-edited content. A conflict must leave files and baseline
  unchanged; do not silently replace the baseline with manually edited content.

Partial credit for a workable but incomplete workflow. Low credit for generic
"analyze and generate" advice, claiming it is still a stub, skipping approval,
or proposing to overwrite an existing L2.
