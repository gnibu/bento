#!/usr/bin/env bash
# Self-check for the reflect-output parser in worker.sh.
#
# The fixture is real `claude -p` output: two well-formed records preceded by a
# line of prose the prompt asked it not to write. Plain `jq -c` aborts the whole
# stream on that first line and silently drops both records — which is exactly
# how the first end-to-end run logged "0 candidates" while the model had in fact
# found two real bugs. Guard the regression.
set -uo pipefail
cd "$(dirname "$0")"
fails=0
check() { if [ "$2" = "$3" ]; then echo "ok   $1"; else echo "FAIL $1: expected [$2] got [$3]"; fails=$((fails + 1)); fi; }

parse() { # stdin: raw model output -> stdout: clean records (mirrors worker.sh)
  jq -Rc --arg s "S" --arg c "/repo" --arg t "T" \
    'fromjson? // empty
     | select(type=="object")
     | select((.key|type)=="string" and (.key|test("^[a-z0-9]+(-[a-z0-9]+){0,9}$")))
     | select((.summary|type)=="string" and (.summary|length) > 0 and (.summary|length) <= 500)
     | .sink = (if (.sink|type)=="string" then (.sink|sub("CLAUDE\\.md$"; "AGENTS.md")) else "" end)
     | select(.sink|test("^(code|(skill|agents-md|docs):[A-Za-z0-9._/-]+)$"))
     | .evidence = (if (.evidence|type)=="string" then .evidence[0:1000] else "" end)
     | .proposal = (if (.proposal|type)=="string" then .proposal[0:1000] else "" end)
     | {key, sink, summary, evidence, proposal, session_id:$s, cwd:$c, ts:$t}'
}

ok_rec='{"key":"a-b","summary":"s","sink":"code","evidence":"e","proposal":"p"}'

got="$(parse < fixtures/reflect-output-with-preamble.txt)"
check "prose preamble does not eat the records" "2" "$(wc -l <<<"$got" | tr -d ' ')"
check "keys survive" "check-hook-mypy-vendored-venv-files zsh-glob-arg-expansion" \
      "$(jq -r .key <<<"$got" | sort | tr '\n' ' ' | sed 's/ $//')"
check "session_id stamped" "S" "$(jq -r .session_id <<<"$got" | sort -u)"

check "empty input yields nothing" "" "$(parse </dev/null)"
check "pure prose yields nothing"  "" "$(parse <<<'I found nothing worth keeping.')"
check "record without key dropped" "" "$(parse <<<'{"summary":"x"}')"
check "non-object json dropped"    "" "$(parse <<<'[1,2,3]')"

# A real simulation run aimed a learning at backend/CLAUDE.md — the symlink, not
# the source. Models pick whichever filename they happened to read.
check "CLAUDE.md sink rewritten to the source" "agents-md:backend/AGENTS.md" \
      "$(parse <<<'{"key":"k","summary":"s","sink":"agents-md:backend/CLAUDE.md"}' | jq -r .sink)"
check "AGENTS.md sink left alone" "agents-md:backend/AGENTS.md" \
      "$(parse <<<'{"key":"k","summary":"s","sink":"agents-md:backend/AGENTS.md"}' | jq -r .sink)"
check "unrelated sink untouched" "code" \
      "$(parse <<<'{"key":"k","summary":"s","sink":"code"}' | jq -r .sink)"

# Schema: a numeric key used to pass the old emptiness check, ripen, and then
# return no records from `ledger.sh show` because jq's == is type-strict —
# yielding an issue with an empty body.
check "numeric key rejected"      "" "$(parse <<<'{"key":123,"summary":"s","sink":"code"}')"
check "non-kebab key rejected"    "" "$(parse <<<'{"key":"Not Kebab","summary":"s","sink":"code"}')"
check "unknown sink rejected"     "" "$(parse <<<'{"key":"a-b","summary":"s","sink":"pastebin:evil"}')"
check "missing sink rejected"     "" "$(parse <<<'{"key":"a-b","summary":"s"}')"
check "non-string summary rejected" "" "$(parse <<<'{"key":"a-b","summary":["s"],"sink":"code"}')"
check "array evidence coerced, record kept" "" \
      "$(parse <<<'{"key":"a-b","summary":"s","sink":"code","evidence":["x"]}' | jq -r .evidence)"
check "valid record still passes"  "a-b" "$(parse <<<"$ok_rec" | jq -r .key)"
check "long evidence truncated"    "1000" \
      "$(parse <<<"$(jq -nc --arg e "$(printf 'x%.0s' $(seq 1 2000))" '{key:"a-b",summary:"s",sink:"code",evidence:$e}')" | jq -r '.evidence|length')"

[ "$fails" -eq 0 ] && echo "PASS" || { echo "$fails failed"; exit 1; }
