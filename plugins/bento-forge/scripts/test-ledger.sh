#!/usr/bin/env bash
# Self-check for ledger.sh counting/promotion rules. Run: ./test-ledger.sh
set -uo pipefail
cd "$(dirname "$0")"
export BENTO_IMPROVE_LEDGER="$(mktemp -d)/ledger.jsonl"
fails=0
check() { # <label> <expected> <actual>
  if [ "$2" = "$3" ]; then echo "ok   $1"
  else echo "FAIL $1: expected [$2] got [$3]"; fails=$((fails + 1)); fi
}
rec() { printf '{"key":"%s","session_id":"%s","ts":"t","sink":"s","summary":"x"}\n' "$1" "$2" | ./ledger.sh add; }

rec zsh-splitting s1
rec zsh-splitting s1          # same session twice -> still one observation
rec zsh-splitting s2
rec other-thing   s1
check "distinct sessions counted, not records" "2 zsh-splitting" "$(./ledger.sh pending | awk '$2=="zsh-splitting"{print $1, $2}')"
check "second key tracked"                     "1 other-thing"   "$(./ledger.sh pending | awk '$2=="other-thing"{print $1, $2}')"
check "nothing ripe at threshold 3"            ""                "$(./ledger.sh ripe 3)"
check "ripe at threshold 2"                    "zsh-splitting"   "$(./ledger.sh ripe 2)"

rec zsh-splitting s3
check "ripe at threshold 3 after 3rd session"  "zsh-splitting"   "$(./ledger.sh ripe 3)"

./ledger.sh promote zsh-splitting
check "promoted key leaves pending"            ""                "$(./ledger.sh pending | awk '$2=="zsh-splitting"{print}')"
check "promoted key never ripens again"        ""                "$(./ledger.sh ripe 1 | grep -x zsh-splitting)"
check "unpromoted key survives"                "other-thing"     "$(./ledger.sh ripe 1)"
check "keys feed the prompt"                   "other-thing"     "$(./ledger.sh keys)"

rm -rf "$(dirname "$BENTO_IMPROVE_LEDGER")"
[ "$fails" -eq 0 ] && echo "PASS" || { echo "$fails failed"; exit 1; }
