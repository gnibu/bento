#!/bin/bash
source "$(dirname "$0")/../_fixtures/workflow.sh"
git switch -q master
git merge -q --squash eng-42-greeting && git commit -q -m "chore: baseline"
git push -q origin master
git switch -q eng-42-greeting
git reset -q --hard master
printf '
# Greeting formatting lives here.
' >> formatter.py
git add formatter.py && git commit -q -m "docs: clarify internal comment"
