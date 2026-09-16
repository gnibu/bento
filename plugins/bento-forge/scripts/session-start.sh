#!/usr/bin/env bash
# SessionStart-hook entry for learnings and occasional manual-update reminders.
#
# The surface+ask half of the loop the Stop hook cannot do. It counts learnings
# that have RIPENED — recurred across >= BENTO_IMPROVE_THRESHOLD distinct
# sessions in the local ledger (ledger.sh does the counting) — and, if any,
# injects model-visible context so the agent can offer to review them and open a
# PR via the session-learn / bento-improve skill. Also occasionally asks the agent
# to check for a newer Bento version before offering a manual update.
#
# SessionStart `additionalContext` IS surfaced to the model on both Claude and
# Codex, unlike a Stop hook's — which is why surfacing happens here, not at Stop.
# This makes the loop env-independent and cross-agent: banking (Stop) and
# surfacing (SessionStart) each use only what its hook can actually do.
#
# The hook uses no LLM or network and writes only a local throttle timestamp.
# When due, the agent checks upstream; it prompts only for a confirmed update.
#
# Wire it PERSONALLY: SessionStart -> session-start.sh. See references/stop-hook.md.

set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
THRESHOLD="${BENTO_IMPROVE_THRESHOLD:-3}"

ripe="$("$here/ledger.sh" ripe "$THRESHOLD" 2>/dev/null || true)"
msg=""
if [ -n "$ripe" ]; then
  n="$(printf '%s\n' "$ripe" | grep -c .)"
  msg="$n bento learning(s) have ripened across recent sessions. Offer to review them and open a PR via the bento-improve / session-learn skill (preview: worker.sh --preview-issue)."
fi

reminder="$(python3 "$here/update-reminder.py" 2>/dev/null || true)"
if [ -n "$reminder" ]; then
  msg="${msg:+$msg }$reminder"
fi
[ -n "$msg" ] || exit 0

if command -v jq >/dev/null 2>&1; then
  jq -nc --arg m "$msg" '{hookSpecificOutput:{hookEventName:"SessionStart",additionalContext:$m}}'
else
  printf '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"%s"}}\n' "$msg"
fi
