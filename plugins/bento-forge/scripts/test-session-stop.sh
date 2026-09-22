#!/usr/bin/env bash
# Self-check for session-stop.sh. Because Stop fires at the end of EVERY turn,
# session-stop must NOT reflect per turn: it skips trivial sessions, and for a
# substantive one it debounces to quiescence and reflects ONCE, on the COMPLETE
# transcript — never the early slice present at the first stop, and never locked
# out of a later burst. The real quality gate is digest.sh's job; this test also
# pins the Codex transcript schema at that boundary.
# A stub worker (BENTO_IMPROVE_WORKER) stands in for the real reflect+bank.
set -uo pipefail
cd "$(dirname "$0")"
tmp="$(mktemp -d)"
# Durable pending state must be isolated from the operator's real ledger/queue.
export BENTO_IMPROVE_STATE="$tmp/state"
# Tiny quiescence window so the debounce resolves within the test.
export BENTO_IMPROVE_QUIESCE_SECS=1
fails=0
check() { if [ "$2" = "$3" ]; then echo "ok   $1"; else echo "FAIL $1: expected [$2] got [$3]"; fails=$((fails+1)); fi; }

# Stub worker: one "spawned" line per call plus the line count of the transcript
# it was handed, namespaced by session id so tests don't cross-contaminate.
stub="$tmp/stub-worker.sh"
cat >"$stub" <<STUB
#!/usr/bin/env bash
t=""; s=""
while [ \$# -gt 0 ]; do case "\$1" in
  --transcript) t="\$2"; shift 2 ;;
  --session)    s="\$2"; shift 2 ;;
  *) shift ;;
esac; done
echo spawned >>"$tmp/spawned.\$s"
wc -l <"\$t" 2>/dev/null | tr -d ' ' >>"$tmp/lines.\$s"
STUB
chmod +x "$stub"
export BENTO_IMPROVE_WORKER="$stub"

uturn() { printf '{"type":"user","isMeta":false,"message":{"content":"%s"}}\n' "$1"; }
tooluse() { printf '{"type":"assistant","message":{"content":[{"type":"tool_use","name":"Edit"}]}}\n'; }
toolerr() { printf '{"type":"user","message":{"content":[{"type":"tool_result","is_error":true,"content":"boom"}]}}\n'; }
codex_uturn() { printf '{"type":"response_item","payload":{"type":"message","role":"user","content":[{"type":"input_text","text":"%s"}]}}\n' "$1"; }
codex_assistant() { printf '{"type":"response_item","payload":{"type":"message","role":"assistant","content":[{"type":"output_text","text":"%s"}]}}\n' "$1"; }
codex_reasoning() { printf '{"type":"response_item","payload":{"type":"reasoning","summary":[{"type":"summary_text","text":"%s"}]}}\n' "$1"; }
codex_tooluse() { printf '{"type":"response_item","payload":{"type":"custom_tool_call","name":"exec"}}\n'; }
codex_toolerr() { printf '{"type":"response_item","payload":{"type":"custom_tool_call_output","output":[{"type":"input_text","text":"Script failed\\nboom"}]}}\n'; }
# Codex-injected context arrives as user-role messages; it is not an operator turn.
codex_injected() { printf '{"type":"response_item","payload":{"type":"message","role":"user","content":[{"type":"input_text","text":"# AGENTS.md instructions for /repo\\n\\n<INSTRUCTIONS>\\nrules\\n</INSTRUCTIONS>"},{"type":"input_text","text":"<environment_context>\\n<cwd>/repo</cwd>\\n</environment_context>"}]}}\n'
  printf '{"type":"response_item","payload":{"type":"message","role":"user","content":[{"type":"input_text","text":"<system_instruction>\\nctx\\n</system_instruction>"}]}}\n'; }
codex_wrapped_uturn() { printf '{"type":"response_item","payload":{"type":"message","role":"user","content":[{"type":"input_text","text":"<system_instruction>ctx</system_instruction>\\n%s"}]}}\n' "$1"; }
codex_command_err() { printf '{"type":"event_msg","payload":{"type":"item_completed","item":{"type":"CommandExecution","status":"failed","aggregated_output":"command failed"}}}\n'; }

