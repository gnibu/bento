#!/bin/bash
source "$(dirname "$0")/../_fixtures/repo.sh"
# A finished Codex run that ended on its usage limit.
echo EXIT=1 > "$(git rev-parse --git-path adversarial-review.exit)"
: > "$(git rev-parse --git-path adversarial-review.md)"
printf '%s\n' 'OpenAI Codex v0.98.0 (research preview)' '--------' 'workdir: .' 'model: gpt-6.2-astra' \
  "ERROR: You've hit your usage limit. Upgrade to Pro or try again in 3 days 4 hours." \
  > "$(git rev-parse --git-path adversarial-review.log)"
