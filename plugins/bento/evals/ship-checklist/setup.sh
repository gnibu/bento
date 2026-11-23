#!/bin/bash
# A consumer repo wired by bento-setup on master, with the downstream repo's ship preferences,
# and a three-commit branch whose diff looks too small to learn from.
source "$(dirname "$0")/../_fixtures/repo.sh"
git switch -q master
python3 "$(dirname "$0")/../../skills/bento-setup/scripts/agents_block.py" --terse on AGENTS.md >/dev/null
ln -s AGENTS.md CLAUDE.md
mkdir -p .agents/bento
cat > .agents/bento/bento-ship.md <<'MD'
<!-- bento:preferences:start -->
## Ship preferences
Written by `bento-setup`; change with `/bento-setup --preferences`.

- Missing ticket: create
- Ticket update: yes
- Tracker: Linear, team ENG, review status In Review
- QA: always
- Pre-PR review: always
- Pre-PR review gate: all branches
- Learnings: yes
- PR reviewers: none
<!-- bento:preferences:end -->
MD
git add -A && git commit -q -m "chore: wire bento"
git push -q origin master
git switch -q eng-42-greeting
git rebase -q master
