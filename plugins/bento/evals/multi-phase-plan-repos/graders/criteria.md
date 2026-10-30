---
type: llm
weight: 1
---

PASS if the plan has exactly one PR per repository (api, web, mobile: three PRs), with the
api PR first because web and mobile depend on its deploy. FAIL if any repository's work is
split into several PRs (for example api migration, model and endpoint as separate PRs).
