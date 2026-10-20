#!/bin/bash
source "$(dirname "$0")/../_fixtures/maintenance.sh"
cat > src/cleanup.py <<'PY'
from shared import normalize

def name(value):
    return value.strip().casefold()
PY
cat > src/shared.py <<'PY'
def normalize(value):
    return value.strip().casefold()
PY
cat > src/test_cleanup.py <<'PY'
import unittest
from cleanup import name
from shared import normalize

class CleanupTests(unittest.TestCase):
    def test_equivalent_keys(self):
        for value in (" A ", "Straße", ""):
            self.assertEqual(name(value), normalize(value))
PY
git add -A
git commit -q -m "test: maintenance-missing-tools"
