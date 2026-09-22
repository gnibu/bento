#!/usr/bin/env bash
# Durable handoff between Stop and the retrospective worker.
#
# Stop events enqueue the latest transcript path, then this script waits for
# quiescence and invokes worker.sh. Pending jobs live under BENTO_IMPROVE_STATE,
# not /tmp, so a killed waiter or reboot does not silently lose the analysis:
# SessionStart calls `recover` and re-arms every job without a live runner.
#
# Usage:
#   pending-session.sh enqueue <session-id> <transcript> <cwd>
#   pending-session.sh recover
#   pending-session.sh run <job-dir>          # internal detached entrypoint
set -uo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
self="$here/pending-session.sh"
state="${BENTO_IMPROVE_STATE:-$HOME/.claude/bento-improve}"
pending="$state/pending"
quiesce="${BENTO_IMPROVE_QUIESCE_SECS:-300}"
worker="${BENTO_IMPROVE_WORKER:-$here/worker.sh}"
mkdir -p "$pending" 2>/dev/null || exit 0

job_key() {
  printf '%s' "$1" | cksum | awk '{print $1 "-" $2}'
}

update_lock=""
owns_update_lock=0
acquire_update_lock() { # <key>
  local owner i=0
  update_lock="$pending/.update-$1"
  until mkdir "$update_lock" 2>/dev/null; do
    owner="$(cat "$update_lock/pid" 2>/dev/null || true)"
    if [ -z "$owner" ] \
       && [ -n "$(find "$update_lock" -maxdepth 0 -mmin +1 2>/dev/null)" ]; then
      rmdir "$update_lock" 2>/dev/null || true
      continue
    fi
    if [ -n "$owner" ] && ! kill -0 "$owner" 2>/dev/null; then
      rm -f "$update_lock/pid" 2>/dev/null || true
      rmdir "$update_lock" 2>/dev/null || true
      continue
    fi
    i=$((i + 1))
    [ "$i" -gt 100 ] && return 1
    sleep 0.1
  done
  printf '%s\n' "$$" >"$update_lock/pid"
  owns_update_lock=1
}

release_update_lock() {
  [ "$owns_update_lock" -eq 1 ] || return 0
  rm -f "$update_lock/pid" 2>/dev/null || true
  rmdir "$update_lock" 2>/dev/null || true
  update_lock=""
  owns_update_lock=0
}

launch() { # <job-dir>
  [ -d "$1" ] || return 0
  # Own process group + closed fds keeps the waiter alive when the agent exits.
  set -m 2>/dev/null || true
  { nohup "$self" run "$1" >/dev/null 2>&1 & } 2>/dev/null
}

enqueue() { # <session-id> <transcript> <cwd>
  local session="$1" transcript="$2" cwd="$3" key job gen
  key="$(job_key "$session")"
  job="$pending/$key"
  gen="$(date +%s).${RANDOM:-0}.$$"
  acquire_update_lock "$key" || return 0
  mkdir -p "$job" 2>/dev/null || { release_update_lock; return 0; }
  printf '%s\n' "$session" >"$job/session"
  printf '%s\n' "$transcript" >"$job/transcript"
  printf '%s\n' "$cwd" >"$job/cwd"
  # Auto-PR is explicit authorization attached to the Stop hook. Preserve that
  # choice across a reboot because SessionStart recovery does not carry it.
  printf '%s\n' "${BENTO_IMPROVE_AUTO_PR:-}" >"$job/auto-pr"
  # Written last: a runner that sees this generation can trust the metadata.
  printf '%s\n' "$gen" >"$job/gen"
  release_update_lock
  launch "$job"
}

acquire_waiter() { # <job-dir>
  local lock="$1/waiter" owner
  if ! mkdir "$lock" 2>/dev/null; then
    owner="$(cat "$lock/pid" 2>/dev/null || true)"
    # A live owner already covers this job. A dead owner is a crashed waiter,
    # which recovery is specifically responsible for replacing.
    if [ -z "$owner" ]; then
      [ -n "$(find "$lock" -maxdepth 0 -mmin +1 2>/dev/null)" ] || return 1
    elif kill -0 "$owner" 2>/dev/null; then
      return 1
    fi
    rm -f "$lock/pid" 2>/dev/null || true
    rmdir "$lock" 2>/dev/null || return 1
    mkdir "$lock" 2>/dev/null || return 1
  fi
  printf '%s\n' "$$" >"$lock/pid"
}

release_waiter() { # <job-dir>
  [ "$(cat "$1/waiter/pid" 2>/dev/null || true)" = "$$" ] || return 0
  rm -f "$1/waiter/pid" 2>/dev/null || true
  rmdir "$1/waiter" 2>/dev/null || true
}

