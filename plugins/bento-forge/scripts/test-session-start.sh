#!/usr/bin/env bash
# Self-check for learning prompts and throttled manual-update reminders. No LLM.
set -uo pipefail
cd "$(dirname "$0")"
tmp="$(mktemp -d)"
export BENTO_IMPROVE_LEDGER="$tmp/ledger.jsonl" BENTO_IMPROVE_THRESHOLD=2
export BENTO_UPDATE_REMINDER_STATE="$tmp/update-reminder" BENTO_UPDATE_REMINDER_DAYS=0
trap 'rm -rf "$tmp"' EXIT
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

# Reminders work without learnings and cannot mutate a checkout: the only state
# they need is the shared local timestamp. All state in this test is isolated.
export BENTO_IMPROVE_LEDGER="$tmp/empty-ledger.jsonl"
check "disabled reminder does not create state" "no" "$([ -e "$BENTO_UPDATE_REMINDER_STATE" ] && echo yes || echo no)"
export BENTO_UPDATE_REMINDER_DAYS=30
out="$(./session-start.sh </dev/null)"
has "first session requests an automatic check" "check for a newer version automatically using read-only checks" "$out"
has "check precedes any user prompt" "Before mentioning updates to the user" "$out"
has "offer requires a confirmed newer version" "Only if you confirm a newer version is available" "$out"
has "offer includes version evidence" "report the installed and available revisions/versions" "$out"
has "inconclusive checks stay silent" "stay silent about updates" "$out"
has "installing remains manual" "Do not update the submodule or plugins automatically" "$out"
check "reminder-only output is valid JSON" "SessionStart" \
      "$(printf '%s' "$out" | jq -r '.hookSpecificOutput.hookEventName')"
check "next session stays quiet" "" "$(./session-start.sh </dev/null)"

printf '%s' "$(($(date +%s) - 31 * 86400))" >"$BENTO_UPDATE_REMINDER_STATE"
out="$(./session-start.sh </dev/null)"
has "expired interval requests a check again" "A periodic Bento update check is due" "$out"
check "expired timestamp was refreshed" "" "$(./session-start.sh </dev/null)"

printf '%s' "$(($(date +%s) - 2 * 86400))" >"$BENTO_UPDATE_REMINDER_STATE"
check "custom interval respected before due" "" "$(./session-start.sh </dev/null)"
has "shorter custom interval becomes due" "A periodic Bento update check is due" \
    "$(BENTO_UPDATE_REMINDER_DAYS=1 ./session-start.sh </dev/null)"

printf 'corrupt' >"$BENTO_UPDATE_REMINDER_STATE"
export BENTO_IMPROVE_LEDGER="$tmp/ledger.jsonl"
out="$(./session-start.sh </dev/null)"
has "corrupt timestamp recovers" "A periodic Bento update check is due" "$out"
has "reminder preserves learning prompt" "2 bento learning" "$out"
check "combined output is valid JSON" "SessionStart" \
      "$(printf '%s' "$out" | jq -r '.hookSpecificOutput.hookEventName')"
has "invalid configuration preserves learning prompt" "2 bento learning" \
    "$(BENTO_UPDATE_REMINDER_DAYS=invalid ./session-start.sh </dev/null)"
has "unavailable state preserves learning prompt" "2 bento learning" \
    "$(BENTO_UPDATE_REMINDER_STATE="$tmp/ledger.jsonl/state" ./session-start.sh </dev/null)"

# Exercise a real worker invocation, replacing only Claude with a child that
# fires SessionStart. No model, network, personal state, or promotion is used.
mkdir -p "$tmp/bin" "$tmp/repo/.bento"
git init -q "$tmp/repo"
cat >"$tmp/transcript.jsonl" <<'EOF'
{"type":"user","message":{"content":"Implement the change"}}
{"type":"user","message":{"content":"That failed"}}
{"type":"user","message":{"content":"Fix the failure"}}
{"type":"user","message":{"content":[{"type":"tool_result","is_error":true,"content":"test failed"}]}}
EOF
cat >"$tmp/bin/claude" <<'EOF'
#!/usr/bin/env bash
cat >/dev/null
bash "$BENTO_TEST_SCRIPTS/session-start.sh" </dev/null >"$BENTO_TEST_WORKER_HOOK"
EOF
chmod +x "$tmp/bin/claude"
export BENTO_TEST_SCRIPTS="$PWD" BENTO_TEST_WORKER_HOOK="$tmp/worker-hook.json"
run_worker() {
  PATH="$tmp/bin:$PATH" BENTO_IMPROVE_STATE="$tmp/worker-state" \
    BENTO_IMPROVE_AUTO_PR='' BENTO_IMPROVE_REPO_MARKER='.bento' \
    bash ./worker.sh --transcript "$tmp/transcript.jsonl" --session test-worker --cwd "$tmp/repo"
}
rm -f "$BENTO_UPDATE_REMINDER_STATE"
run_worker
check "worker does not create reminder state" "no" "$([ -e "$BENTO_UPDATE_REMINDER_STATE" ] && echo yes || echo no)"
has "worker child still receives learning prompt" "2 bento learning" "$(cat "$BENTO_TEST_WORKER_HOOK")"
check "worker child receives no update-check instructions" "false" \
      "$(jq '.hookSpecificOutput.additionalContext | contains("A periodic Bento update check is due")' "$BENTO_TEST_WORKER_HOOK")"
has "normal session after worker still receives due check" "A periodic Bento update check is due" \
    "$(./session-start.sh </dev/null)"

expired="$(($(date +%s) - 31 * 86400))"
printf '%s' "$expired" >"$BENTO_UPDATE_REMINDER_STATE"
run_worker
check "worker preserves expired timestamp" "$expired" "$(cat "$BENTO_UPDATE_REMINDER_STATE")"
has "expired reminder remains due after worker" "A periodic Bento update check is due" \
    "$(./session-start.sh </dev/null)"

# Competing starts share one throttle.
export BENTO_IMPROVE_LEDGER="$tmp/empty-ledger.jsonl"
rm -f "$BENTO_UPDATE_REMINDER_STATE"
for i in 1 2 3 4 5; do ./session-start.sh </dev/null >"$tmp/out-$i" & done
wait
check "concurrent starts emit just one reminder" "1" \
      "$(cat "$tmp"/out-* | jq -s 'length')"

[ "$fails" -eq 0 ] && echo "PASS" || { echo "$fails failed"; exit 1; }
