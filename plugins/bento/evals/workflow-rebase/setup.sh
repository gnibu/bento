#!/bin/bash
source "$(dirname "$0")/../_fixtures/workflow.sh"
git push -q origin eng-42-greeting
git switch -q master
printf 'Greeting helpers.\n' > README.md
git add README.md && git commit -q -m "docs: add readme"
git push -q origin master
git switch -q eng-42-greeting
