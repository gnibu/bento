#!/bin/bash
# A branch adding a client whose retry loop the pre-PR review questions.
source "$(dirname "$0")/../_fixtures/repo.sh"
printf 'def fetch(get):\n    while True:\n        r = get()\n        if r.status != 401:\n            return r\n' > client.py
git add -A && git commit -q -m "feat: add client"
