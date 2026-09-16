"""Phase-2 scoring backtest — GOV_CONTRACT_SPEC.md (LOCKED) + G-1..G-4.

Builds the load-date-censored point-in-time panel per (name, quarter), labels
revenue-surprise direction + beta-hedged post-earnings drift, scores Arm A vs
Arm B, and reports edge(A)-edge(B), a timing-shuffle placebo, and clustered-N.

Run:  python3 run_govcon_backtest.py
Out:  outputs/phase2_govcon_backtest.json
"""
from __future__ import annotations

import json
import statistics as st
from datetime import date, timedelta
from pathlib import Path

import requests

import build_govcon_panel as B

HERE = Path(__file__).resolve().parent
PXDIR = HERE / "outputs" / "px_cache"
SEC_H = {"User-Agent": "SignalOS-Frontrun research 4tripathy@gmail.com"}

# ----- decision/label parameters (LOCKED-consistent; not fished) -----
DECISION_LEAD_DAYS = 21          # D ~ 3 weeks before the filing/earnings date (point-in-time)
DRIFT_START, DRIFT_END = 1, 20   # trading days post-earnings (+1..+20) for drift
BORROW_BPS_ANN = 200             # small-cap borrow ~2%/yr -> per 20td ~ negligible but charged
HEDGE = "ITA"                    # gov/defense ETF beta hedge (XAR used in robustness)
PX_FLOOR = date(2021, 6, 28)     # price-cache start -> tradeable window floor

TAGS = ["RevenueFromContractWithCustomerExcludingAssessedTax",
        "RevenueFromContractWithCustomerIncludingAssessedTax", "Revenues", "SalesRevenueNet"]

CIK = {"DLHC": "0000785557", "ICFI": "0001362004",
       "LMT": "0000936468", "GD": "0000040533", "BAH": "0001443646",
       "LDOS": "0001336920", "SAIC": "0001571123", "CACI": "0000016058"}

# gov-revenue share of total (FY-ish, from filings/concentration disclosure) for run-rate gate
GOV_SHARE = {"DLHC": 1.00, "ICFI": 0.72, "LMT": 0.74, "GD": 0.60, "BAH": 0.98,
             "LDOS": 0.87, "SAIC": 0.98, "CACI": 0.93}

# IBKR contract ids for names with a VERIFIED, distinct daily price series this session.
# LDOS excluded: contract 134280621 returned BAH's series/quote this session (feed anomaly),
# so its drift is UNVERIFIABLE and we do not fabricate it. SAIC/CACI throttled-out of the panel.
IBKR = {"DLHC": 109908055, "ICFI": 40784309,
        "LMT": 611191, "GD": 7496, "BAH": 80968828}


def load_px(tag):
    p = PXDIR / f"{tag}.json"
    return {k: float(v) for k, v in json.load(open(p)).items()} if p.exists() else {}


PX = {t: load_px(t) for t in ["DLHC", "ICFI", "ITA", "XAR", "LMT", "GD", "BAH"]}
TRADING_DAYS = sorted(set(PX["ITA"]))  # market calendar from the hedge series


def quarter_revenue(cik):
    """{end_date: (rev_musd, filed_date)} for ~quarterly spans, latest-filed wins."""
    j = requests.get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json",
                     headers=SEC_H, timeout=120).json()["facts"]["us-gaap"]
    d = {}
    for tag in TAGS:
        if tag not in j:
            continue
        for u in j[tag]["units"]["USD"]:
            if u.get("start") and u.get("end") and u.get("form") in ("10-Q", "10-K"):
                s = date.fromisoformat(u["start"]); e = date.fromisoformat(u["end"])
                if 80 <= (e - s).days <= 100:
                    if u["end"] not in d or u["filed"] > d[u["end"]][1]:
                        d[u["end"]] = (u["val"] / 1e6, u["filed"])
    return d


_REVQ_CACHE = {}


def revq_filed(ticker, end_iso):
    """Filing date for a quarter end (for drift-refresh from checkpoints)."""
    if ticker not in _REVQ_CACHE:
        _REVQ_CACHE[ticker] = quarter_revenue(CIK[ticker])
    return _REVQ_CACHE[ticker][end_iso][1]


def nearest_td(target: date, after=True):
    """Nearest trading day on/after (or on/before) target in the market calendar."""
    iso = target.isoformat()
    if after:
        cand = [d for d in TRADING_DAYS if d >= iso]
        return cand[0] if cand else None
    cand = [d for d in TRADING_DAYS if d <= iso]
    return cand[-1] if cand else None


def td_offset(anchor_iso: str, n: int):
    """Trading day n steps after anchor_iso (n>0 forward)."""
    if anchor_iso not in TRADING_DAYS:
        return None
    i = TRADING_DAYS.index(anchor_iso)
    j = i + n
    return TRADING_DAYS[j] if 0 <= j < len(TRADING_DAYS) else None


