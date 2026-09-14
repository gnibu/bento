#!/usr/bin/env bash
# SessionStart-hook entry for bento-improve. Read-only, no LLM, no side effects.
#
# The surface+ask half of the loop the Stop hook cannot do. It counts learnings
# that have RIPENED — recurred across >= BENTO_IMPROVE_THRESHOLD distinct
# sessions in the local ledger (ledger.sh does the counting) — and, if any,
# injects model-visible context so the agent can offer to review them and open a
# PR via the session-learn / bento-improve skill. Nothing ripe → no output.
#
# SessionStart `additionalContext` IS surfaced to the model on both Claude and
# Codex, unlike a Stop hook's — which is why surfacing happens here, not at Stop.
# This makes the loop env-independent and cross-agent: banking (Stop) and
# surfacing (SessionStart) each use only what its hook can actually do.
#
# Fast and side-effect-free: one cheap ledger read, no writes, no network.
#
# Wire it PERSONALLY: SessionStart -> session-start.sh. See references/stop-hook.md.

set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
THRESHOLD="${BENTO_IMPROVE_THRESHOLD:-3}"

ripe="$("$here/ledger.sh" ripe "$THRESHOLD" 2>/dev/null || true)"
[ -n "$ripe" ] || exit 0
n="$(printf '%s\n' "$ripe" | grep -c .)"
[ "$n" -ge 1 ] || exit 0

msg="$n bento learning(s) have ripened across recent sessions. Offer to review them and open a PR via the bento-improve / session-learn skill (preview: worker.sh --preview-issue)."

if command -v jq >/dev/null 2>&1; then
  jq -nc --arg m "$msg" '{hookSpecificOutput:{hookEventName:"SessionStart",additionalContext:$m}}'
else
  printf '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"%s"}}\n' "$msg"
fi
