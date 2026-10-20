#!/bin/bash
# The hotspots-scan repo merged to master, plus a second tangled function (report.summary) and an overlay that
# leaves orders.price alone: unattended mode must skip price and refactor summary.
source "$(dirname "$0")/../hotspots-scan/setup.sh"
cat > report.py <<'PY'
def summary(rows, by_region, include_closed, currency):
    out = {}
    for r in rows:
        if r["closed"] and not include_closed:
            continue
        if by_region:
            if r["region"] not in out:
                out[r["region"]] = 0
            if currency == "EUR":
                if r["currency"] == "USD":
                    out[r["region"]] += r["total"] * 0.9
                else:
                    out[r["region"]] += r["total"]
            else:
                if r["currency"] == "EUR":
                    out[r["region"]] += r["total"] / 0.9
                else:
                    out[r["region"]] += r["total"]
        else:
            out["all"] = out.get("all", 0) + r["total"]
    return out
PY
mkdir -p .agents/bento
cat > .agents/bento/bento-hotspots.md <<'MD'
# Shop overlay for bento-hotspots

## Leave
- orders.py: price: pricing rules mirror the contract table line by line; finance reviews it
MD
git add -A && git commit -q -m "feat: report by region"
# Unattended mode works from origin/master: land the code there, as a merged history would be.
git switch -q master && git merge -q --ff-only eng-42-greeting && git push -q origin master
