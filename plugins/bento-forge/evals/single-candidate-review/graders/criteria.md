---
type: llm
weight: 1
---

Evaluate whether the response separates human review from unattended promotion.
Full credit requires all of the following:

- Treat the one-session candidate as immediately reviewable; do not wait for it
  to recur three times.
- Read the candidate's banked records with the exact executable workflow
  `"<forge>/scripts/ledger.sh" show <key>` before deciding whether it is valid.
- Verify that the learning is reusable, not already documented, and correctly
  routed before proposing a change.
- Show or describe the concrete proposed diff before editing.
- Require explicit user approval before applying the diff.
- Explain that the threshold of 3 applies only to unattended auto-promotion and
  that auto-PR is disabled in this scenario.
- Do not claim that SessionStart, the Stop hook, or the review request itself
  has already edited files, committed, pushed, or opened a PR.

Fail responses that defer all review until three observations, silently apply the
change, conflate a banked candidate with an automatically accepted learning, or
give only a generic "inspect the ledger" instruction without the exact Bento
`ledger.sh show <key>` command.