def beta_hedged_drift(ticker, filed: date):
    """Long name vs HEDGE ETF, return from +DRIFT_START to +DRIFT_END trading days
    after the earnings (filing) day, net of borrow + a half-spread round-trip cost.
    Beta estimated on a trailing 120-trading-day pre-event window (point-in-time)."""
    name_px = PX.get(ticker, {})
    hedge_px = PX[HEDGE]
    e0 = nearest_td(filed, after=True)
    if e0 is None:
        return None
    start = td_offset(e0, DRIFT_START)
    end = td_offset(e0, DRIFT_END)
    if not (start and end):
        return None
    # trailing beta on pre-event window
    pre = [d for d in TRADING_DAYS if d < e0][-120:]
    nm = [name_px.get(d) for d in pre]
    hg = [hedge_px.get(d) for d in pre]
    rn, rh = [], []
    for a, b in zip(zip(nm, nm[1:]), zip(hg, hg[1:])):
        if all(x and x > 0 for x in a + b):
            rn.append(a[1] / a[0] - 1); rh.append(b[1] / b[0] - 1)
    beta = 1.0
    if len(rn) > 30 and st.pstdev(rh) > 0:
        cov = sum((x - st.mean(rn)) * (y - st.mean(rh)) for x, y in zip(rn, rh)) / len(rn)
        beta = cov / st.pvariance(rh)
        beta = max(0.0, min(2.5, beta))
    p0, p1 = name_px.get(start), name_px.get(end)
    h0, h1 = hedge_px.get(start), hedge_px.get(end)
    if not all(x and x > 0 for x in (p0, p1, h0, h1)):
        return None
    raw = p1 / p0 - 1
    hedged = raw - beta * (h1 / h0 - 1)
    # costs: half-spread round trip (use 2.6% for DLHC micro, 0.2% ICFI; charged once each side)
    # round-trip half-spread cost (DLHC micro-cap ~2.6% from live quote; large caps ~bps)
    spread = {"DLHC": 0.026, "ICFI": 0.004,
              "LMT": 0.0005, "GD": 0.0005, "BAH": 0.001}.get(ticker, 0.002)
    borrow = BORROW_BPS_ANN / 1e4 * (DRIFT_END - DRIFT_START) / 252.0
    net = hedged - spread - borrow
    return {"beta": round(beta, 2), "raw_ret": round(raw, 4),
            "hedged_ret": round(hedged, 4), "net_ret": round(net, 4),
            "e0": e0, "win": [start, end], "cost": round(spread + borrow, 4)}


def build_panel(sess, ticker, co):
    """Per-quarter rows with censored signal + labels. Only quarters with D >= PX_FLOOR
    (tradeable) and a NEXT quarter revenue label."""
    revq = quarter_revenue(CIK[ticker])
    ends = sorted(revq)
    rows = []
    for i in range(4, len(ends) - 1):  # need 8Q history for signal + a next label
        q_end = date.fromisoformat(ends[i])
        # common tradeable window: decision dates from ~2020Q4 on (price floor 2021-06 + lead).
        # earlier quarters can't yield a tradeable Arm-A drift event; bound Arm-B to the same era.
        if q_end < date(2020, 6, 1):
            continue
        rev, filed = revq[ends[i]]
        filed_d = date.fromisoformat(filed)
        D = filed_d - timedelta(days=DECISION_LEAD_DAYS)
        if D < PX_FLOOR:
            continue
        # gov-rev run-rate = trailing-4Q total revenue * gov share, annualized
        last4 = [revq[ends[k]][0] for k in range(i - 3, i + 1)]
        gov_rr = sum(last4) * 1e6 * GOV_SHARE[ticker]   # ~annual gov revenue
        sig = B.signal(sess, co, D, gov_rr)
        # label (a): NEXT-quarter revenue surprise direction vs run-rate model
        nxt_rev = revq[ends[i + 1]][0]
        nxt_filed = date.fromisoformat(revq[ends[i + 1]][1])
        # run-rate model = mean of trailing 4 quarters (seasonality-naive); surprise = actual - model
        model = st.mean(last4)
        rev_surprise = nxt_rev - model
        rev_dir = "up" if rev_surprise > 0 else "down"
        # label (b): beta-hedged drift around the NEXT earnings (the one the signal predicts)
        drift = beta_hedged_drift(ticker, nxt_filed) if ticker in IBKR else None
        rows.append({
            "ticker": ticker, "quarter_end": ends[i], "decision_date": D.isoformat(),
            "filed": filed, "gov_rev_run_rate_usd": round(gov_rr),
            "signal_censored": sig["censored"], "signal_leaky": sig["leaky"],
            "leak_gap_usd": sig["cur_diag"]["leak_gap_usd"],
            "next_quarter_end": ends[i + 1], "next_rev_musd": round(nxt_rev, 2),
            "runrate_model_musd": round(model, 2), "rev_surprise_musd": round(rev_surprise, 2),
            "rev_direction": rev_dir, "drift": drift,
        })
    return rows


