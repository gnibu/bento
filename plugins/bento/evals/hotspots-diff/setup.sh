#!/bin/bash
# master already has a tangled legacy() the branch never touches; the branch's last commit
# turns shout() into a nested mess. Only shout() is this branch's regression.
source "$(dirname "$0")/../_fixtures/repo.sh"
git switch -q master
cat > legacy.py <<'PY'
def legacy(a, b, c):
    for x in a:
        if x:
            for y in b:
                if y:
                    while c:
                        if x and y:
                            c -= 1
    return c
PY
git add -A && git commit -q -m "chore: legacy" && git push -q origin master
git switch -q eng-42-greeting && git rebase -q master
cat > app.py <<'PY'
def greet(name):
    return "hi " + name


def shout(name, loud=True, polite=False, excited=False):
    if name:
        if loud:
            if polite:
                if excited:
                    return "PLEASE, " + greet(name).upper() + "!"
                else:
                    return "PLEASE, " + greet(name).upper()
            else:
                if excited:
                    return greet(name).upper() + "!"
                else:
                    return greet(name).upper()
        else:
            return greet(name)
    return ""
PY
git add -A && git commit -q -m "feat: shout options"
# The eval sandbox has no network, so uv can't fetch lizard: give the repo a local env.
python3 -m venv .venv && .venv/bin/pip install -q lizard && echo .venv >> .git/info/exclude
