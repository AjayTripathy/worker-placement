"""orphan_screen v2 — the UNIVERSAL orphan/carry sweep, on the doctrine data stack
(user directives 2026-08-06: "screen every public equity" + "why yahoo when we have
the Gateway").

DATA STACK (v2 — yahoo demoted):
  prices        IBKR Gateway delayed-snapshot sweep (desk/gw_quotes.py; local, contractual,
                no IP rate-limit wars) — falls back to the Nasdaq screener's lastsale,
                flagged px_basis, never silently
  mcap          Nasdaq screener marketCap, re-marked by gw_px/lastsale (implied shares)
  fundamentals  SEC XBRL frames (audited, TTM via the deep-value machinery) — never a
                quote vendor's ratios; with EDGAR inputs the ADR ratio-identity guard is
                exact by construction, so the failure mode shifts to fundamentals_missing
                (foreign ADRs without us-gaap frames), which is COUNTED, never silent
  coverage      yahoo ONLY at shortlist scale (~200 names): analyst rating + opinion count
                — the one datum the Gateway doesn't carry

SELECTION: absence of coverage first, carry second —
  carry_spread = NI_ttm / mcap  −  (rf_10Y + Damodaran total ERP by country)
FAIR-CARRY doctrine (PRD R1.9): fair-or-better carry in uncovered paper is the product.
Financials INCLUDED (a bank IS a carry instrument; the country CoE is its bar).

  python3 -m verticals.deep_value.orphan_screen [--top 40] [--max-analysts 2] [--no-enrich]
"""
from __future__ import annotations

import argparse
import datetime
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))

DATA = HERE / "data"
OUT = DATA / "orphan_carry_shortlist.json"
CRP = ROOT / "desk" / "data" / "damodaran_crp.json"

COUNTRY_MAP = {"South Korea": "Korea", "Hong Kong": "Hong Kong SAR"}
MIN_MCAP = 30e6
CARRY_FLOOR = 0.0


def _rf_live() -> float:
    """10Y UST. Gateway-first would need an index sub; the one tiny yahoo call is tolerable,
    with the Damodaran-vintage rf as the documented fallback."""
    try:
        sys.path.insert(0, str(HERE / "global"))
        from screen_korea import _yahoo_quotes
        q = (_yahoo_quotes(["^TNX"]) or {}).get("^TNX") or {}
        px = q.get("regularMarketPrice")
        if px and 1.0 < px < 12.0:
            return round(px / 100, 5)
    except Exception:
        pass
    return 0.0423


def coe_for(country: str | None, crp: dict, rf: float) -> tuple[float, str]:
    c = COUNTRY_MAP.get(str(country or "").strip(), str(country or "").strip())
    row = crp["countries"].get(c)
    if row is None:
        return rf + crp["us_mature_erp"], f"country '{country}' not in CRP table — US ERP used"
    return rf + row["total_erp"], c


def ni_ttm_cross_section() -> dict:
    """{cik: TTM net income} from SEC frames — the same rolling-TTM idiom as the deep-value
    cross-section (annual − old Q + new Q, annual fallback)."""
    import fundamentals as F
    ann = F._freshest("NetIncomeLoss", F.ANNUAL_FALLBACK)
    qo = F.frame("NetIncomeLoss", F.Q_OLD)
    qn = F.frame("NetIncomeLoss", F.Q_NEW)
    out = {}
    for cik, a in ann.items():
        o, n = qo.get(cik), qn.get(cik)
        out[cik] = (a - o + n) if (o is not None and n is not None) else a
    return out


def build_rows(uni: list[dict], gw_px: dict, ni: dict, eq: dict, t2c: dict,
               crp: dict, rf: float) -> list[dict]:
    rows = []
    for u in uni:
        t = u["ticker"]
        mcap0, last = u.get("mcap"), u.get("lastsale")
        if not mcap0 or mcap0 < MIN_MCAP:
            continue
        g = gw_px.get(t)
        px = g["px"] if g else last
        px_basis = "gateway" if g else ("screener_lastsale" if last else None)
        if px is None:
            continue
        mcap = mcap0 * (px / last) if (last and px) else mcap0     # re-mark by implied shares
        cik = t2c.get(t)
        ni_v, eq_v = (ni.get(cik), eq.get(cik)) if cik else (None, None)
        coe, coe_basis = coe_for(u.get("country"), crp, rf)
        ey = (ni_v / mcap) if (ni_v is not None and mcap) else None
        rows.append({
            "ticker": t, "name": u.get("name", "")[:40], "sector": u.get("sector"),
            "country": u.get("country"), "cik": cik,
            "mcap": round(mcap), "px": px, "px_basis": px_basis,
            "ni_ttm": ni_v, "equity": eq_v,
            "ey": round(ey, 4) if ey is not None else None,
            "pb": round(mcap / eq_v, 3) if (eq_v and eq_v > 0) else None,
            "roe": round(ni_v / eq_v, 4) if (ni_v is not None and eq_v and eq_v > 0) else None,
            "coe": round(coe, 4), "coe_basis": coe_basis,
            "carry_spread": round(ey - coe, 4) if ey is not None else None,
            "fundamentals_missing": ni_v is None,
            "ey_no_earnings": ni_v is not None and ni_v <= 0,
        })
    return rows


