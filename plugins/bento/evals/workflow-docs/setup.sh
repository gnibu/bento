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
cat > CHANGELOG.md <<'MD'
# Changelog

## Unreleased
MD
git add cli.py README.md CHANGELOG.md && git commit -q -m "chore: export CLI baseline"
python3 - <<'PY'
from pathlib import Path
p = Path('cli.py')
p.write_text(p.read_text().replace('--output-dir', '--destination').replace('args.output_dir', 'args.destination'))
PY
