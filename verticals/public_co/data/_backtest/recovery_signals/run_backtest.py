"""Recovery-signal backtest on Tier 3 universe.

Retroactively applies the 4 newly-built CIK-only recovery-signal m-sources
to the 58-name Tier 3 universe (cutoff 2024-05-15), then correlates the
resulting `recovery_signal_score` with known 12m and 24m forward returns.

If high-recovery-signal names systematically outperformed (especially at
24m), the new framework would have improved Tier 3's basket math.

M-sources used (4 of 5 — counterparty_reciprocity is skipped because
it requires per-name counterparty extraction, which we'd need a fresh
10-K parse for):
  • filing_timeliness
  • insider_buy_timing      (the heavy one — Form 4 XML fetches)
  • mw_lifecycle
  • lender_concession

OUTPUT
  recovery_backtest.json   — per-name signals + scores + actual returns
  recovery_backtest.md     — analysis writeup

Usage:
  python3 verticals/public_co/data/_backtest/recovery_signals/run_backtest.py
"""
import json
import sys
import time
import warnings
from pathlib import Path

warnings.filterwarnings('ignore')
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parents[4]))

from verticals.public_co.m_sources.filing_timeliness import query_filing_timeliness
from verticals.public_co.m_sources.insider_buy_timing import query_insider_buy_timing
from verticals.public_co.m_sources.mw_lifecycle import query_mw_lifecycle
from verticals.public_co.m_sources.lender_concession import query_lender_concession


CUTOFF = "2024-05-15"
TIER3_DIR = HERE.parents[1] / "_backtest" / "walk_forward_2024_05"


# --- signal → score mapping per the V3 prompt rules ---
# Score range: -3 (strongest negative) to +3 (strongest positive)

def score_filing_timeliness(r):
    s = r.get("signal", "")
    if s == "ON_TIME_STREAK" and r.get("on_time_streak_periods", 0) >= 8:
        return ("positive", 1)
    if s == "ON_TIME_STREAK":
        return ("neutral", 0)
    if s == "DRIFTING_TIMING":
        return ("negative", -1)
    if s == "RECURRING_AMENDMENTS":
        return ("negative", -1)
    if s == "RECENT_NT_FILING":
        return ("negative", -2)
    return ("neutral", 0)


def score_insider_buy_timing(r):
    s = r.get("signal", "")
    if s == "STRONG_POST_DISTRESS_BUY":
        return ("positive", 3)
    if s == "MODERATE_POST_DISTRESS_BUY":
        return ("positive", 2)
    if s == "QUIET_PERIOD_BUYS_ONLY":
        # Look at dollar amount
        dollars = r.get("timing_class_dollars", {}).get("QUIET_PERIOD_BUY", 0)
        if dollars >= 500_000:
            return ("positive", 1)
        return ("neutral", 0)
    if s == "POTENTIAL_INSIDER_TRADING":
        return ("negative", -3)
    if s == "NO_INSIDER_BUYS":
        return ("negative", -1)
    return ("neutral", 0)


def score_mw_lifecycle(r):
    s = r.get("signal", "")
    if s == "NO_MW":                         return ("neutral", 0)
    if s == "MW_HIGH_QUALITY_CURE":          return ("positive", 2)
    if s == "MW_LOW_QUALITY_CURE":           return ("neutral", 0)
    if s == "MW_CURRENT":                    return ("negative", -2)
    if s == "MW_OPERATIONAL_CHAOS":          return ("negative", -3)
    return ("neutral", 0)


def score_lender_concession(r):
    s = r.get("signal", "")
    if s == "HEALTHY_LENDER_RELATIONSHIP":     return ("positive", 2)
    if s == "MIXED_LENDER_RELATIONSHIP":       return ("neutral", 0)
    if s == "DETERIORATING_LENDER_RELATIONSHIP": return ("negative", -2)
    if s == "NO_AMENDMENTS":                   return ("neutral", 0)
    return ("neutral", 0)