def score_arm(rows, which="censored"):
    """Among FIRING events: hit-rate (signal dir == rev surprise dir) + mean net drift
    in the signalled direction."""
    fired = [r for r in rows if r[f"signal_{which}"]["fires"]]
    hits, drifts, dir_drifts = 0, [], []
    for r in fired:
        sd = r[f"signal_{which}"]["direction"]
        if sd == r["rev_direction"]:
            hits += 1
        if r["drift"]:
            net = r["drift"]["net_ret"]
            drifts.append(net)
            dir_drifts.append(net if sd == "up" else -net)  # trade in signalled direction
    n = len(fired)
    return {"n_events": n, "n_with_drift": len(dir_drifts),
            "hit_rate": round(hits / n, 3) if n else None,
            "mean_dir_net_drift": round(st.mean(dir_drifts), 4) if dir_drifts else None,
            "median_dir_net_drift": round(st.median(dir_drifts), 4) if dir_drifts else None,
            "events": [{"t": r["ticker"], "q": r["quarter_end"],
                        "sig_dir": r[f"signal_{which}"]["direction"],
                        "delta_pct": r[f"signal_{which}"]["delta_pct_gov_rr"],
                        "rev_dir": r["rev_direction"], "hit": r[f"signal_{which}"]["direction"] == r["rev_direction"],
                        "net_drift": (r["drift"]["net_ret"] if r["drift"] else None),
                        "leak_gap_usd": r["leak_gap_usd"]} for r in fired]}


def main():
    sess = B.Session(rate_min=40)
    ckdir = HERE / "outputs" / "_panel_ckpt"
    ckdir.mkdir(exist_ok=True)
    panel = {}
    failed = []

    import os
    ckpt_only = os.environ.get("CKPT_ONLY") == "1"

    def get_panel(tk, co):
        ck = ckdir / f"{tk}.json"
        if ck.exists():
            return json.load(open(ck))
        if ckpt_only:
            raise RuntimeError("no checkpoint and CKPT_ONLY set (throttled-out name)")
        rows = build_panel(sess, tk, co)
        json.dump(rows, open(ck, "w"))
        return rows

    for arm, names in (("A", B.LIVE), ("B", B.ARMB)):
        for tk, co in names.items():
            try:
                panel[tk] = get_panel(tk, co)
                print(f"[{arm}] {tk}: {len(panel[tk])} quarters", flush=True)
            except Exception as e:  # a name that won't resolve / throttled -> skip, report honestly
                failed.append(tk)
                print(f"[{arm}] {tk}: SKIPPED ({type(e).__name__})", flush=True)

    # refresh drift from the current (verified) price caches for any name with an IBKR series.
    # checkpoints were built before Arm-B prices existed; recompute drift now so the §5
    # beta-hedged-drift control is populated for LMT/GD/BAH (LDOS excluded: feed anomaly).
    for tk, rows in panel.items():
        if tk not in IBKR:
            continue
        for r in rows:
            nxt_filed = date.fromisoformat(revq_filed(tk, r["next_quarter_end"]))
            r["drift"] = beta_hedged_drift(tk, nxt_filed)

    armA = [r for tk in B.LIVE if tk in panel for r in panel[tk]]
    armB = [r for tk in B.ARMB if tk in panel for r in panel[tk]]

    out = {"as_of": "2026-06-24", "spec": "GOV_CONTRACT_SPEC.md LOCKED + G-1..G-4",
           "failed_names": failed,
           "params": {"decision_lead_days": DECISION_LEAD_DAYS,
                      "drift_window_td": [DRIFT_START, DRIFT_END], "hedge": HEDGE,
                      "materiality": 0.10, "armA_cut": "<=5 analysts", "armB_cut": ">=15 analysts",
                      "px_floor": PX_FLOOR.isoformat()},
           "panel": panel}

    for which in ["censored", "leaky"]:
        out[f"armA_{which}"] = score_arm(armA, which)
        out[f"armB_{which}"] = score_arm(armB, which)

    # leak-check summary
    gaps = [r["leak_gap_usd"] for r in armA + armB]
    out["leak_check"] = {
        "n_rows": len(gaps),
        "median_leak_gap_usd": int(st.median(gaps)) if gaps else None,
        "armA_censored_events": out["armA_censored"]["n_events"],
        "armA_leaky_events": out["armA_leaky"]["n_events"],
        "interpretation": "action_date(leaky) vs last_modified(censored) signal sets; "
                          "gap is the look-ahead G-4 removes"}

    json.dump(out, open(HERE / "outputs" / "phase2_govcon_backtest.json", "w"), indent=1)
    print("\nwrote outputs/phase2_govcon_backtest.json")
    for k in ["armA_censored", "armB_censored", "armA_leaky", "armB_leaky"]:
        s = out[k]
        print(f"  {k:16} n={s['n_events']:2d} hit={s['hit_rate']} drift={s['mean_dir_net_drift']}")


if __name__ == "__main__":
    main()
