"""december_dislocation_scanner — Stage 0b generator: the BUY-SIDE of other people's tax-loss harvests.

MECHANISM (2026 plan: the $0.5-0.75M December dislocation reserve): taxable investors and Oct-31
fiscal-year mutual funds mechanically sell their big YTD losers in Nov-Dec regardless of quality;
the pressure is price-insensitive and calendar-bounded, and the historical January-effect rebound
concentrates in exactly the cohort being sold (small/mid, low-price, retail-held, hardest-hit).
We want the QUALITY names caught in that flow — losers whose businesses pass the deep-value trap
gauntlet — bought INTO December weakness via ladders, adjudicated by the pipeline first.

SELF-GATING: full runs only Oct-Dec (the harvest window); off-season exits fast unless --force.
CADENCE: weekly from Oct-1; the shortlist -> DD+court early Nov; ladders staged pre-Thanksgiving.

SCORE = loss_depth x quality x harvest_pressure:
  loss_depth   — YTD return <= -30% (deeper = more mechanical supply)
  quality      — SEC XBRL TTM (reuses deep_value.fundamentals): EBIT > 0 TTM, OCF-capex > 0,
                 both quarters non-degrading; the trap guards (merger_pending, foreign filer)
  harvest_px   — proxies for who holds it: sub-$40 price (retail cohorts), mktcap $200M-$10B
                 (below index-flow support, above the untouchable), ADV sane for our size
DOCTRINE GUARDS: every candidate still goes through DD + court — the scanner PROPOSES only;
quality-at-a-loss is where value traps live (DCGO/COLL/PSIX catalog), so the gauntlet is not
optional. Wash-sale note: OUR OWN harvested names are EXCLUDED as buys for 31 days (the
wash-sale window) — the excluded list reads desk/data/harvested_2026.json if present.

  python3 verticals/generators/december_dislocation_scanner.py [--force] [--sample N] [--min-loss -30]
Writes data/DECEMBER_CANDIDATES.json. READ-ONLY; proposes, never sizes.
"""
from __future__ import annotations
import json, datetime, argparse, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = HERE / "data" / "DECEMBER_CANDIDATES.json"
sys.path.insert(0, str(ROOT))


def in_season(today: datetime.date | None = None) -> bool:
    m = (today or datetime.date.today()).month
    return m in (10, 11, 12)


def _universe_from_deepvalue() -> list[dict]:
    """ticker/cik/mktcap/px rows from the SEC company_tickers + XBRL cross-section."""
    from verticals.deep_value import fundamentals as F
    import urllib.request
    req = urllib.request.Request("https://www.sec.gov/files/company_tickers.json",
                                 headers={"User-Agent": "signalos-research 4tripathy@gmail.com"})
    with urllib.request.urlopen(req, timeout=45) as r:
        tick = json.load(r)
    cik2sym = {v["cik_str"]: v["ticker"] for v in tick.values()}
    xs = F.build_cross_section()
    rows = []
    for cik, rec in xs.items():
        sym = cik2sym.get(cik)
        if not sym or "." in sym or "-" in sym:
            continue
        rows.append({"sym": sym, "cik": cik, **rec})
    return rows


def _ytd_returns(symbols: list[str]) -> dict[str, float]:
    import yfinance as yf
    out = {}
    for i in range(0, len(symbols), 100):
        batch = symbols[i:i + 100]
        try:
            df = yf.download(batch, start=f"{datetime.date.today().year}-01-01",
                             progress=False, auto_adjust=True)["Close"]
        except Exception:
            continue
        for s in batch:
            try:
                ser = df[s].dropna() if hasattr(df, "columns") else df.dropna()
                if len(ser) > 20:
                    out[s] = float(ser.iloc[-1] / ser.iloc[0] - 1)
            except Exception:
                pass
    return out


