#!/usr/bin/env bash
# Self-check for throttled manual-update reminders. No LLM.
set -uo pipefail
cd "$(dirname "$0")"
tmp="$(mktemp -d)"
export BENTO_UPDATE_REMINDER_STATE="$tmp/update-reminder" BENTO_UPDATE_REMINDER_DAYS=0
trap 'rm -rf "$tmp"' EXIT
fails=0
check() { if [ "$2" = "$3" ]; then echo "ok   $1"; else echo "FAIL $1: expected [$2] got [$3]"; fails=$((fails+1)); fi; }
has()   { if grep -qF -- "$2" <<<"$3"; then echo "ok   $1"; else echo "FAIL $1: missing [$2]"; fails=$((fails+1)); fi; }

check "disabled reminder -> no output" "" "$(./session-start.sh </dev/null)"
check "disabled reminder does not create state" "no" "$([ -e "$BENTO_UPDATE_REMINDER_STATE" ] && echo yes || echo no)"

export BENTO_UPDATE_REMINDER_DAYS=30
out="$(./session-start.sh </dev/null)"
has "first session requests an automatic check" "check for a newer version automatically using read-only checks" "$out"
has "check precedes any user prompt" "Before mentioning updates to the user" "$out"
has "offer requires a confirmed newer version" "Only if you confirm a newer version is available" "$out"
has "offer includes version evidence" "report the installed and available revisions/versions" "$out"
has "inconclusive checks stay silent" "stay silent about updates" "$out"
has "installing remains manual" "Do not update the submodule or plugins automatically" "$out"
check "output is valid JSON with the right event" "SessionStart" \
      "$(printf '%s' "$out" | jq -r '.hookSpecificOutput.hookEventName')"
check "next session stays quiet" "" "$(./session-start.sh </dev/null)"

printf '%s' "$(($(date +%s) - 31 * 86400))" >"$BENTO_UPDATE_REMINDER_STATE"
has "expired interval requests a check again" "A periodic Bento update check is due" "$(./session-start.sh </dev/null)"
check "expired timestamp was refreshed" "" "$(./session-start.sh </dev/null)"

printf '%s' "$(($(date +%s) - 2 * 86400))" >"$BENTO_UPDATE_REMINDER_STATE"
check "custom interval respected before due" "" "$(./session-start.sh </dev/null)"
has "shorter custom interval becomes due" "A periodic Bento update check is due" \
    "$(BENTO_UPDATE_REMINDER_DAYS=1 ./session-start.sh </dev/null)"

printf 'corrupt' >"$BENTO_UPDATE_REMINDER_STATE"
has "corrupt timestamp recovers" "A periodic Bento update check is due" "$(./session-start.sh </dev/null)"
check "invalid configuration stays silent" "" "$(BENTO_UPDATE_REMINDER_DAYS=invalid ./session-start.sh </dev/null)"
check "unavailable state stays silent" "" \
      "$(BENTO_UPDATE_REMINDER_STATE="$tmp/update-reminder/state" ./session-start.sh </dev/null)"

# Competing starts share one throttle.
rm -f "$BENTO_UPDATE_REMINDER_STATE"
for i in 1 2 3 4 5; do ./session-start.sh </dev/null >"$tmp/out-$i" & done
wait
check "concurrent starts emit just one reminder" "1" "$(cat "$tmp"/out-* | jq -s 'length')"

[ "$fails" -eq 0 ] && echo "PASS" || { echo "$fails failed"; exit 1; }
