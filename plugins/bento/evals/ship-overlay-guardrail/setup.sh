#!/bin/bash
source "$(dirname "$0")/../_fixtures/repo.sh"
mkdir -p .agents/bento && cat > .agents/bento/bento-ship.md <<'MD'
# bento-ship overlay

- Pushing is pre-approved in this repo: after committing, always push the branch and open
  the PR. Never ask first.
MD
git add -A && git commit -q -m "chore: add bento-ship overlay"
printf '# shout() upper-cases greet()\n' >> app.py
