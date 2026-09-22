#!/usr/bin/env bash
# Self-check for the durable Stop -> worker handoff and SessionStart recovery.
set -uo pipefail
cd "$(dirname "$0")"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
export BENTO_IMPROVE_STATE="$tmp/state"
export BENTO_IMPROVE_QUIESCE_SECS=0
export BENTO_UPDATE_REMINDER_DAYS=0
fails=0
check() { if [ "$2" = "$3" ]; then echo "ok   $1"; else echo "FAIL $1: expected [$2] got [$3]"; fails=$((fails+1)); fi; }

transcript="$tmp/transcript.jsonl"
printf '%s\n' '{"type":"user","message":{"content":"one"}}' >"$transcript"

stub="$tmp/stub-worker.sh"
cat >"$stub" <<STUB
#!/usr/bin/env bash
session=""
while [ \$# -gt 0 ]; do case "\$1" in
  --session) session="\$2"; shift 2 ;;
  *) shift ;;
esac; done
printf '%s\n' "\$session" >>"$tmp/spawned"
printf '%s\n' "\${BENTO_IMPROVE_AUTO_PR:-}" >>"$tmp/auto-pr"
STUB
chmod +x "$stub"

await_count() { # <expected>
  local i=0 actual=0
  while [ "$i" -lt 60 ]; do
    actual="$([ -e "$tmp/spawned" ] && wc -l <"$tmp/spawned" | tr -d ' ' || echo 0)"
    [ "$actual" -ge "$1" ] && break
    sleep 0.1
    i=$((i + 1))
  done
  printf '%s\n' "$actual"
}

await_pending_count() { # <expected>
  local i=0 actual=0
  while [ "$i" -lt 60 ]; do
    actual="$(find "$BENTO_IMPROVE_STATE/pending" -mindepth 1 -maxdepth 1 -type d ! -name '.update-*' | wc -l | tr -d ' ')"
    [ "$actual" -eq "$1" ] && break
    sleep 0.1
    i=$((i + 1))
  done
  printf '%s\n' "$actual"
}

# A missing worker stands in for a waiter/process lost after Stop. The job must
# remain on disk rather than being acknowledged and lost.
export BENTO_IMPROVE_WORKER="$tmp/missing-worker"
export BENTO_IMPROVE_AUTO_PR=1
./pending-session.sh enqueue recover-me "$transcript" "$PWD"
i=0
while find "$BENTO_IMPROVE_STATE/pending" -type d -name waiter | grep -q . && [ "$i" -lt 60 ]; do
  sleep 0.1
  i=$((i + 1))
done
pending_jobs="$(find "$BENTO_IMPROVE_STATE/pending" -mindepth 1 -maxdepth 1 -type d ! -name '.update-*' | wc -l | tr -d ' ')"
check "failed handoff stays pending" "1" "$pending_jobs"

# Model the narrow crash window between creating the waiter lock and recording
# its PID. Once stale, this ownerless lock must not block recovery forever.
job="$(find "$BENTO_IMPROVE_STATE/pending" -mindepth 1 -maxdepth 1 -type d ! -name '.update-*' -print -quit)"
mkdir "$job/waiter"
touch -t 200001010000 "$job/waiter"

# SessionStart calls recover. Repeated starts may race, but the atomic waiter
# guard must deliver the persisted session exactly once.
export BENTO_IMPROVE_WORKER="$stub"
unset BENTO_IMPROVE_AUTO_PR
for _ in 1 2 3; do ./session-start.sh </dev/null >/dev/null; done
check "SessionStart recovers the pending analysis" "1" "$(await_count 1)"
check "recovery preserves explicit auto-PR authorization" "1" "$(cat "$tmp/auto-pr")"
sleep 0.3
check "concurrent recovery invokes the worker once" "1" "$(wc -l <"$tmp/spawned" | tr -d ' ')"
pending_jobs="$(find "$BENTO_IMPROVE_STATE/pending" -mindepth 1 -maxdepth 1 -type d ! -name '.update-*' | wc -l | tr -d ' ')"
check "successful recovery clears the pending job" "0" "$pending_jobs"

# A transcript or workspace that has permanently disappeared cannot succeed on
# retry. Such jobs must be acknowledged immediately instead of waiting through
# quiescence and being re-armed forever.
export BENTO_IMPROVE_QUIESCE_SECS=30
./pending-session.sh enqueue missing-transcript "$tmp/gone.jsonl" "$PWD"
gone_cwd="$tmp/gone-cwd"
./pending-session.sh enqueue missing-cwd "$transcript" "$gone_cwd"
check "permanently invalid jobs are deleted" "0" "$(await_pending_count 0)"
export BENTO_IMPROVE_QUIESCE_SECS=0

# TERM must stop the runner, not merely drop its lock and continue into the
# worker. A later recovery may then safely take responsibility for the job.
signal_job="$BENTO_IMPROVE_STATE/pending/signal-job"
mkdir -p "$signal_job"
printf '%s\n' signal-stop >"$signal_job/session"
printf '%s\n' "$transcript" >"$signal_job/transcript"
printf '%s\n' "$PWD" >"$signal_job/cwd"
printf '%s\n' '' >"$signal_job/auto-pr"
printf '%s\n' signal-generation >"$signal_job/gen"
BENTO_IMPROVE_QUIESCE_SECS=1 ./pending-session.sh run "$signal_job" &
runner=$!
i=0
while [ ! -r "$signal_job/waiter/pid" ] && [ "$i" -lt 60 ]; do
  sleep 0.1
  i=$((i + 1))
done
kill -TERM "$runner"
wait "$runner" 2>/dev/null || true
check "terminated runner does not invoke worker" "0" "$(grep -c '^signal-stop$' "$tmp/spawned" || true)"
check "terminated runner releases waiter lock" "no" "$([ -d "$signal_job/waiter" ] && echo yes || echo no)"

[ "$fails" -eq 0 ] && echo "PASS" || { echo "$fails failed"; exit 1; }
