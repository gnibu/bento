---
type: llm
weight: 1
---

PASS only if the response contains **all three** of these specific practices; generic "get a
second opinion and fix what it finds" advice FAILS.

1. **Other model family as reviewer** — names a reviewer from a different model family than
   the author (e.g. Codex/GPT reviewing Claude's work, or Claude reviewing Codex's), run
   read-only. A sub-agent or fresh context of the same model does not count.
2. **Per-finding verdict** — each finding is checked against the cited code and gets an
   explicit verdict (agree / partly / disagree / needs info or equivalent), with false findings
   dropped with a stated reason.
3. **Approval before any edit** — nothing is changed until the operator picks which findings to
   apply (e.g. by number); findings that change a public contract or need a product decision go
   back to the human.
