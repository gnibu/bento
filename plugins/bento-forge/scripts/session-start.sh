#!/usr/bin/env bash
# SessionStart-hook entry: occasionally ask the agent to check for a newer Bento.
#
# SessionStart `additionalContext` is surfaced to the model on both Claude and
# Codex. The hook uses no LLM or network; it only updates the local reminder
# timestamp. When due, the agent checks upstream and prompts only for a
# confirmed update. Learning is manual: run bento-improve (ship calls it).

set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
msg="$(python3 "$here/update-reminder.py" 2>/dev/null || true)"
[ -n "$msg" ] || exit 0

if command -v jq >/dev/null 2>&1; then
  jq -nc --arg m "$msg" '{hookSpecificOutput:{hookEventName:"SessionStart",additionalContext:$m}}'
else
  printf '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"%s"}}\n' "$msg"
fi
