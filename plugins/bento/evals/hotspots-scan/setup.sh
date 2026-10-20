#!/bin/bash
# A repo with one tangled, often-changed function (orders.price), calm modules, and an
# import cycle orders.py <-> customers.py that no single file shows.
source "$(dirname "$0")/../_fixtures/repo.sh"
cat > customers.py <<'PY'
from orders import open_orders


def tier(customer):
    return "gold" if len(open_orders(customer)) > 10 else "basic"
PY
cat > report.py <<'PY'
def summary(rows):
    return {"count": len(rows), "total": sum(r["total"] for r in rows)}
PY
write_orders() {
cat > orders.py <<PY
import customers


def open_orders(customer):
    return [o for o in customer["orders"] if not o["closed"]]


def price(order, customer, coupon, region, rush, gift):
    total = 0
    for line in order["lines"]:
        if line["qty"] > 0:
            if customer and customers.tier(customer) == "gold":
                if line["sku"].startswith("X"):
                    total += line["qty"] * line["unit"] * 0.8
                else:
                    if coupon and coupon["active"]:
                        total += line["qty"] * line["unit"] * (1 - coupon["pct"])
                    else:
                        total += line["qty"] * line["unit"] * 0.9
            else:
                if coupon and coupon["active"] and not line["sku"].startswith("X"):
                    total += line["qty"] * line["unit"] * (1 - coupon["pct"])
                else:
                    total += line["qty"] * line["unit"]
    if region == "EU":
        total *= 1.2
    elif region == "UK":
        total *= 1.2 if not gift else 1.0
    if rush:
        total += $1
    return round(total, 2)
PY
git add -A && git commit -q -m "$2"
}
write_orders 5 "feat: pricing"
write_orders 7 "fix: rush fee"
write_orders 9 "fix: rush fee again"
write_orders 12 "chore: rush fee for 2026"
# The eval sandbox has no network, so uv can't fetch lizard: give the repo a local env.
python3 -m venv .venv && .venv/bin/pip install -q lizard && echo .venv >> .git/info/exclude
