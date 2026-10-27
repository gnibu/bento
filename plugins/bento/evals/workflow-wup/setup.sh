#!/bin/bash
source "$(dirname "$0")/../_fixtures/workflow.sh"
cat > formatter.py <<'CODE'
def greeting(name, prefix="hi"):
    return prefix + " " + name
CODE
