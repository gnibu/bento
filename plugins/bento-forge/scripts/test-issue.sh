#!/usr/bin/env bash
# Self-check for the tracker issue fields the worker derives from ripe ledger keys.
# Renders only — never touches a tracker.
set -uo pipefail
cd "$(dirname "$0")"
tmp="$(mktemp -d)"
export BENTO_IMPROVE_STATE="$tmp" BENTO_IMPROVE_LEDGER="$tmp/ledger.jsonl" BENTO_IMPROVE_THRESHOLD=2
fails=0
check() { if grep -qF -- "$2" <<<"$3"; then echo "ok   $1"; else echo "FAIL $1: missing [$2]"; fails=$((fails + 1)); fi; }
rec() { jq -nc --arg k "$1" --arg s "$2" --arg m "$3" --arg e "$4" \
        '{key:$k,session_id:$s,summary:$m,sink:"code",evidence:$e,ts:"t"}' | ./ledger.sh add; }

out="$(./worker.sh --preview-issue)"
check "nothing ripe says so" "(nothing ripe at threshold 2)" "$out"

rec zsh-glob s1 "zsh expands unquoted --include=*.py before the command runs" "ERR: no matches found"
out="$(./worker.sh --preview-issue)"
check "one session is not yet ripe" "(nothing ripe at threshold 2)" "$out"

rec zsh-glob s2 "zsh expands unquoted --include=*.py before the command runs" "ERR: no matches found again"
out="$(./worker.sh --preview-issue)"
check "single ripe key titles from its summary" "TITLE: learn: zsh expands unquoted" "$out"
check "body states the recurrence bar"          "recurred in at least 2 independent sessions" "$out"
check "body groups by key"                      '## `zsh-glob`' "$out"
check "body cites each session"                 "session \`s1\`" "$out"
check "body cites the second session"           "session \`s2\`" "$out"
check "body points the reviewer at the PR"      "Review the PR, not this description" "$out"

rec venv-mypy s1 "check.sh has no .venv exclusion" "HOOK: mypy failed"
rec venv-mypy s3 "check.sh has no .venv exclusion" "HOOK: mypy failed"
out="$(./worker.sh --preview-issue)"
check "multiple ripe keys get a counted title" "TITLE: learn: Session retrospective: 2 recurring learnings" "$out"
check "both keys present"                      '## `venv-mypy`' "$out"

rm -rf "$tmp"
[ "$fails" -eq 0 ] && echo "PASS" || { echo "$fails failed"; exit 1; }
