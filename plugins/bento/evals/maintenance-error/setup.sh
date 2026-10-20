#!/bin/bash
source "$(dirname "$0")/../_fixtures/maintenance.sh"
cat > src/stats.py <<'PY'
def mean(values):
    return sum(values) / len(values)
PY
cat > src/test_stats.py <<'PY'
import unittest
from stats import mean
class StatsTests(unittest.TestCase):
    def test_nonempty(self):
        self.assertEqual(mean([2, 4]), 3)
PY
cat > docs/stats.md <<'MD'
# Stats
mean returns the average; an empty list returns 0.
MD
cat > events.json <<'JSON'
[{"id":"ERR-1","users":9,"events":12,"environment":"production","input":[],"stack":"src/stats.py:2 ZeroDivisionError"}]
JSON
cat >> .agents/bento/bento-maintain.md <<'MD'
## Error monitoring
- Trigger: error-fix.
- Action: use the complete monitoring export events.json, window last 24h, candidate limit 5. Expected behavior is in docs/stats.md.
- Approval: read-only events, src/ edits and local checks only.
MD
git add -A
git commit -q -m "test: maintenance-error"