delete_generation() { # <job-dir> <key> <generation>
  local job="$1" key="$2" generation="$3"
  acquire_update_lock "$key" || return 2
  if [ "$(cat "$job/gen" 2>/dev/null || true)" != "$generation" ]; then
    release_update_lock
    return 1
  fi
  rm -f "$job/session" "$job/transcript" "$job/cwd" "$job/auto-pr" "$job/gen" \
    2>/dev/null || true
  release_waiter "$job"
  rmdir "$job" 2>/dev/null || true
  release_update_lock
}

discard_invalid_generation() { # <job-dir> <key> <generation> <session>
  local job="$1" key="$2" generation="$3" session="$4" cleanup_status
  delete_generation "$job" "$key" "$generation"
  cleanup_status=$?
  if [ "$cleanup_status" -eq 0 ]; then
    printf '%s %s pending analysis discarded; transcript or working folder is gone\n' \
      "$(date -u +%FT%TZ)" "${session:-$key}" >>"$state/worker.log"
  fi
  return "$cleanup_status"
}

run_job() { # <job-dir>
  local job="$1" key mine current session transcript cwd auto_pr status cleanup_status
  [ -d "$job" ] || return 0
  acquire_waiter "$job" || return 0
  trap 'release_waiter "$job"; release_update_lock' EXIT
  trap 'exit 0' HUP INT TERM
  key="$(basename "$job")"

  while :; do
    mine="$(cat "$job/gen" 2>/dev/null || true)"
    [ -n "$mine" ] || return 0

    # Recovery commonly sees jobs whose workspace was archived while no waiter
    # was alive. Do not make those known-dead jobs wait through quiescence.
    session="$(cat "$job/session" 2>/dev/null || true)"
    transcript="$(cat "$job/transcript" 2>/dev/null || true)"
    cwd="$(cat "$job/cwd" 2>/dev/null || true)"
    if [ -z "$session" ] || [ ! -r "$transcript" ] || [ ! -d "$cwd" ]; then
      discard_invalid_generation "$job" "$key" "$mine" "$session"
      cleanup_status=$?
      [ "$cleanup_status" -eq 0 ] && return 0
      [ "$cleanup_status" -eq 1 ] && continue
      return 0
    fi

    sleep "$quiesce"
    current="$(cat "$job/gen" 2>/dev/null || true)"
    [ "$current" = "$mine" ] || continue

    session="$(cat "$job/session" 2>/dev/null || true)"
    transcript="$(cat "$job/transcript" 2>/dev/null || true)"
    cwd="$(cat "$job/cwd" 2>/dev/null || true)"
    auto_pr="$(cat "$job/auto-pr" 2>/dev/null || printf '%s' "${BENTO_IMPROVE_AUTO_PR:-}")"
    if [ -z "$session" ] || [ ! -r "$transcript" ] || [ ! -d "$cwd" ]; then
      discard_invalid_generation "$job" "$key" "$mine" "$session"
      cleanup_status=$?
      [ "$cleanup_status" -eq 0 ] && return 0
      [ "$cleanup_status" -eq 1 ] && continue
      return 0
    fi

    BENTO_IMPROVE_AUTO_PR="$auto_pr" \
      "$worker" --transcript "$transcript" --session "$session" --cwd "$cwd"
    status=$?
    if [ "$status" -ne 0 ]; then
      printf '%s %s pending analysis failed; SessionStart will retry\n' \
        "$(date -u +%FT%TZ)" "${session:-$key}" >>"$state/worker.log"
      return 0
    fi

    # A turn may arrive while reflection runs. Keep this runner and debounce the
    # new generation instead of spawning an overlapping analysis.
    [ "$(cat "$job/gen" 2>/dev/null || true)" = "$mine" ] || continue

    # Serialize completion against a simultaneous Stop enqueue. A newer
    # generation keeps the job and this runner loops to debounce it.
    delete_generation "$job" "$key" "$mine"
    cleanup_status=$?
    [ "$cleanup_status" -eq 0 ] && return 0
    [ "$cleanup_status" -eq 2 ] && return 0
  done
}

recover() {
  local job
  for job in "$pending"/*; do
    [ -d "$job" ] || continue
    [ -r "$job/gen" ] && [ -r "$job/session" ] && [ -r "$job/transcript" ] || continue
    launch "$job"
  done
}

case "${1:-}" in
  enqueue) [ "$#" -eq 4 ] || exit 0; enqueue "$2" "$3" "$4" ;;
  recover) recover ;;
  run)     [ "$#" -eq 2 ] || exit 0; run_job "$2" ;;
  *)       echo "usage: pending-session.sh enqueue <session> <transcript> <cwd> | recover" >&2; exit 2 ;;
esac
