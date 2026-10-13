#!/bin/bash
source "$(dirname "$0")/../_fixtures/repo.sh"
git switch -q -c gone master && c app.py "# gone" "chore: dropped" && git rev-parse HEAD > "$(git rev-parse --git-path adversarial-review.head)" && git switch -q eng-42-greeting && git branch -q -D gone
