#!/usr/bin/env bash
# Self-check for secret-scan.sh. Fail-closed: every credential shape must drop.
set -uo pipefail
cd "$(dirname "$0")"
fails=0
rec() { jq -nc --arg e "$1" '{key:"k",sink:"code",summary:"s",evidence:$e,proposal:"p"}'; }
drops() { [ -z "$(rec "$1" | ./secret-scan.sh 2>/dev/null)" ]; }
keeps() { [ -n "$(rec "$1" | ./secret-scan.sh 2>/dev/null)" ]; }
must_drop() { if drops "$2"; then echo "ok   drops $1"; else echo "FAIL kept $1"; fails=$((fails+1)); fi; }
must_keep() { if keeps "$2"; then echo "ok   keeps $1"; else echo "FAIL dropped $1"; fails=$((fails+1)); fi; }

# Fixtures are assembled from fragments, never written literally: a test file
# containing real-shaped credentials trips gitleaks and detect-private-key in
# every repo that vendors it — this one blocked its own commit until it didn't.
j() { local IFS=; echo "$*"; }

must_drop "openai-style key"   "ERR: auth failed with $(j 'sk' '-proj-' 'AbCdEf0123456789XyZwVuTs')"
must_drop "github token"       "remote: bad credentials $(j 'gh' 'p_' 'AbCdEf0123456789AbCdEf0123456789')"
must_drop "jwt"                "Authorization: Bearer $(j 'ey' 'JhbGciOiJIUzI1NiJ9' '.' 'eyJyb2xlIjoiYW5vbiJ9')"
must_drop "aws key id"         "$(j 'AKI' 'AIOSFODNN7EXAMPLE') was rejected"
must_drop "slack token"        "$(j 'xox' 'b-' '123456789012-abcdefghijkl')"
must_drop "private key"        "$(j '-----BEGIN ' 'RSA ' 'PRIVATE ' 'KEY-----')"
must_drop "supabase role"      "used the $(j 'service' '_role') key by mistake"
must_drop "db url with pw"     "$(j 'postgres://' 'admin' ':' 'hunter2hunter2' '@db.example.co:5432/x')"
must_drop "assignment form"    "$(j 'IX_API' '_KEY = ' '"' 'abcdef0123456789abcdef' '"')"
must_drop "env line"           "$(j 'AZURE_OPENAI' '_KEY=' 'abcdefghijklmnopqrstuvwxyz012345')"

must_keep "ordinary error"     'ERR: (eval):1: no matches found: --include=*.py'
must_keep "mypy noise"         'HOOK: mypy failed: site-packages is in the MYPYPATH. Please remove it.'
must_keep "mentions the word"  'the api_key is loaded from Secret Manager, not the env'
must_keep "short hex"          'commit c844ec658 introduced the regression'

echo "--- multi-line stream keeps the clean ones ---"
n=$({ rec 'clean one'; rec "$(j 'sk' '-proj-' 'AbCdEf0123456789XyZwVuTs')"; rec 'clean two'; } | ./secret-scan.sh 2>/dev/null | wc -l | tr -d ' ')
if [ "$n" = "2" ]; then echo "ok   2 of 3 survive"; else echo "FAIL expected 2 got $n"; fails=$((fails+1)); fi

[ "$fails" -eq 0 ] && echo "PASS" || { echo "$fails failed"; exit 1; }
