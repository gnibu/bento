#!/usr/bin/env bash
# Self-check for session-stop.sh: skip trivial sessions, spawn the worker for
# substantive ones, and stay once-per-session. A stub worker (BENTO_IMPROVE_WORKER)
# stands in for the real reflect+bank so no LLM runs here.
set -uo pipefail
cd "$(dirname "$0")"
tmp="$(mktemp -d)"
# Isolate TMPDIR so per-session sentinels live in the throwaway dir — no cross-run
# contamination from a real ~/TMPDIR, and `rm -rf "$tmp"` wipes everything.
export TMPDIR="$tmp"
fails=0
check() { if [ "$2" = "$3" ]; then echo "ok   $1"; else echo "FAIL $1: expected [$2] got [$3]"; fails=$((fails+1)); fi; }

# Stub worker records that it was spawned. It replaces the reflect+bank worker.
stub="$tmp/stub-worker.sh"
printf '#!/usr/bin/env bash\necho spawned >>"%s/spawned"\n' "$tmp" >"$stub"
chmod +x "$stub"
export BENTO_IMPROVE_WORKER="$stub"

uturn() { printf '{"type":"user","isMeta":false,"message":{"content":"%s"}}\n' "$1"; }
tooluse() { printf '{"type":"assistant","message":{"content":[{"type":"tool_use","name":"Edit"}]}}\n'; }

run() { # <session_id> <transcript> -> yes|no (worker spawned?)
  rm -f "$tmp/spawned"
  echo "{\"session_id\":\"$1\",\"transcript_path\":\"$2\",\"cwd\":\"$PWD\"}" | ./session-stop.sh
  # The worker is detached; poll for its marker rather than race a fixed sleep.
  local i=0
  while [ ! -e "$tmp/spawned" ] && [ "$i" -lt 20 ]; do sleep 0.1; i=$((i+1)); done
  [ -e "$tmp/spawned" ] && echo yes || echo no
}

# trivial: one operator turn, no tool use
triv="$tmp/triv.jsonl"; uturn "hi" >"$triv"
check "trivial session (1 turn, no tools) does not spawn" "no" "$(run triv-1 "$triv")"

# substantive: 2 operator turns + a tool use
sub="$tmp/sub.jsonl"; { uturn "do a thing"; tooluse; uturn "fix it"; } >"$sub"
check "substantive session (2 turns + tool) spawns" "yes" "$(run sub-1 "$sub")"

# the skip is an AND: one turn but a tool use still spawns (it touched the repo)
mix="$tmp/mix.jsonl"; { uturn "one shot"; tooluse; } >"$mix"
check "one turn WITH tool use spawns" "yes" "$(run mix-1 "$mix")"

# missing transcript never spawns
check "missing transcript does not spawn" "no" "$(run miss-1 "$tmp/nope.jsonl")"

# sentinel: a second stop for the same session is silent
run sub-2 "$sub" >/dev/null           # first stop banks
check "second stop for same session does not respawn" "no" "$(run sub-2 "$sub")"

rm -rf "$tmp"
[ "$fails" -eq 0 ] && echo "PASS" || { echo "$fails failed"; exit 1; }
