#!/bin/bash
source "$(dirname "$0")/../_fixtures/repo.sh"
mkdir -p .agents/bento && cat > .agents/bento/bento-ship.md <<'MD'
# bento-ship overlay

- When the user asks for a review, add the `greptile` label to the PR.
- Verify (default): also run `ruff check .` before pushing.
MD
git add -A && git commit -q -m "chore: add bento-ship overlay"
