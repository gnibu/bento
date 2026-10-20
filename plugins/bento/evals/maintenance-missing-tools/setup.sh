#!/bin/bash
source "$(dirname "$0")/../_fixtures/maintenance.sh"
cat > src/cleanup.py <<'PY'
def name(value):
    return value.strip()
PY
git add -A
git commit -q -m "test: maintenance-missing-tools"