fire() { echo "{\"session_id\":\"$1\",\"transcript_path\":\"$2\",\"cwd\":\"$PWD\"}" | ./session-stop.sh; }
awaited() { # <session> -> yes|no  (poll for the debounced spawn)
  local i=0
  while [ ! -e "$tmp/spawned.$1" ] && [ "$i" -lt 60 ]; do sleep 0.2; i=$((i+1)); done
  [ -e "$tmp/spawned.$1" ] && echo yes || echo no
}
count() { [ -e "$tmp/spawned.$1" ] && wc -l <"$tmp/spawned.$1" | tr -d ' ' || echo 0; }

# trivial: 1 turn, no tool use → never arms a waiter, so it never reflects
triv="$tmp/triv.jsonl"; uturn "hi" >"$triv"
fire triv-1 "$triv"; sleep 1.5
check "trivial session does not reflect" "0" "$(count triv-1)"

# missing transcript → nothing to arm on
fire miss-1 "$tmp/nope.jsonl"; sleep 1.5
check "missing transcript does not reflect" "0" "$(count miss-1)"

# substantive single stop → reflects once, after the quiescence window
sub="$tmp/sub.jsonl"; { uturn "a"; tooluse; } >"$sub"
fire sub-1 "$sub"
check "substantive session reflects" "yes" "$(awaited sub-1)"

# headline: Stop fires per turn, so a growing session must reflect ONCE, on the
# FULL transcript — not the 2-line slice present at the first stop.
grow="$tmp/grow.jsonl"; { uturn "a"; tooluse; } >"$grow"          # 2 lines at first stop
fire grow-1 "$grow"
{ uturn "a"; tooluse; uturn "b"; toolerr; uturn "c"; } >"$grow"   # grows to 5 lines
fire grow-1 "$grow"
check "growing session reflects" "yes" "$(awaited grow-1)"
check "reflects exactly once (debounced)" "1" "$(count grow-1)"
check "reflects on the full transcript, not the early slice" "5" "$(cat "$tmp/lines.grow-1")"

# not permanently locked (the original bug): a later burst re-arms and reflects again
prev="$(count grow-1)"
fire grow-1 "$grow"
i=0; while [ "$(count grow-1)" = "$prev" ] && [ "$i" -lt 60 ]; do sleep 0.2; i=$((i+1)); done
check "a later burst re-arms (not permanently locked)" "2" "$(count grow-1)"

# Codex writes response_item/event_msg records rather than Claude's
# user/assistant/tool_result schema. It must pass both the cheap Stop pre-check
# and digest's real signal gate.
codex_triv="$tmp/codex-triv.jsonl"; { codex_injected; codex_uturn "hi"; } >"$codex_triv"
fire codex-triv-1 "$codex_triv"; sleep 1.5
check "Codex injected context is not an operator turn" "0" "$(count codex-triv-1)"

codex="$tmp/codex.jsonl"
{ codex_injected; codex_wrapped_uturn "a"; codex_tooluse; codex_uturn "b"; codex_assistant "answer";
  codex_reasoning "reason"; codex_uturn "c"; codex_toolerr; codex_command_err; } >"$codex"
fire codex-1 "$codex"
check "Codex session reflects" "yes" "$(awaited codex-1)"
check "Codex session reflects exactly once" "1" "$(count codex-1)"

codex_digest="$(./digest.sh "$codex")"
check "Codex digest keeps user turns" "3" "$(printf '%s\n' "$codex_digest" | grep -c '^U: ')"
check "Codex digest keeps assistant text and reasoning" "2" "$(printf '%s\n' "$codex_digest" | grep -c '^A: ')"
check "Codex digest keeps both failure forms" "2" "$(printf '%s\n' "$codex_digest" | grep -c '^ERR: ')"

rm -rf "$tmp"
[ "$fails" -eq 0 ] && echo "PASS" || { echo "$fails failed"; exit 1; }
