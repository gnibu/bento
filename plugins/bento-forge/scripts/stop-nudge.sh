#!/usr/bin/env bash
# Guarded Stop-hook trigger for the bento-improve autorun subsystem.
#
# Fires AT MOST ONCE per session, in one of two modes:
#
#   default                    inject a reminder to capture the session's learnings
#   BENTO_IMPROVE_AUTORUN=1     spawn a detached worker that does it, silently
#
# Autorun mode is why there is no cron. A scheduler would have to rediscover
# which sessions ended and when; the Stop hook already knows, and hands us the
# exact transcript path. The worker is detached so the visible session ends
# normally while the retrospective runs behind it.
#
# Wire it PERSONALLY (not in committed settings) — see references/stop-hook.md.
# Reads the Stop hook payload as JSON on stdin; emits additionalContext JSON.

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

# No session id → can't guard against repeats; stay silent rather than nag.
[ -n "${session_id:-}" ] || exit 0

sentinel="${TMPDIR:-/tmp}/bento-improve-${session_id}.done"

# Already nudged this session → silent.
[ -e "$sentinel" ] && exit 0

touch "$sentinel" 2>/dev/null || true

# Autorun: hand the finished session to a detached worker and say nothing. The
# hook must not block the session ending, so every fd is closed and the child is
# reparented — Claude Code exiting cannot take the retrospective down with it.
if [ -n "${BENTO_IMPROVE_AUTORUN:-}" ]; then
  transcript="$(field transcript_path)"
  cwd="$(field cwd)"
  [ -n "$transcript" ] || transcript="$HOME/.claude/projects/$(printf '%s' "${cwd:-$PWD}" | tr -c 'A-Za-z0-9' '-')/${session_id}.jsonl"
  nohup "$(dirname "$0")/worker.sh" \
    --transcript "$transcript" \
    --session "$session_id" \
    --cwd "${cwd:-$PWD}" >/dev/null 2>&1 &
  exit 0
fi

# `systemMessage` is the field a Stop hook surfaces to the user on BOTH Claude and Codex.
# `additionalContext` is NOT model/user-visible for the Stop event, so it can't carry the
# nudge — kept only as a harmless fallback for any host that reads it.
cat <<'JSON'
{"systemMessage":"Session winding down — consider capturing learnings via your session-learn / bento-improve skill and routing them to the right shared artifact (subsystem AGENTS.md, a skill, docs, or a code fix).","hookSpecificOutput":{"hookEventName":"Stop","additionalContext":"Session winding down — consider capturing learnings via your session-learn / bento-improve skill."}}
JSON
