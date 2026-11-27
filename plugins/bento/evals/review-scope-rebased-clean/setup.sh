#!/bin/bash
# Reviewed through the second commit, then master moved on another file and the branch was
# rebased onto it cleanly: the reviewed commits keep their patches under new shas.
source "$(dirname "$0")/../_fixtures/repo.sh"
git rev-parse HEAD~1 > "$(git rev-parse --git-path adversarial-review.head)"
git switch -q master && printf 'x\n' > other.txt && git add -A && git commit -q -m "chore: other" && git push -q origin master
git switch -q eng-42-greeting && git rebase -q master