def _quality(rec: dict) -> tuple[bool, str]:
    """The deep-value gates: TTM EBIT>0, FCF>0, quarter not collapsing."""
    ebit = rec.get("OperatingIncomeLoss")
    ocf = rec.get("NetCashProvidedByUsedInOperatingActivities")
    capex = rec.get("PaymentsToAcquirePropertyPlantAndEquipment") or 0
    if ebit is None or ebit <= 0:
        return False, "EBIT<=0"
    if ocf is None or (ocf - abs(capex)) <= 0:
        return False, "FCF<=0"
    q, qp = rec.get("OperatingIncomeLoss_q"), rec.get("OperatingIncomeLoss_q_prior")
    if q is not None and qp is not None and qp > 0 and q < 0.4 * qp:
        return False, "quarter collapsing (>60% EBIT drop)"
    return True, "ok"


def scan(min_loss: float, sample: int | None) -> dict:
    today = datetime.date.today().isoformat()
    harvested = set()
    hp = ROOT / "desk" / "data" / "harvested_2026.json"
    if hp.exists():
        harvested = set(json.loads(hp.read_text()))
    rows = _universe_from_deepvalue()
    if sample:
        rows = rows[:sample]
    ytd = _ytd_returns([r["sym"] for r in rows])
    from verticals.deep_value.fundamentals import merger_pending, is_foreign_filer
    cands, dropped = [], {"not_loser": 0, "quality": 0, "trap_guard": 0, "washsale": 0, "no_px": 0}
    for r in rows:
        yret = ytd.get(r["sym"])
        if yret is None:
            dropped["no_px"] += 1; continue
        if yret > min_loss / 100.0:
            dropped["not_loser"] += 1; continue
        ok, why = _quality(r)
        if not ok:
            dropped["quality"] += 1; continue
        if r["sym"] in harvested:
            dropped["washsale"] += 1; continue
        if merger_pending(r["cik"]) or is_foreign_filer(r["cik"]):
            dropped["trap_guard"] += 1; continue
        score = round(abs(yret) * 100, 1)
        cands.append({"sym": r["sym"], "ytd_pct": round(yret * 100, 1), "score": score,
                      "ebit_ttm": r.get("OperatingIncomeLoss"),
                      "note": "quality-at-a-loss — DD+court MANDATORY before any ladder"})
    cands.sort(key=lambda c: -c["score"])
    return {"asof": today, "min_loss_pct": min_loss, "n_universe": len(rows),
            "dropped": dropped, "candidates": cands[:40],
            "doctrine": "scanner proposes; pipeline disposes. Ladders staged pre-Thanksgiving ONLY for court-adjudicated names; wash-sale exclusions applied; the January-effect cohort (small, low-px, retail-held) gets sizing priority at equal quality."}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="run outside the Oct-Dec season")
    ap.add_argument("--sample", type=int, default=None, help="cap universe for a test run")
    ap.add_argument("--min-loss", type=float, default=-30.0)
    a = ap.parse_args()
    if not in_season() and not a.force:
        print(f"off-season (month {datetime.date.today().month}) — the harvest window is Oct-Dec; exiting (use --force to test)")
        return
    res = scan(a.min_loss, a.sample)
    print(f"=== DECEMBER DISLOCATION SCANNER  {res['asof']}  (universe {res['n_universe']}, losers <= {res['min_loss_pct']}%) ===")
    print(f"  dropped: {res['dropped']}")
    for c in res["candidates"][:15]:
        print(f"  {c['sym']:<6} YTD {c['ytd_pct']:>7.1f}%  score {c['score']:>5}  EBIT ttm {c['ebit_ttm'] and round(c['ebit_ttm']/1e6) or '?'}M")
    if not res["candidates"]:
        print("  no candidates (small sample or off-season universe)")
    OUT.write_text(json.dumps(res, indent=1))
    print(f"[-> {OUT.name}] — shortlist -> DD+court early Nov; ladders pre-Thanksgiving; deploy into December weakness.")


if __name__ == "__main__":
    main()
