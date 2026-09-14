#!/usr/bin/env bash
# Candidate ledger for the automated session retrospective (bento-improve autorun).
#
#   ~/.claude/bento-improve/ledger.jsonl   (override: $BENTO_IMPROVE_LEDGER)
#
# Why local and not in the repo: the transcripts this is derived from live only
# on this machine, so recurrence can only ever be counted per-operator. A
# committed ledger would also merge-conflict on every session — several detached
# workers append concurrently. The ledger is scratch state on the way to a PR;
# the PR is the shared artifact, so only the PR goes to the team.
#
# Append-only JSONL under a mkdir lock: concurrent detached workers can interleave
# safely. mkdir and not flock(1) because macOS does not ship flock, and pulling in
# util-linux for one advisory lock is not worth it.
#
# Dedup is by `key`, a stable kebab-case slug the reflecting model emits. The
# model is handed the existing keys and told to reuse an exact match — that is
# cheaper and better than string similarity, and it needs no new dependency.
# A key's weight is its number of DISTINCT session_ids: one session that trips
# over the same thing five times is still one observation.
#
# Records:
#   {"key","session_id","ts","cwd","sink","summary","evidence"}   candidate
#   {"key","ts","promoted":true}                                  promotion mark
#
# Usage: ledger.sh keys | add <<<json | pending | ripe [N] | show <key> | promote <key>
set -uo pipefail

LEDGER="${BENTO_IMPROVE_LEDGER:-$HOME/.claude/bento-improve/ledger.jsonl}"
THRESHOLD="${BENTO_IMPROVE_THRESHOLD:-3}"
mkdir -p "$(dirname "$LEDGER")"
[ -e "$LEDGER" ] || : >"$LEDGER"

# ponytail: mkdir lock, ~10s worst-case wait. A lock dir older than 60s is a
# crashed worker, not contention, so break it.
with_lock() {
  local lock="$LEDGER.lock" i=0
  until mkdir "$lock" 2>/dev/null; do
    if [ -d "$lock" ] && [ -z "$(find "$lock" -maxdepth 0 -mmin -1 2>/dev/null)" ]; then
      rmdir "$lock" 2>/dev/null && continue
    fi
    i=$((i + 1)); [ "$i" -gt 100 ] && { echo "ledger.sh: lock timeout" >&2; return 1; }
    sleep 0.1
  done
  trap 'rmdir "$lock" 2>/dev/null' RETURN
  "$@"
}

append() { cat >>"$LEDGER"; }

promoted_keys() { jq -r 'select(.promoted==true) | .key' "$LEDGER" 2>/dev/null | sort -u; }

# key -> distinct session count, excluding already-promoted keys
counts() {
  local promoted; promoted=$(promoted_keys)
  jq -r 'select(.promoted != true and (.key//"") != "" and (.session_id//"") != "")
         | [.key, .session_id] | @tsv' "$LEDGER" 2>/dev/null \
    | sort -u \
    | cut -f1 | uniq -c \
    | while read -r n k; do
        grep -qxF "$k" <<<"$promoted" || printf '%s\t%s\n' "$n" "$k"
      done \
    | sort -rn
}

case "${1:-pending}" in
  keys)    counts | cut -f2 ;;
  add)     with_lock append ;;
  pending) counts ;;
  ripe)    counts | awk -v t="${2:-$THRESHOLD}" '$1 >= t {print $2}' ;;
  show)    jq -c --arg k "${2:?show <key>}" 'select(.key==$k)' "$LEDGER" ;;
  promote) printf '{"key":"%s","ts":"%s","promoted":true}\n' \
             "${2:?promote <key>}" "$(date -u +%FT%TZ)" | with_lock append ;;
  path)    echo "$LEDGER" ;;
  *)       echo "usage: ledger.sh keys|add|pending|ripe [N]|show <key>|promote <key>|path" >&2; exit 2 ;;
esac
