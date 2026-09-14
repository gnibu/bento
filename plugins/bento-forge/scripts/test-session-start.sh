#!/usr/bin/env bash
# Self-check for session-start.sh: emit a model-visible SessionStart prompt only
# when the ledger has ripened candidates. Read-only, no LLM.
set -uo pipefail
cd "$(dirname "$0")"
tmp="$(mktemp -d)"
export BENTO_IMPROVE_LEDGER="$tmp/ledger.jsonl" BENTO_IMPROVE_THRESHOLD=2
fails=0
check() { if [ "$2" = "$3" ]; then echo "ok   $1"; else echo "FAIL $1: expected [$2] got [$3]"; fails=$((fails+1)); fi; }
has()   { if grep -qF -- "$2" <<<"$3"; then echo "ok   $1"; else echo "FAIL $1: missing [$2]"; fails=$((fails+1)); fi; }
rec() { printf '{"key":"%s","session_id":"%s","ts":"t","sink":"code","summary":"x"}\n' "$1" "$2" | ./ledger.sh add; }

check "empty ledger -> no output" "" "$(./session-start.sh </dev/null)"

rec zsh-glob s1
check "one session (below threshold) -> no output" "" "$(./session-start.sh </dev/null)"

rec zsh-glob s2   # second distinct session -> ripe at threshold 2
out="$(./session-start.sh </dev/null)"
has "ripe -> emits SessionStart output"  '"hookEventName":"SessionStart"' "$out"
has "carries additionalContext"          "additionalContext" "$out"
has "counts the ripened learning"        "1 bento learning" "$out"
check "output is valid one-line JSON with the right event" "SessionStart" \
      "$(printf '%s' "$out" | jq -r '.hookSpecificOutput.hookEventName')"

rec venv-mypy s1
rec venv-mypy s3   # second key crosses the threshold
out="$(./session-start.sh </dev/null)"
has "two ripened learnings counted" "2 bento learning" "$out"

rm -rf "$tmp"
[ "$fails" -eq 0 ] && echo "PASS" || { echo "$fails failed"; exit 1; }
