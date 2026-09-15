#!/usr/bin/env bash
# Wire principles and, for a vendored .bento submodule, bootstrap Claude plugins.
set -euo pipefail

BENTO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ "${1:-}" == "--codex" ]]; then
  shift
  exec python3 "$BENTO_DIR/install/bento-codex.py" "$@"
fi
if [[ "${1:-}" == "--claude-hooks" ]]; then
  shift
  exec python3 "$BENTO_DIR/install/bento-claude-hooks.py" "$@"
fi
if [[ $# -gt 0 ]]; then
  echo "usage: bash install.sh [--codex [options] | --claude-hooks [options]]" >&2
  exit 1
fi
# Keep this before the import's idempotency check: existing principles do not prove
# that this machine has registered the marketplace or installed the plugins.
BENTO_DIR="$(python3 "$BENTO_DIR/install/claude-plugins.py" "$BENTO_DIR")"
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
