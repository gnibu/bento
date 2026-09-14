#!/usr/bin/env bash
# Reject candidate records whose text looks like it carries a credential.
#
#   secret-scan.sh < records.jsonl > safe.jsonl     rejected lines -> stderr
#
# Why reject and not redact: `evidence` is published verbatim into a tracker
# issue AND a GitHub PR body — two irreversible external writes — and the only
# other defence is a sentence in a prompt asking a model not to leak. Partial
# redaction is a bypass surface; dropping the record costs nothing, because a
# genuinely recurring learning will be re-emitted from a cleaner session.
#
# Fail closed: anything that matches is dropped whole, no attempt to salvage.
set -uo pipefail

# Deliberately broad. A false positive costs one dropped candidate; a false
# negative publishes a live credential to GitHub.
PATTERNS='(sk|rk|pk)-[A-Za-z0-9_-]{16,}
gh[pousr]_[A-Za-z0-9]{20,}
eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}
AKIA[0-9A-Z]{16}
xox[baprs]-[A-Za-z0-9-]{10,}
-----BEGIN [A-Z ]*PRIVATE KEY
service_role
(postgres|postgresql|mongodb(\+srv)?|redis|amqp)://[^:[:space:]]+:[^@[:space:]]+@
(password|passwd|secret|api[_-]?key|access[_-]?token|bearer)["'"'"'`]?[[:space:]]*[:=][[:space:]]*["'"'"'`]?[A-Za-z0-9/+_.-]{16,}
[A-Za-z][A-Za-z0-9_]{6,}=[A-Za-z0-9/+_-]{32,}'

kept=0; dropped=0
while IFS= read -r line; do
  [ -n "$line" ] || continue
  # Scan the human-readable fields only: keys and sinks are already schema-bound.
  text="$(jq -r '[.summary?, .evidence?, .proposal?] | map(select(type=="string")) | join(" ")' <<<"$line" 2>/dev/null)"
  if printf '%s' "$text" | grep -qiE "$(printf '%s' "$PATTERNS" | paste -sd'|' -)"; then
    dropped=$((dropped + 1))
    printf 'secret-scan: dropped %s\n' "$(jq -r '.key // "?"' <<<"$line" 2>/dev/null)" >&2
    continue
  fi
  printf '%s\n' "$line"
  kept=$((kept + 1))
done
printf 'secret-scan: kept %d, dropped %d\n' "$kept" "$dropped" >&2
