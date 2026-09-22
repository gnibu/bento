#!/usr/bin/env bash
# Reduce a Claude Code or Codex transcript to the part a retrospective can
# learn from.
#
# Usage: digest.sh <transcript.jsonl>
#   stdout : the digest (chronological)
#   exit 0 : session cleared the gate, digest emitted
#   exit 1 : session is below the gate — nothing worth reflecting on
#
# Why a digest and not the raw file: measured over 222 transcripts (7 days, all
# workspaces), the learnable content is 3.1% of the bytes — 7.9 MB of 253 MB.
# The other 97% is file contents, diffs, search results and tool parameters,
# none of which a retrospective needs. Feeding the raw file would cost ~30x for
# no extra signal.
#
# What counts as signal:
#   U     operator turns          — corrections and redirects are the strongest
#                                   signal in the Reflect step
#   A     assistant text+thinking — thinking blocks hold the "that failed
#                                   because…" reasoning the final text drops
#   ERR   is_error tool results   — friction, retries, wrong commands
#   HOOK  hook_blocking_error     — typecheck/lint/migration-check failures
#
# The gate (>=3 operator turns AND >=1 failure) selects 113 of 222 sessions.
# It is deliberately about *friction*, not effort: a long clean session taught
# nobody anything, a short one that failed twice did.
set -uo pipefail

f="${1:?usage: digest.sh <transcript.jsonl>}"
[ -r "$f" ] || { echo "digest.sh: cannot read $f" >&2; exit 1; }

# ---- gate (pure, cheap: two passes of jq over one file) ----------------------
gate() { # transcript -> 0 if worth reflecting on
  local turns errs
  # Codex injects AGENTS.md, environment and system context as user-role
  # messages; count only those with operator text left after stripping them.
  turns=$(jq -r '
    if .type=="user" and (.isMeta|not) and ((.message.content|type)=="string") then 1
    elif .type=="response_item" and .payload.type=="message" and .payload.role=="user"
      then ([.payload.content[]? | select(.type=="input_text") | .text] | join("\n")
      | gsub("(?s)<(system_instruction|environment_context|recommended_plugins|user_instructions)>.*?</\\1>"; "")
      | gsub("(?s)# AGENTS\\.md instructions for [^\\n]*\\s*<INSTRUCTIONS>.*?</INSTRUCTIONS>"; "")
      | select(test("\\S")) | 1)
    else empty end' "$1" 2>/dev/null | wc -l)
  errs=$(jq -r '
    if .type=="user" and ((.message.content|type)=="array")
      then (.message.content[] | select(.type=="tool_result" and .is_error==true) | 1)
    elif .type=="attachment" and (.attachment.type=="hook_blocking_error") then 1
    elif .type=="event_msg" and .payload.type=="item_completed"
      and .payload.item.status=="failed" then 1
    elif .type=="response_item" and .payload.type=="custom_tool_call_output"
      and (([.payload.output[]?.text] | join("\n"))
        | test("^(Script failed|Script error:)")) then 1
    else empty end' "$1" 2>/dev/null | wc -l)
  [ "$turns" -ge 3 ] && [ "$errs" -ge 1 ]
}

gate "$f" || exit 1

# ---- extraction --------------------------------------------------------------
# Harness-injected wrappers are stripped: they are identical in every session,
# so they carry zero per-session signal but dominate the first operator turn.
jq -r '
  def clean:
      gsub("(?s)<system_instruction>.*?</system_instruction>"; "")
    | gsub("(?s)<system-reminder>.*?</system-reminder>"; "")
    | gsub("(?s)<user-preferences>.*?</user-preferences>"; "")
    | gsub("(?s)<local-command-stdout>.*?</local-command-stdout>"; "")
    | gsub("(?s)<(environment_context|recommended_plugins|user_instructions)>.*?</\\1>"; "")
    | gsub("(?s)# AGENTS\\.md instructions for [^\\n]*\\s*<INSTRUCTIONS>.*?</INSTRUCTIONS>"; "")
    | gsub("^\\s+|\\s+$"; "");

  if .type=="user" and (.isMeta|not) and ((.message.content|type)=="string")
    then (.message.content | clean | select(length > 0) | "U: " + .[0:2000])
  elif .type=="response_item" and .payload.type=="message" and .payload.role=="user"
    then ([.payload.content[]? | select(.type=="input_text") | .text]
          | join("\n") | clean | select(length > 0) | "U: " + .[0:2000])
  elif .type=="user" and ((.message.content|type)=="array")
    then (.message.content[] | select(.type=="tool_result" and .is_error==true)
          | "ERR: " + (.content|tostring)[0:600])
  elif .type=="assistant"
    then (.message.content[]? | select(.type=="text" or .type=="thinking")
          | ((.text // .thinking) | clean | select(length > 0) | "A: " + .[0:1500]))
  elif .type=="response_item" and .payload.type=="message" and .payload.role=="assistant"
    then ([.payload.content[]? | select(.type=="output_text") | .text]
          | join("\n") | clean | select(length > 0) | "A: " + .[0:1500])
  elif .type=="response_item" and .payload.type=="reasoning"
    then (.payload.summary[]? | select(.type=="summary_text")
          | (.text | clean | select(length > 0) | "A: " + .[0:1500]))
  elif .type=="event_msg" and .payload.type=="item_completed"
    and .payload.item.status=="failed"
    then (.payload.item.aggregated_output // "") as $aggregated
      | (.payload.item.stderr // "") as $stderr
      | "ERR: " + ((if ($aggregated | length) > 0 then $aggregated
          elif ($stderr | length) > 0 then $stderr
          else (.payload.item | tostring) end) | tostring)[0:600]
  elif .type=="response_item" and .payload.type=="custom_tool_call_output"
    then ([.payload.output[]?.text] | join("\n")) as $output
      | select($output | test("^(Script failed|Script error:)"))
      | "ERR: " + $output[0:600]
  elif .type=="attachment" and (.attachment.type=="hook_blocking_error")
    then "HOOK: " + ((.attachment|tostring)[0:600])
  else empty end' "$f" 2>/dev/null
