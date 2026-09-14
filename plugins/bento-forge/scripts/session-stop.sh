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
# Cheap skips so a trivial session costs nothing: no session id, no readable
# transcript, or a trivial session (fewer than 2 user turns AND no tool use)
# exits before spawning — a "say hi" session pays for nothing. A per-session
# sentinel keeps it to once per session. The digest gate inside the worker is
# the real quality filter; this is only a spawn-or-not pre-check.
#
# Why detached, not cron: a scheduler would have to rediscover which sessions
# ended and when; the Stop hook already knows and hands us the exact transcript.
# The worker is detached (all fds closed, reparented) so the visible session ends
# normally while the retrospective runs behind it.
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

sentinel="${TMPDIR:-/tmp}/bento-improve-${session_id}.done"

# Already handled this session → silent.
[ -e "$sentinel" ] && exit 0

touch "$sentinel" 2>/dev/null || true

transcript="$(field transcript_path)"
cwd="$(field cwd)"
[ -n "$transcript" ] || transcript="$HOME/.claude/projects/$(printf '%s' "${cwd:-$PWD}" | tr -c 'A-Za-z0-9' '-')/${session_id}.jsonl"

# Trivial-session skip. No transcript to read → nothing to learn from. Otherwise,
# a session with fewer than 2 operator turns AND no tool use taught nobody
# anything (it never touched the repo); don't pay a worker to reflect on it. The
# counts mirror the shapes digest.sh reads, over one file, so this is cheap.
[ -r "$transcript" ] || exit 0
if command -v jq >/dev/null 2>&1; then
  uturns="$(jq -r 'select(.type=="user" and (.isMeta|not) and ((.message.content|type)=="string")) | 1' "$transcript" 2>/dev/null | wc -l | tr -d ' ')"
  tools="$(jq -r 'select(.type=="assistant") | (.message.content[]? | select(.type=="tool_use") | 1)' "$transcript" 2>/dev/null | wc -l | tr -d ' ')"
  [ "${uturns:-0}" -lt 2 ] && [ "${tools:-0}" -eq 0 ] && exit 0
fi

# Hand the finished session to a detached worker and say nothing. Every fd is
# closed and the child reparented — Claude Code exiting cannot take the
# retrospective down with it. BENTO_IMPROVE_WORKER overrides the worker path
# (tests point it at a stub so no LLM runs).
worker="${BENTO_IMPROVE_WORKER:-$(dirname "$0")/worker.sh}"
nohup "$worker" \
  --transcript "$transcript" \
  --session "$session_id" \
  --cwd "${cwd:-$PWD}" >/dev/null 2>&1 &
exit 0
