#!/usr/bin/env bash
# Stop-hook entry for the bento-improve autorun subsystem. ALWAYS ON, silent.
#
# On every session stop it hands the finished session to a detached worker that
# reflects + banks the learnings to a local ledger. It never nudges (a Stop hook
# cannot surface model-visible context on Claude or Codex) and it never opens a
# PR — banking is the whole job here. Ripened learnings are surfaced at the NEXT
# session start by session-start.sh, which CAN inject model-visible context.
#
# No env gate: reflect + bank runs for every substantive session so recurrence
# can be counted. Fully hands-off PR opening is a separate opt-in on the worker
# (BENTO_IMPROVE_AUTO_PR=1).
#
# Stop fires at the END OF EVERY TURN, not once at session close, so this does
# not reflect on each stop. Cheap skips first (no session id, no readable
# transcript, or a trivial <2-turn/no-tool session cost nothing). Then it
# persists the job and debounces it to a quiescence window
# (BENTO_IMPROVE_QUIESCE_SECS, default 300s). A long 60-turn session is therefore
# learned from in full — not from the early slice present at the first stop. If
# the detached waiter dies, SessionStart re-arms the durable pending job. The
# digest gate inside the worker is the real quality filter; the checks here only
# decide whether to enqueue the session.
#
# Why detached, not cron: the Stop hook already knows the exact transcript. The
# worker is detached so the visible session ends normally, while the persistent
# pending record lets SessionStart recover if that best-effort process is lost.
#
# Wire it PERSONALLY (not in committed settings): Stop -> session-stop.sh and
# SessionStart -> session-start.sh. See references/stop-hook.md. Renamed from the
# old stop-nudge.sh — update any hook that still points at the old name.
# Reads the Stop hook payload as JSON on stdin.

set -euo pipefail

payload="$(cat)"

# Extract fields without assuming jq is installed.
field() { # <name> -> value
  if command -v jq >/dev/null 2>&1; then
    printf '%s' "$payload" | jq -r --arg k "$1" '.[$k] // empty'
  else
    printf '%s' "$payload" | sed -n "s/.*\"$1\"[[:space:]]*:[[:space:]]*\"\([^\"]*\)\".*/\1/p"
  fi
}
session_id="$(field session_id)"

# No session id → can't guard against repeats; stay silent rather than respawn.
[ -n "${session_id:-}" ] || exit 0

transcript="$(field transcript_path)"
cwd="$(field cwd)"
[ -n "$transcript" ] || transcript="$HOME/.claude/projects/$(printf '%s' "${cwd:-$PWD}" | tr -c 'A-Za-z0-9' '-')/${session_id}.jsonl"

# No transcript to read → nothing to learn from.
[ -r "$transcript" ] || exit 0

# Cheap per-turn trivial skip: a session with fewer than 2 operator turns AND no
# tool use has touched nothing worth reflecting on. Unlike a sentinel it sets no
# permanent state — a later, richer turn is re-evaluated. The real quality gate
# (>=3 turns AND >=1 failure) lives in the worker's digest.sh and runs once, at
# the end, on the complete transcript.
if command -v jq >/dev/null 2>&1; then
  # Claude and Codex write different JSONL schemas. Count both here; otherwise
  # every Codex session looks empty and the real digest gate is never reached.
  # Codex also injects AGENTS.md/environment/system context as user-role
  # messages; only count those with operator text left once they are stripped.
  uturns="$(jq -r '
    if .type=="user" and (.isMeta|not) and ((.message.content|type)=="string") then 1
    elif .type=="response_item" and .payload.type=="message" and .payload.role=="user"
      then ([.payload.content[]? | select(.type=="input_text") | .text] | join("\n")
      | gsub("(?s)<(system_instruction|environment_context|recommended_plugins|user_instructions)>.*?</\\1>"; "")
      | gsub("(?s)# AGENTS\\.md instructions for [^\\n]*\\s*<INSTRUCTIONS>.*?</INSTRUCTIONS>"; "")
      | select(test("\\S")) | 1)
    else empty end' "$transcript" 2>/dev/null | wc -l | tr -d ' ')"
  tools="$(jq -r '
    if .type=="assistant"
      then (.message.content[]? | select(.type=="tool_use") | 1)
    elif .type=="response_item"
      and (.payload.type=="custom_tool_call" or .payload.type=="function_call") then 1
    else empty end' "$transcript" 2>/dev/null | wc -l | tr -d ' ')"
  [ "${uturns:-0}" -lt 2 ] && [ "${tools:-0}" -eq 0 ] && exit 0
fi

# Stop fires at the end of EVERY turn, so no single stop is "the session end".
# pending-session.sh stores the handoff under BENTO_IMPROVE_STATE, bumps its
# generation token, and maintains one detached runner. The runner waits until
# the token stays unchanged for the whole window, then reflects. SessionStart
# calls its recovery entrypoint so a killed process or reboot delays the work
# instead of losing it.
here="$(cd "$(dirname "$0")" && pwd)"
"$here/pending-session.sh" enqueue "$session_id" "$transcript" "${cwd:-$PWD}"
