#!/bin/bash
source "$(dirname "${BASH_SOURCE[0]}")/repo.sh"
mkdir -p src tests docs .agents/bento
cat > AGENTS.md <<'MD'
# Repository rules
- Base branch: master. Forge: local fixture. Tracker: none.
- Checks for src/: python3 -m unittest discover -s src
- No production or network writes. Do not edit policies/ or .agents/.
- Ownership snapshot supplied by the operator: no open PRs or owned tracker work.
MD
cat > .agents/bento/bento-maintain.md <<'MD'
# Fixture overlay for bento-maintain
## Verification
- Trigger: code-improvement or error-fix.
- Action: run python3 -m unittest discover -s src before and after changes.
- Approval: local checks only.
## Protected files
- Trigger: every task.
- Action: never edit policies/, .agents/ or existing test assertions. No tracker writes.
- Approval: none.
MD
mkdir -p policies
printf 'Never change production data.\n' > policies/safety.md
git add -A
git commit -q -m "test: maintenance policy"
