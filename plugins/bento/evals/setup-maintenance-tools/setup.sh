#!/bin/bash
source "$(dirname "$0")/../_fixtures/maintenance.sh"
mkdir -p docs src .agents/skills
mkdir -p .agents/skills/bento-maintain
cat > .agents/skills/bento-maintain/SKILL.md <<'MD'
---
name: bento-maintain
description: Installed marker for setup discovery.
---
MD
cat > AGENTS.md <<'MD'
# Repository rules
- Forge: GitLab. Tracker: GitLab issues; no separate tracker service.
- Checks: make check. No network or remote writes during setup.
- Documentation: Sphinx, docs/conf.py and docs/index.rst; make docs-check.
- Monitoring: Bugsnag, project reports; use the repository procedure docs/monitoring.md.
MD
cat > Makefile <<'MAKE'
check:
	python3 -m unittest
docs-check:
	sphinx-build -b linkcheck docs /tmp/example-docs
MAKE
cat > docs/conf.py <<'PY'
project = "Example"
master_doc = "index"
PY
cat > docs/index.rst <<'RST'
Example
-------
.. toctree::

   monitoring
RST
cat > docs/monitoring.md <<'MD'
# Monitoring
Use the connected Bugsnag tool to read project reports, production events from the last
24 hours, limit 5. If the tool is not connected, report access unverified.
MD
cat > .agents/bento/bento-maintain.md <<'MD'
# Repository overlay
## Manual protected paths
- Trigger: every task.
- Action: never edit src/generated/.
- Approval: no exception.
MD
git add -A
git commit -q -m "test: setup-maintenance-tools"
