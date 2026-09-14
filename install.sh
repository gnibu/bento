#!/usr/bin/env bash
# bento install: wire the always-on principles into the user CLAUDE.md, idempotently.
# Playbooks (bento-core) are loaded separately by installing the plugin; see README.
set -euo pipefail

BENTO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_MD="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/CLAUDE.md"
IMPORT="@${BENTO_DIR}/principles/PRINCIPLES.md"

mkdir -p "$(dirname "$CLAUDE_MD")"
touch "$CLAUDE_MD"

if grep -qF "$IMPORT" "$CLAUDE_MD"; then
  echo "bento: principles already imported in $CLAUDE_MD"
  exit 0
fi

# Append as its own block at end of file (imports mid-file are disallowed).
printf '\n# bento (personal agent kit — always-on principles)\n%s\n' "$IMPORT" >> "$CLAUDE_MD"
echo "bento: added principles import to $CLAUDE_MD"
