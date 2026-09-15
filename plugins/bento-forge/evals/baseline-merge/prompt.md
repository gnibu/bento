---
max_turns: 3
timeout_seconds: 300
allowed_tools: [Skill, Read]
---

This is a hypothetical planning exercise, not a repository on disk. Do not inspect
the working directory, search for repository files, or execute commands. Consult
the relevant available bento command/skill if present, then answer in at most 300
words. If bento is unavailable, propose your own workflow without searching for it.

Use bento-improve to propose how to capture a recurring repo-specific test-command
gotcha in AGENTS.md. This repo was initialized with bento-init and has
.bento-state/baseline.json. A teammate has since hand-edited the relevant
AGENTS.md paragraph. The learning changes that same paragraph, so the generated
change may conflict. Explain the precise preview/apply sequence, which content
becomes the next baseline, and what happens if it conflicts, including in unattended
promotion. Don't edit anything.