def rank(rows: list[dict]) -> list[dict]:
    clean = [r for r in rows if not r["fundamentals_missing"] and not r["ey_no_earnings"]
             and r["carry_spread"] is not None and r["carry_spread"] >= CARRY_FLOOR]
    return sorted(clean, key=lambda r: -r["carry_spread"])


def enrich_coverage(rows: list[dict], max_n=200) -> None:
    """Shortlist-only yahoo: rating + analyst count — the orphan gate. ~0.4s/name pacing."""
    try:
        import yfinance as yf
    except ImportError:
        for r in rows[:max_n]:
            r["analysts"] = None
        return
    for r in rows[:max_n]:
        try:
            info = yf.Ticker(r["ticker"]).info
            r["analysts"] = info.get("numberOfAnalystOpinions")
            r["rating"] = info.get("averageAnalystRating")
        except Exception:
            r["analysts"] = None
        time.sleep(0.4)


def run(top=40, max_analysts=2, enrich=True):
    from universe import _get, NASDAQ_URL, NASDAQ_HDRS, ticker_to_cik
    crp = json.loads(CRP.read_text())
    rf = _rf_live()
    print(f"orphan_screen v2 (gateway/EDGAR): rf={rf:.2%}, CRP vintage {crp['vintage']}")
    raw = _get(NASDAQ_URL, NASDAQ_HDRS)["data"]["rows"]
    uni = []
    for r in raw:
        t = r["symbol"].strip()
        if "^" in t or "/" in t or " " in t:
            continue
        def _num(x):
            try:
                return float(str(x).replace("$", "").replace(",", ""))
            except (ValueError, TypeError):
                return None
        uni.append({"ticker": t, "name": r.get("name", ""), "sector": r.get("sector"),
                    "country": r.get("country"), "mcap": _num(r.get("marketCap")),
                    "lastsale": _num(r.get("lastsale"))})
    print(f"universe (US-listed common incl. ADRs, ALL sectors): {len(uni)}")
    from desk.gw_quotes import bulk_quotes
    gw = bulk_quotes([u["ticker"] for u in uni])
    print(f"gateway-priced: {len(gw)} "
          f"({'FALLBACK px_basis=screener_lastsale for the rest' if len(gw) < len(uni) else ''})")
    print("EDGAR frames: NI ttm + equity cross-section…")
    import fundamentals as F
    ni = ni_ttm_cross_section()
    eq = F._freshest("StockholdersEquity", F.INSTANTS)
    t2c = ticker_to_cik()
    rows = build_rows(uni, gw, ni, eq, t2c, crp, rf)
    n_miss = sum(1 for r in rows if r["fundamentals_missing"])
    ranked = rank(rows)
    print(f"rows {len(rows)} | fundamentals_missing (no us-gaap frames — mostly foreign ADRs, "
          f"COUNTED not hidden): {n_miss} | fair-or-better carry: {len(ranked)}")
    short = ranked[:top * 5]
    if enrich:
        print(f"coverage enrich (yahoo, shortlist-only) on {min(len(short), 200)}…")
        enrich_coverage(short)
        short = [r for r in short if (r.get("analysts") or 0) <= max_analysts]
    short = short[:top]
    payload = {"meta": {"generated_utc": datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z",
                        "rf": rf, "crp_vintage": crp["vintage"], "universe": len(uni),
                        "gateway_priced": len(gw), "fundamentals_missing": n_miss,
                        "stack": "gw_quotes + nasdaq-screener mcap + SEC frames; yahoo shortlist-coverage only"},
               "rows": short}
    DATA.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=1))
    print(f"\n  {'tkr':8s}{'country':14s}{'mc$M':>8s}{'ey':>7s}{'CoE':>7s}{'spread':>8s}{'P/B':>6s}{'anlst':>6s} px_src     name")
    for r in short:
        print(f"  {r['ticker']:8s}{str(r['country'])[:13]:14s}{r['mcap']/1e6:8.0f}"
              f"{r['ey']:7.1%}{r['coe']:7.1%}{r['carry_spread']:8.1%}"
              f"{r['pb'] if r['pb'] else 0:6.2f}{str(r.get('analysts','?')):>6s} {str(r['px_basis'])[:9]:10s}{r['name'][:24]}")
    try:
        from desk.court_queue import enqueue_candidates
        c = enqueue_candidates(short[:15], source=f"orphan_screen/{datetime.date.today().isoformat()}")
        print(f"\ncourt_queue: {c['added']} new candidates enqueued")
    except Exception as e:
        print(f"court_queue enqueue failed (screen output unaffected): {type(e).__name__}: {e}")
    return short


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=40)
    ap.add_argument("--max-analysts", type=int, default=2)
    ap.add_argument("--no-enrich", action="store_true")
    a = ap.parse_args()
    run(a.top, a.max_analysts, enrich=not a.no_enrich)
