#!/bin/bash
source "$(dirname "$0")/../../_fixtures/repo.sh"
git branch -q -m greeting
# The overlay lands on master, so the branch diff stays the feature alone.
branch=$(git branch --show-current) && git switch -q master
mkdir -p .agents/bento && cat > .agents/bento/bento-ship.md <<'OVERLAY'
# Overlay for bento-ship

<!-- bento:preferences:start -->
## Ship preferences
Written by `bento-setup`; change with `/bento-setup --preferences`.

- Missing ticket: never
- Ticket update: yes
- Tracker: Linear, team ENG, review status In Review
- QA: always
- Pre-PR review: always
- Learnings: yes
- PR reviewers: none
<!-- bento:preferences:end -->
OVERLAY
git add -A && git commit -q -m "chore: add bento-ship preferences"
git push -q origin master && git switch -q "$branch" && git rebase -q master
