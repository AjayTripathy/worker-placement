#!/bin/bash
# Weekly CA-muni universe refresh (OS-level, durable) — read-only TWS scan, NEVER places orders.
# Re-pulls the insulated universe (incl 3% discounts) and MERGES into bonds_priced.json so the daily
# scanner sees new issuance. Degrades gracefully if TWS is down (keeps the existing universe).
cd /Users/ajay/exalted/signalos/verticals/muni_credit || exit 1
PY=/usr/bin/python3
LOG="outputs/cron_weekly_$(date +%Y%m%d).log"
{
  echo "=== WEEKLY UNIVERSE REFRESH $(date) ==="
  if $PY -u refresh_universe.py --out bonds_priced_refreshed.json 2>&1; then
    N=$($PY -c "import json;print(json.load(open('bonds_priced_refreshed.json'))['n'])" 2>/dev/null || echo 0)
    if [ "$N" -gt 400 ]; then
      cp bonds_priced.json bonds_priced.prev.json
      $PY - <<'EOF'
import json
o=json.load(open("bonds_priced.json")); n=json.load(open("bonds_priced_refreshed.json"))
ob={x["cusip"]:x for x in o["bonds"]}
add=0
for x in n["bonds"]:
    if x["cusip"] in ob:
        if x.get("px"): ob[x["cusip"]]["px"]=x["px"]; ob[x["cusip"]]["ytm"]=x.get("ytm")
    else: ob[x["cusip"]]=x; add+=1
json.dump({"source":"merged_weekly","n":len(ob),"bonds":list(ob.values())}, open("bonds_priced.json","w"))
print(f"merged: {len(ob)} bonds (+{add} new)")
EOF
      echo "universe refreshed+merged ($N from scan)"
    else echo "refresh wrote too few ($N) — keeping existing universe"; fi
  else echo "TWS down — universe NOT refreshed (daily scanner will use existing universe)"; fi
  echo "=== DONE $(date) ==="
} >> "$LOG" 2>&1
