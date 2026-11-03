#!/bin/bash
# Maintenance fixture with a tracker that records writes. Callers write tickets.json and commit.
source "$(dirname "${BASH_SOURCE[0]}")/maintenance.sh"
grep -v 'Ownership snapshot' AGENTS.md | sed 's/ Tracker: none\./ Tracker: .\/tracker./' > AGENTS.tmp
mv AGENTS.tmp AGENTS.md
cat >> AGENTS.md <<'MD'
- Tracker commands: ./tracker list | ./tracker create <title> | ./tracker reopen <id> | ./tracker comment <id> <text>
- Open PRs: none.
MD
cat > tracker <<'SH2'
#!/bin/bash
[ "$1" = list ] && exec cat tickets.json
echo "$*" >> tracker-writes.log
echo "ok: $1"
SH2
chmod +x tracker
