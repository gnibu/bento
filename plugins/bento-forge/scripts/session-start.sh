#!/usr/bin/env bash
# SessionStart-hook entry for learnings and occasional manual-update reminders.
#
# The surface+ask half of the loop the Stop hook cannot do. Every valid candidate
# is human-reviewable by default (BENTO_IMPROVE_SURFACE_THRESHOLD=1), while the
# separate BENTO_IMPROVE_THRESHOLD still protects unattended auto-promotion.
# This hook also re-arms durable pending analyses whose detached waiter was lost,
# and occasionally asks the agent to check for a newer Bento version.
#
# SessionStart `additionalContext` IS surfaced to the model on both Claude and
# Codex, unlike a Stop hook's — which is why surfacing happens here, not at Stop.
# This makes the loop env-independent and cross-agent: banking (Stop) and
# surfacing (SessionStart) each use only what its hook can actually do.
#
# The hook itself uses no LLM or network. It may re-arm a local pending worker
# and update the local reminder timestamp. When due, the agent checks upstream;
# it prompts only for a confirmed update.
#
# Wire it PERSONALLY: SessionStart -> session-start.sh. See references/stop-hook.md.

set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
SURFACE_THRESHOLD="${BENTO_IMPROVE_SURFACE_THRESHOLD:-1}"

# Best-effort Stop waiters are backed by persistent jobs. Recovery is detached
# and silent so SessionStart stays fast; recovered candidates surface on a later
# session once their reflection completes.
"$here/pending-session.sh" recover >/dev/null 2>&1 || true

ripe="$("$here/ledger.sh" ripe "$SURFACE_THRESHOLD" 2>/dev/null || true)"
msg=""
if [ -n "$ripe" ]; then
  n="$(printf '%s\n' "$ripe" | grep -c .)"
  keys="$(printf '%s\n' "$ripe" | awk 'BEGIN{ORS=""} NR>1{printf ", "} {printf "%s", $0}')"
  msg="$n bento learning candidate(s) are ready for human review (keys: $keys). Review them now via the bento-improve / session-learn skill: read their ledger evidence, verify each against the repo, propose concrete diffs, and apply only after explicit approval. Recurrence is required only for unattended auto-promotion."
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