def run_one(ticker, cik):
    out = {"ticker": ticker, "cik": cik, "errors": []}
    print(f"  {ticker:6}  filing_timeliness...", end=" ", flush=True)
    try:
        ft = query_filing_timeliness(cik, CUTOFF)
        out["filing_timeliness"] = {"signal": ft.get("signal"), "streak": ft.get("on_time_streak_periods"), "nt_count": ft.get("nt_count_5y")}
        d, s = score_filing_timeliness(ft)
        out["filing_timeliness"]["direction"] = d
        out["filing_timeliness"]["score"] = s
        print(f"{ft.get('signal')}", end="; ")
    except Exception as e:
        out["errors"].append(f"filing_timeliness: {e}")
        print(f"ERR", end="; ")

    print(f"insider_buy_timing...", end=" ", flush=True)
    try:
        ibt = query_insider_buy_timing(cik, CUTOFF, lookback_days=540, classify_8k_text=False)
        out["insider_buy_timing"] = {
            "signal": ibt.get("signal"),
            "n_P_transactions": ibt.get("n_P_transactions"),
            "timing_class_counts": ibt.get("timing_class_counts"),
            "timing_class_dollars": ibt.get("timing_class_dollars"),
        }
        d, s = score_insider_buy_timing(ibt)
        out["insider_buy_timing"]["direction"] = d
        out["insider_buy_timing"]["score"] = s
        print(f"{ibt.get('signal')}", end="; ")
    except Exception as e:
        out["errors"].append(f"insider_buy_timing: {e}")
        print(f"ERR", end="; ")

    print(f"mw_lifecycle...", end=" ", flush=True)
    try:
        mw = query_mw_lifecycle(cik, CUTOFF, lookback_years=4)
        out["mw_lifecycle"] = {"signal": mw.get("signal"), "current_state": mw.get("current_state")}
        d, s = score_mw_lifecycle(mw)
        out["mw_lifecycle"]["direction"] = d
        out["mw_lifecycle"]["score"] = s
        print(f"{mw.get('signal')}", end="; ")
    except Exception as e:
        out["errors"].append(f"mw_lifecycle: {e}")
        print(f"ERR", end="; ")

    print(f"lender_concession...", end=" ", flush=True)
    try:
        lc = query_lender_concession(cik, CUTOFF, lookback_days=730, max_amendments_to_parse=10)
        out["lender_concession"] = {
            "signal": lc.get("signal"),
            "n_concession": lc.get("n_concession"),
            "n_restriction": lc.get("n_restriction"),
        }
        d, s = score_lender_concession(lc)
        out["lender_concession"]["direction"] = d
        out["lender_concession"]["score"] = s
        print(f"{lc.get('signal')}")
    except Exception as e:
        out["errors"].append(f"lender_concession: {e}")
        print(f"ERR")

    # Aggregate score
    total = sum([
        out.get("filing_timeliness", {}).get("score", 0),
        out.get("insider_buy_timing", {}).get("score", 0),
        out.get("mw_lifecycle", {}).get("score", 0),
        out.get("lender_concession", {}).get("score", 0),
    ])
    out["recovery_signal_score"] = total
    return out


def main():
    universe = json.load(open(TIER3_DIR / "_unblinded" / "tier3_test_set.json"))
    m24 = {r["ticker"]: r.get("fwd_return_24m") for r in json.load(open(TIER3_DIR / "_unblinded" / "tier3_24m.json"))}

    print(f"Running recovery m-sources on {len(universe)} Tier 3 names (cutoff {CUTOFF})...")
    print()

    results = []
    for r in universe:
        tk = r.get("ticker")
        cik = r.get("cik")
        if not cik or cik in ("None", ""):
            print(f"  {tk:6}  no CIK — skipping")
            continue
        try:
            res = run_one(tk, cik)
            res["fwd_12m"] = r.get("forward_return")
            res["fwd_24m"] = m24.get(tk)
            results.append(res)
        except Exception as e:
            print(f"  {tk}: error {e}")
        time.sleep(0.5)

    out_path = HERE / "recovery_backtest.json"
    out_path.write_text(json.dumps(results, indent=2))
    print(f"\nSaved {len(results)} pilots to {out_path}")


if __name__ == "__main__":
    main()
