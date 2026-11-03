#!/bin/bash
source "$(dirname "$0")/../_fixtures/maintenance-tracker.sh"
cat > src/stats.py <<'PY'
def mean(values):
    return sum(values) / len(values)

def median(values):
    return sorted(values)[len(values) // 2]

def ratio(part, total):
    return part / total
PY
cat > src/test_stats.py <<'PY'
import unittest
from stats import mean, median, ratio
class StatsTests(unittest.TestCase):
    def test_nonempty(self):
        self.assertEqual(mean([2, 4]), 3)
        self.assertEqual(median([1, 2, 3]), 2)
        self.assertEqual(ratio(1, 2), 0.5)
PY
cat > docs/stats.md <<'MD'
# Stats
mean and median return 0 for an empty list; ratio returns 0 for a zero total.
MD
cat > tickets.json <<'JSON'
[{"id":"TCK-1","issue":"ERR-1","state":"done","closed_at":"2026-09-01"},
 {"id":"TCK-2","issue":"ERR-2","state":"done","closed_at":"2026-10-20"},
 {"id":"TCK-3","issue":"ERR-3","state":"canceled","closed_at":"2026-09-15","closed_by":"a maintainer","note":"Not worth fixing."}]
JSON
cat > events.json <<'JSON'
[{"id":"ERR-3","link":"https://monitor.example/ERR-3","users":600,"events":900,"last_seen":"2026-10-30","environment":"production","input":[1,0],"stack":"src/stats.py:8 ZeroDivisionError"},
 {"id":"ERR-2","link":"https://monitor.example/ERR-2","users":500,"events":700,"last_seen":"2026-10-15","environment":"production","input":[],"stack":"src/stats.py:5 IndexError"},
 {"id":"ERR-1","link":"https://monitor.example/ERR-1","users":240,"events":310,"last_seen":"2026-10-30","environment":"production","input":[],"stack":"src/stats.py:2 ZeroDivisionError"}]
JSON
cat >> .agents/bento/bento-maintain.md <<'MD'
## Error monitoring
- Trigger: error-fix.
- Action: use the complete monitoring export events.json as the candidate set, limit 5. Expected behavior is in docs/stats.md.
- Approval: read-only events, src/ edits and local checks only.
MD
git add -A
git commit -q -m "test: maintenance-error-regression"
