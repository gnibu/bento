#!/bin/bash
source "$(dirname "$0")/../_fixtures/workflow.sh"
cat > cli.py <<'CODE'
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--output-dir", required=True)
args = parser.parse_args()
print(args.output_dir)
CODE
cat > README.md <<'MD'
# Export

python3 cli.py --output-dir ./export
MD
git add cli.py README.md && git commit -q -m "chore: export CLI baseline"
# Greeting and the previous export interface are already on the base; only the feature below
# belongs to this branch. The ticket scope groups its token handling and CLI contract.
# An older overlay replaces the former docs/check defaults; specialist triggers must survive.
mkdir -p .agents/bento
cat > .agents/bento/bento-ship.md <<'MD'
# Fixture overlay for bento-ship

## Version/changelog tooling
- Trigger: step 5.
- Action: replace the default step with adding an Unreleased changelog entry.
- Approval: none, local work.

## Check tooling
- Trigger: step 7.
- Action: replace the default step with running `python3 -m unittest`.
- Approval: none, local checks.
MD
git add .agents/bento/bento-ship.md && git commit -q -m "chore: configure baseline ship tooling"
git push -q origin HEAD:master
printf '\n- ENG-42 covers the password-reset token export feature, including its destination flag.\n' >> AGENTS.md
cat > reset.py <<'CODE'
import secrets


def issue_reset_token(user_id, store):
    token = secrets.token_urlsafe(32)
    store[token] = user_id
    return token
CODE
python3 - <<'PY'
from pathlib import Path
p = Path('cli.py')
p.write_text(p.read_text().replace('--output-dir', '--destination').replace('args.output_dir', 'args.destination'))
PY
cat > test_export.py <<'CODE'
import subprocess
import sys
import unittest
from reset import issue_reset_token


class ExportTest(unittest.TestCase):
    def test_destination(self):
        run = subprocess.run([sys.executable, "cli.py", "--destination", "./export"],
                             capture_output=True, text=True, check=True)
        self.assertEqual(run.stdout.strip(), "./export")

    def test_reset_token_binding(self):
        store = {}
        first = issue_reset_token(7, store)
        second = issue_reset_token(7, store)
        self.assertNotEqual(first, second)
        self.assertEqual(store[first], 7)
CODE
git add AGENTS.md reset.py cli.py test_export.py && git commit -q -m "feat: reset tokens and destination flag"
