#!/bin/bash
# Shared eval fixture, sourced by each case's setup.sh: a repo whose origin is a local bare
# repo, on branch eng-42-greeting with three commits over origin/master. Fixed identities
# and dates keep every sha deterministic, so prompts and graders can name them.
set -euo pipefail
export GIT_AUTHOR_NAME=Dev GIT_AUTHOR_EMAIL=dev@example.com GIT_AUTHOR_DATE=2026-01-01T00:00:00Z
export GIT_COMMITTER_NAME=Dev GIT_COMMITTER_EMAIL=dev@example.com GIT_COMMITTER_DATE=2026-01-01T00:00:00Z
git init -q -b master .
git config user.name Dev && git config user.email dev@example.com && git config commit.gpgsign false
cat > AGENTS.md <<'MD'
# Agents

- Base branch: `master`. Forge: GitHub. Tracker: Linear; the ticket id is in the branch name.
- Review status: `In Review`.
- Checks: `python3 -m unittest`.
MD
printf 'def greet(name):\n    return "hi " + name\n' > app.py
git add -A && git commit -q -m "chore: init"
git init -q --bare .origin.git && echo .origin.git >> .git/info/exclude
git remote add origin ./.origin.git && git push -q origin master
git switch -q -c eng-42-greeting
c() { printf '%s\n' "$2" >> "$1" && git add "$1" && git commit -q -m "$3"; }
c app.py 'def shout(name):' 'feat: add shout'
c app.py '    return greet(name).upper()' 'feat: shout upper-cases the greeting'
c app.py '# end' 'chore: mark end of module'
