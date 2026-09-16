"""liquidity_gate — EMMA trade-tape liquidity floor for muni baskets.

WHY. The IBKR scanner surfaces a bond because *one* dealer is showing an ask; that says nothing
about whether you can actually build a position in it or get out later. Munis have no consolidated
quote (no NBBO), so the only honest liquidity signal is the realized MSRB trade tape: how recently
and how often the bond trades, and whether it trades *two-sided* (both customer-buy `S` and
customer-sell `P`) — a one-way-only tape means you can buy it but may be stuck holding it.

This gate measures that per CUSIP and rejects names that can't be acquired/exited at a fair price.
It is the execution sibling of the credit/insulation screens: clean credit + tight channel exposure
is worthless if the block is a paper position. Wire it into any basket build AFTER the EMMA
credit-verify and BEFORE sizing.

Spread is reported (same-day S vs P, which controls for rate drift) but is NOT a floor criterion:
for a hold-to-maturity ladder the spread is paid once on the buy and the bond redeems at par, so
recency/frequency/two-sidedness — "can I transact at all" — are what gate inclusion.
"""
from __future__ import annotations
import re, json, datetime, statistics as st
from collections import defaultdict

try:
    import emma_scraper as E
except ImportError:  # allow `python -m` from repo root
    from verticals.muni_credit import emma_scraper as E

# Default floor. Tunable per-mandate; these are calibrated to the CA insulated-muni universe where
# a genuinely tradeable name prints ~monthly and shows at least one two-sided day per year.
FLOOR = {
    "max_days_since_trade": 90,   # must have traded in the last quarter
    "min_trades_365": 12,         # ~monthly or better
    "min_two_sided_days": 1,      # at least one day with BOTH a customer buy and a customer sell
}


def _d(x: str) -> datetime.date:
    return datetime.date(int(x[:4]), int(x[5:7]), int(x[8:10]))


def _fetch_trades(cusip: str, session) -> list[dict]:
    url = E.BASE + "/Security/Details/" + cusip
    t = session.get(url, headers={"Referer": E.BASE + "/"}, timeout=40).text
    if "yesButton" in t:
        session.post(E.BASE + "/Disclaimer.aspx",
                     data={"__VIEWSTATE": E._hidden("__VIEWSTATE", t),
                           "__VIEWSTATEGENERATOR": E._hidden("__VIEWSTATEGENERATOR", t),
                           "__EVENTVALIDATION": E._hidden("__EVENTVALIDATION", t),
                           "ctl00$mainContentArea$disclaimerContent$yesButton": "Accept"},
                     headers={"Content-Type": "application/x-www-form-urlencoded",
                              "Origin": E.BASE, "Referer": url}, timeout=40)
        t = session.get(url, headers={"Referer": E.BASE + "/"}, timeout=40).text
    m = re.search(r"var tradeData = (\{.*?\});", t, re.S)
    return json.loads(m.group(1)).get("data", []) if m else []


def tape_metrics(cusip: str, session=None, today: datetime.date | None = None) -> dict:
    """Realized-tape liquidity metrics for one CUSIP. TT: S=dealer->customer (you buy / offer),
    P=customer->dealer (you sell / bid), D=inter-dealer."""
    session = session or E._session()
    today = today or datetime.date.today()
    rows = _fetch_trades(cusip, session)
    if not rows:
        return {"cusip": cusip, "n365": 0, "n90": 0, "days_since_trade": None,
                "two_sided_days": 0, "med_block": None, "max_block": None,
                "px_spread": None, "y_spread_bps": None}
    for r in rows:
        r["_d"] = _d(r["TD"])
    last = max(r["_d"] for r in rows)
    yr = [r for r in rows if (today - r["_d"]).days <= 365]
    sizes = [r["TA"] for r in yr if r.get("TA")]
    byday = defaultdict(lambda: {"S": [], "P": []})
    for r in yr:
        if r["TT"] in ("S", "P") and r.get("PX") and r.get("YX") is not None:
            byday[r["_d"]][r["TT"]].append(r)
    px, yb = [], []
    for sp in byday.values():
        if sp["S"] and sp["P"]:
            px.append(st.mean(x["PX"] for x in sp["S"]) - st.mean(x["PX"] for x in sp["P"]))
            yb.append(st.mean(x["YX"] for x in sp["P"]) - st.mean(x["YX"] for x in sp["S"]))
    return {"cusip": cusip,
            "days_since_trade": (today - last).days,
            "n365": len(yr),
            "n90": sum(1 for r in rows if (today - r["_d"]).days <= 90),
            "two_sided_days": len(px),
            "med_block": st.median(sizes) if sizes else None,
            "max_block": max(sizes) if sizes else None,
            "px_spread": round(st.median(px), 3) if px else None,
            "y_spread_bps": round(st.median(yb) * 100, 0) if yb else None}


def passes(m: dict, floor: dict = FLOOR) -> tuple[bool, list[str]]:
    """Return (pass, reasons_for_failure)."""
    reasons = []
    dst = m.get("days_since_trade")
    if dst is None:
        return False, ["no_trades_on_record"]
    if dst > floor["max_days_since_trade"]:
        reasons.append(f"stale:{dst}d>{floor['max_days_since_trade']}")
    if m.get("n365", 0) < floor["min_trades_365"]:
        reasons.append(f"thin:{m.get('n365',0)}tr/yr<{floor['min_trades_365']}")
    if m.get("two_sided_days", 0) < floor["min_two_sided_days"]:
        reasons.append(f"one_sided:{m.get('two_sided_days',0)}two-sided-days")
    return (len(reasons) == 0), reasons


def gate_cusips(cusips: list[str], session=None, today=None, floor=FLOOR) -> dict:
    """Score a list of CUSIPs; return {cusip: {**metrics, pass, reasons}}."""
    import time
    session = session or E._session()
    out = {}
    for cu in cusips:
        try:
            m = tape_metrics(cu, session, today)
        except Exception as e:
            m = {"cusip": cu, "err": str(e)[:60]}
        ok, why = passes(m, floor) if "err" not in m else (False, ["fetch_error"])
        out[cu] = {**m, "pass": ok, "reasons": why}
        time.sleep(0.35)
    return out


if __name__ == "__main__":
    import sys
    today = datetime.date(2026, 6, 9)
    cusips = sys.argv[1:]
    res = gate_cusips(cusips, today=today)
    for cu, r in res.items():
        tag = "PASS" if r["pass"] else "FAIL"
        print(f"{cu} {tag:4} n365={r.get('n365')} dago={r.get('days_since_trade')} "
              f"2sd={r.get('two_sided_days')} {';'.join(r['reasons'])}")
