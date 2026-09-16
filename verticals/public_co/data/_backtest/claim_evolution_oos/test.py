"""Out-of-sample test: does claim_evolution discriminate forward
returns on a NON-AIRO-prefiltered universe?

The 99 names in data/_local/*.scores.json come from thematic cohorts
(defense, hydrogen, ssbattery, lidar, dcpivot, quantum, cellgene,
nuclear, autos, fintech, etc.) — these were picked by industry
exposure, NOT by the AIRO-signature stock-for-services+ICFR-weakness
screen.

For each name, we ask:
  1. Did claim_evolution-mapped claims fire any severity?
  2. What's the forward return from each cohort's cutoff to today?

Test: do claim_evolution-flagged names underperform claim_evolution-
clean names? If yes → claim_evolution has independent alpha. If no
→ the AIRO-signature was carrying the work in fresh_universe.
"""
from __future__ import annotations

import json
import warnings
from pathlib import Path
from statistics import mean, median

warnings.filterwarnings("ignore")

import pandas as pd
import yfinance as yf

LOCAL = Path("verticals/public_co/data/_local")


def _ce_severity(d: dict, ticker: str) -> tuple[str, str | None]:
    """Return the highest-severity from claims adjudicated by the
    focal company's own subsequent filings (claim_evolution semantics).

    Detection: M_check / supports reference claim_evolution OR raw
    edgar_fts with the focal CIK (which IS the same semantic test —
    'is the focal company's own subsequent filings cadence consistent
    with the original claim?').

    Severity priority: SEVERE > RED > MODERATE > PASS > UNVERIFIABLE.
    """
    priority = {"SEVERE_UNDERDELIVERY": 4, "RED_FLAG_NEGATIVE": 3,
                "MODERATE_UNDERDELIVERY": 2, "PASS": 1, "UNVERIFIABLE": 0}
    tk_low = ticker.lower()
    going_concern_kw = ("going concern", "substantial doubt", "material weakness",
                         "restate", "restatement", "auditor change", "10-k/a",
                         "going silent", "no longer", "amend", "amended")
    best = "NONE_FOUND"
    interp = None
    for s in d.get("scores", []):
        supports = s.get("supports")
        if isinstance(supports, list):
            supports_str = " ".join(str(x) for x in supports if x)
        elif isinstance(supports, str):
            supports_str = supports
        else:
            supports_str = ""
        mcheck = str(s.get("M_check") or "")
        interp_s = str(s.get("interpretation") or "")
        full = (supports_str + " " + mcheck + " " + interp_s).lower()

        # claim_evolution semantics: any check that targets the focal
        # company's own subsequent filings cadence
        is_ce = (
            "claim_evolution" in full or
            f"cik={tk_low}" in full or
            f"cik=focal" in full or
            "own subsequent" in full or
            "subsequent filing" in full or
            "10-q" in full and any(k in full for k in going_concern_kw)
        )
        if not is_ce:
            continue
        sev = s.get("severity", "UNVERIFIABLE")
        if best == "NONE_FOUND" or priority.get(sev, 0) > priority.get(best, 0):
            best = sev
            interp = s.get("interpretation", "")
    return best, interp


def _forward_return(ticker: str, entry_date: str = "2025-05-15",
                     exit_date: str = "2026-05-15") -> float | None:
    """Adjusted-close return ticker over [entry, exit]."""
    try:
        h = yf.Ticker(ticker).history(start="2025-05-01", end="2026-05-20",
                                       auto_adjust=True)
        if h.empty: return None
        e = h.index.get_indexer([pd.Timestamp(entry_date, tz=h.index.tz)],
                                method="nearest")[0]
        x = h.index.get_indexer([pd.Timestamp(exit_date, tz=h.index.tz)],
                                method="nearest")[0]
        return float(h.iloc[x]["Close"]) / float(h.iloc[e]["Close"]) - 1
    except Exception:
        return None


def main():
    rows = []
    for p in sorted(LOCAL.glob("*.scores.json")):
        tk = p.name.split(".")[0].upper()
        d = json.loads(p.read_text())
        sev, interp = _ce_severity(d, tk)
        if sev == "NONE_FOUND":
            continue
        r = _forward_return(tk)
        rows.append({"ticker": tk, "ce_severity": sev,
                     "forward_return": r, "interp": interp})

    n = len(rows)
    print(f"Tickers with claim_evolution-mapped claims: {n}")

    # Bucket
    buckets: dict[str, list[float]] = {}
    bucket_names: dict[str, list[str]] = {}
    for r in rows:
        if r["forward_return"] is None:
            continue
        key = r["ce_severity"]
        buckets.setdefault(key, []).append(r["forward_return"])
        bucket_names.setdefault(key, []).append(r["ticker"])

    print()
    print(f"{'severity':30s} {'n':>3s} {'mean ret':>10s} {'median':>10s}  names")
    print("=" * 110)
    for sev in ("SEVERE_UNDERDELIVERY", "RED_FLAG_NEGATIVE",
                "MODERATE_UNDERDELIVERY", "PASS", "UNVERIFIABLE"):
        vals = buckets.get(sev, [])
        if not vals:
            print(f"  {sev:28s} {'0':>3s}    —          —      —")
            continue
        names = ",".join(bucket_names[sev][:8])
        if len(bucket_names[sev]) > 8:
            names += f",... (+{len(bucket_names[sev])-8})"
        print(f"  {sev:28s} {len(vals):>3d} {mean(vals)*100:>+9.1f}% "
              f"{median(vals)*100:>+9.1f}%  {names}")

    print()
    # Hit rate: how often does claim_evolution flag predict negative return?
    for sev in ("SEVERE_UNDERDELIVERY", "MODERATE_UNDERDELIVERY"):
        vals = buckets.get(sev, [])
        if not vals: continue
        n_neg = sum(1 for v in vals if v < 0)
        print(f"  {sev}: hit_rate (negative return) = {n_neg}/{len(vals)} = "
              f"{n_neg*100/len(vals):.0f}%")

    # Save
    Path("verticals/public_co/data/_backtest/claim_evolution_oos").mkdir(
        parents=True, exist_ok=True)
    out = {"n_tickers": n, "rows": rows, "buckets": {
        k: {"mean": mean(v), "median": median(v), "n": len(v),
            "names": bucket_names[k]} for k, v in buckets.items()
    }}
    Path("verticals/public_co/data/_backtest/claim_evolution_oos/results.json"
         ).write_text(json.dumps(out, indent=2, default=str))


if __name__ == "__main__":
    main()
