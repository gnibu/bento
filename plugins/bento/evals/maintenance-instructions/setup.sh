#!/bin/bash
source "$(dirname "$0")/../_fixtures/maintenance.sh"
mkdir -p area
cat > area/AGENTS.md <<'MD'
# Area
- Before editing this area, read [testing](../docs/old-testing.md).
- Never change production data.
MD
cat > area/CLAUDE.md <<'MD'
@AGENTS.md
MD
cat > docs/testing.md <<'MD'
# Testing
Run the unit tests using the repository checks.
MD
git add -A
git commit -q -m "test: maintenance-instructions"
