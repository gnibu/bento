#!/bin/bash
source "$(dirname "$0")/../_fixtures/repo.sh"
git rev-parse HEAD~2 > "$(git rev-parse --git-path adversarial-review.head)" && git switch -q master && c README.md "readme" "docs: readme" && git push -q origin master && git switch -q eng-42-greeting && git merge -q --no-edit master
