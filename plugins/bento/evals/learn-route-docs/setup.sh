#!/bin/bash
# A repo whose docs/ has no developer guide: only a deploy runbook. bento-learn must still
# keep a test procedure out of the root AGENTS.md.
source "$(dirname "$0")/../_fixtures/repo.sh"
mkdir -p docs billing
printf '# Deploy\n\nRun `make deploy` from master after CI is green.\n' > docs/DEPLOY.md
printf 'def total(lines):\n    return sum(line.cents for line in lines)\n' > billing/invoice.py
git add -A && git commit -q -m "chore: billing and deploy runbook"
