# Changelog

## 0.2.0 — 2026-10-13

First versioned release since 0.1.1. It also carries the npx-skills install and `bento-*`
names (#26) and `bento-adversarial-review` (#28).

- **Repo overlays.** Every bento skill reads `AGENTS.md`/`CLAUDE.md`, then its overlay
  `.agents/bento/<skill-name>.md` if the repo has one. Overlays add rules and may replace steps
  marked *(default)*; they never relax a guardrail. `bento-learn` routes repo-specific
  learnings about a bento skill there; `bento-setup` never creates or deletes them.
- **`bento-adversarial-review` picks its own scope.** It skips a branch already reviewed at
  `HEAD`, reviews only the commits since the last review when history allows, and returns the
  reviewed sha in ship mode. An explicit scope still wins.
- **`bento-ship` holds the whole PR flow**, so a repo needs no PR skill of its own: commit
  first, one PR per ticket, stale-base detection, a single `ACTION REQUIRED` stop for
  learnings and decisions, push recovery, PR title and body rules, ticket comment and status
  with a re-check, and a report naming the pre-PR review (local) and the PR's reviewers.
