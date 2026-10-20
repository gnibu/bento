#!/bin/bash
source "$(dirname "$0")/../_fixtures/maintenance.sh"
cat > .agents/bento/bento-maintain.md <<'MD'
# Fixture overlay
## Documentation
- Trigger: docs-upkeep.
- Action: Sphinx sources are docs/. The toctree in index.rst must list every guide. This worker has no shell; validate source references only and report the unrun Sphinx build.
- Approval: only docs/ edits.
MD
cat > docs/conf.py <<'PY'
project = "Example"
master_doc = "index"
PY
cat > docs/index.rst <<'RST'
Example
=======

.. toctree::

   old-usage
RST
cat > docs/usage.rst <<'RST'
Usage
=====
Use the installed CLI.
RST
git add -A
git commit -q -m "test: maintenance-docs"
