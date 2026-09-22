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
# debounces: each turn bumps an activity token and arms a single detached waiter
# that reflects ONCE, on the complete transcript, after the session has been idle
# for a quiescence window (BENTO_IMPROVE_QUIESCE_SECS, default 300s). A long
# 60-turn session is therefore learned from in full — not from the early slice
# present at the first stop. The digest gate inside the worker is the real
# quality filter; the checks here only decide whether to arm the waiter.
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
# Debounce to quiescence: every turn bumps an activity token; the first arms ONE
# detached waiter (mkdir is the atomic guard) that sleeps a window and re-checks
# the token, waiting again while turns keep coming. Once the session has been
# idle for the whole window it reflects ONCE on the now-complete transcript — so
# a 60-turn session is learned from in full, not from the slice present when it
# first crossed the gate. No reliable end-of-session hook exists for headless
# Claude or Codex, so quiescence is the portable stand-in.
state_dir="${TMPDIR:-/tmp}/bento-improve-${session_id}"
mkdir -p "$state_dir" 2>/dev/null || true
# Unique per turn (pid + RANDOM), so the token always changes even within one
# clock second — the waiter can trust "unchanged" to mean "no turn happened".
printf '%s.%s.%s\n' "$(date +%s)" "${RANDOM:-0}" "$$" >"$state_dir/gen" 2>/dev/null || true

# A waiter already covers this session → we only needed to bump the token.
mkdir "$state_dir/waiter" 2>/dev/null || exit 0

quiesce="${BENTO_IMPROVE_QUIESCE_SECS:-300}"
worker="${BENTO_IMPROVE_WORKER:-$(dirname "$0")/worker.sh}"

# Detached AND in its own process group: all fds closed and the child reparented
# (survives the parent exiting), nohup ignores SIGHUP, and `set -m` makes the
# backgrounded job a group leader so a session-close signal aimed at Claude's
# process group cannot reach the waiter while it sleeps. Verified: without the
# own-group step the waiter shares — and dies with — the session's group; setsid
# is absent on macOS, so `set -m` is the portable route. The visible session ends
# normally while the waiter idles behind it, then hands off to the worker.
# BENTO_IMPROVE_WORKER overrides the worker (tests use a stub).
set -m 2>/dev/null || true
{ nohup bash -c '
  set -u
  gen="$1"; lock="$2"; quiesce="$3"; worker="$4"; transcript="$5"; session="$6"; cwd="$7"
  while :; do
    mine="$(cat "$gen" 2>/dev/null || true)"
    sleep "$quiesce"
    [ "$(cat "$gen" 2>/dev/null || true)" = "$mine" ] && break
  done
  rmdir "$lock" 2>/dev/null || true
  "$worker" --transcript "$transcript" --session "$session" --cwd "$cwd"
' bento-waiter \
  "$state_dir/gen" "$state_dir/waiter" "$quiesce" "$worker" \
  "$transcript" "$session_id" "${cwd:-$PWD}" >/dev/null 2>&1 & } 2>/dev/null
exit 0
