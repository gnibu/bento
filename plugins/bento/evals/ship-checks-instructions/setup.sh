#!/bin/bash
# A consumer repo wired by bento-setup on master, and a branch on which a feature agent edited
# the root AGENTS.md directly, without bento-learn: a long e2e gotcha about web/e2e/ and a
# line that restates bento's Ship principle.
source "$(dirname "$0")/../_fixtures/repo.sh"
git switch -q master
python3 "$(dirname "$0")/../../skills/bento-setup/scripts/agents_block.py" --terse on AGENTS.md >/dev/null
ln -s AGENTS.md CLAUDE.md
git add -A && git commit -q -m "chore: wire bento"
git push -q origin master
git switch -q eng-42-greeting
git rebase -q master
mkdir -p web/e2e
printf 'test("checkout", () => {});\n' > web/e2e/checkout.spec.ts
printf 'import unittest\nimport app\n\nclass T(unittest.TestCase):\n    def test_shout(self):\n        self.assertEqual(app.shout("a"), "HI A")\n' > test_app.py
python3 - <<'PY'
from pathlib import Path
agents = Path("AGENTS.md")
text = agents.read_text()
add = ("- **E2E flakiness:** the browser tests in web/e2e/ fail now and then on CI because the seeded users"
       " expire after an hour, so rerun `make seed` before `npm run e2e`, and if that doesn't help delete"
       " web/e2e/.auth/ and rerun the whole suite with two workers.\n"
       "- Asked to commit or open a PR: run bento-ship.\n")
agents.write_text(text.replace("- Checks: `python3 -m unittest`.\n", "- Checks: `python3 -m unittest`.\n" + add))
PY
git add -A && git commit -q -m "test: checkout e2e spec, AGENTS.md notes"
