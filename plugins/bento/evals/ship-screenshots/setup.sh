#!/bin/bash
# The qa-web-ui counter app, with a tracker named in AGENTS.md and ticket ENG-42 in the branch.
source "$(dirname "$0")/../qa-web-ui/setup.sh"
git switch -q master
printf -- '- Forge: GitHub. Tracker: Linear; the ticket id is in the branch name.\n- Review status: `In Review`.\n' >> AGENTS.md
git commit -qam "chore: name the tracker"
git switch -q ui-reset && git rebase -q master && git branch -m eng-42-reset
