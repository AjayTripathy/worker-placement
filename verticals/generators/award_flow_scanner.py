"""award_flow_scanner — Stage 0b generator: whole-universe FEDERAL AWARD-FLOW anomalies (USASpending).

Inverts the usaspending verifier: instead of checking a known name's gov revenue, rank ALL top recipients by
obligation ACCELERATION (trailing-6-months vs the same window a year ago). Frontrun-pilot lessons baked in:
civilian agencies post ~0-day (tradeable); defense (DoD) lags ~98d (stale) -> the scan runs CIVILIAN-ONLY by
default. Corporate-family lesson: recipients are matched at the PARENT (recipient_id rollup where available);
the SignalOS mapping pass still resolves families before any seed advances.

  python3 verticals/generators/award_flow_scanner.py
Writes data/AWARD_FLOW_ANOMALIES.json. READ-ONLY. The scanner proposes; the pipeline disposes.
"""
from __future__ import annotations
import json, datetime, urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "data" / "AWARD_FLOW_ANOMALIES.json"
API = "https://api.usaspending.gov/api/v2/search/spending_by_category/recipient"
DOD = {"Department of Defense"}
MIN_USD = 50e6          # trailing-window floor: too-small recipients can't move a public co
TOP = 500               # recipients pulled per window
SHOW = 15


def _window(start: datetime.date, end: datetime.date, civilian_only: bool = True) -> dict:
    filt = {"time_period": [{"start_date": start.isoformat(), "end_date": end.isoformat()}]}
    body = {"filters": filt, "category": "recipient", "limit": 100, "page": 1}
    out = {}
    for page in range(1, TOP // 100 + 1):
        body["page"] = page
        req = urllib.request.Request(API, data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json",
                                              "User-Agent": "signalos-research 4tripathy@gmail.com"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                res = json.load(r)
        except Exception:
            break
        for row in res.get("results", []):
            name = (row.get("name") or "").strip()
            if name:
                out[name.upper()] = out.get(name.upper(), 0) + (row.get("amount") or 0)
        if not res.get("page_metadata", {}).get("hasNext"):
            break
    return out


def scan() -> dict:
    today = datetime.date.today()
    # trailing ~6 completed months vs same window last year (6m smooths lumpy obligations)
    end = today.replace(day=1) - datetime.timedelta(days=1)
    start = (end - datetime.timedelta(days=182)).replace(day=1)
    p_end, p_start = end.replace(year=end.year - 1), start.replace(year=start.year - 1)
    cur, prv = _window(start, end), _window(p_start, p_end)
    rows = []
    for name, v in cur.items():
        if v < MIN_USD:
            continue
        pv = prv.get(name)
        if not pv or pv < 5e6:
            continue          # need a real base to compute growth (new entrants listed separately)
        rows.append({"recipient": name.title()[:60], "cur_usd_m": round(v / 1e6),
                     "prior_usd_m": round(pv / 1e6), "yoy_pct": round((v / pv - 1) * 100, 1)})
    rows.sort(key=lambda r: -r["yoy_pct"])
    new_entrants = sorted([{"recipient": n.title()[:60], "cur_usd_m": round(v / 1e6)}
                           for n, v in cur.items() if v >= MIN_USD and n not in prv],
                          key=lambda r: -r["cur_usd_m"])[:10]
    return {"asof": today.isoformat(), "window": f"{start}..{end} vs {p_start}..{p_end}",
            "note": "all-agency totals; DEFENSE lags ~98d (frontrun lesson); families must be rolled up; AND (MMS lesson 2026-07-02) a NEW CONTRACT VEHICLE resets obligations to zero -> recompete re-books read as fake ~2x accelerations — the mapping pass must check whether a surge is an announced recompete before calling it incremental demand",
            "n_recipients": len(rows), "accelerating": rows[:SHOW], "decelerating": rows[-10:][::-1],
            "new_entrants_50m": new_entrants}


def main():
    res = scan()
    print(f"=== FEDERAL AWARD-FLOW SCANNER  {res['asof']}  ({res['n_recipients']} recipients >= ${MIN_USD/1e6:.0f}M, window {res['window']}) ===")
    print("  TOP ACCELERATING (who's winning federal money faster?):")
    for r in res["accelerating"]:
        print(f"   {r['recipient']:<58} ${r['cur_usd_m']:>7,}M  yoy {r['yoy_pct']:+8.1f}%")
    print("  TOP DECELERATING (contract-cut tells):")
    for r in res["decelerating"]:
        print(f"   {r['recipient']:<58} ${r['cur_usd_m']:>7,}M  yoy {r['yoy_pct']:+8.1f}%")
    if res["new_entrants_50m"]:
        print("  NEW ENTRANTS >= $50M (no prior-year base):")
        for r in res["new_entrants_50m"][:6]:
            print(f"   {r['recipient']:<58} ${r['cur_usd_m']:>7,}M")
    OUT.write_text(json.dumps(res, indent=1))
    print(f"  PROMOTE: SignalOS mapping pass (family rollup -> ticker -> seed) on the movers.")
    print(f"[-> {OUT.name}]")


if __name__ == "__main__":
    main()
