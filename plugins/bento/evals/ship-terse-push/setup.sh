#!/bin/bash
# A consumer repo wired by bento-setup (AGENTS.md block, CLAUDE.md symlink) with uncommitted work.
source "$(dirname "$0")/../_fixtures/repo.sh"
python3 "$(dirname "$0")/../../skills/bento-setup/scripts/agents_block.py" AGENTS.md >/dev/null
ln -s AGENTS.md CLAUDE.md
git add -A && git commit -q -m "chore: wire bento"
printf '\n\ndef whisper(name):\n    return greet(name).lower()\n' >> app.py
