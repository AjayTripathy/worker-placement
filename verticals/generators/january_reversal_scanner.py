"""january_reversal_scanner — Stage 0b FLOW: the REVERSAL leg of the tax-loss dislocation trade.

THESIS (the pair to december_dislocation): taxable investors and Oct-31 fiscal-year funds dump
their big YTD losers into Nov-Dec for the tax deduction — price-INSENSITIVE, calendar-bounded
forced selling. That mechanical supply LIFTS at year-end, and the January-effect rebound
concentrates in exactly the cohort that was dumped: small/low-price/retail-held names too small
for the factor funds that arbitraged the anomaly out of large caps. That last clause is the whole
edge — a CAPACITY edge that survives only below the index-flow floor. December is the SELLING leg
(december_dislocation surfaces the loss basket); this scanner is the BUY-the-bounce RE-ENTRY leg.

We want the names where the December selling was tax-TECHNICAL, not fundamental: small-cap, big
YTD loss, and NOT a value trap (passes the deep-value quality gauntlet). The rebound is a FLOW
re-rating as the forced seller exits, not a fundamental call — so quality-at-a-loss DD + court is
MANDATORY before any re-entry (quality-at-a-loss is exactly where value traps hide: DCGO/COLL/PSIX).

The tradeable structure is the CALENDAR (mirrors russell_recon's dormant-countdown pattern):
  · SELLING window   — ~Dec 1-31: the tax-loss dump; december_dislocation sets the loss basket here
  · REVERSAL window  — ~Dec 20 - Jan 31: the forced seller is done; buy the bounce in the quality names
Off-season (now, July) this generator is DORMANT — a dated countdown to the next selling/reversal
windows and the mechanism. The loss basket isn't set until December, so an EMPTY candidate list
off-season is the CORRECT output; there is nothing to buy the bounce in yet.

  python3 verticals/generators/january_reversal_scanner.py [--force] [--sample N] [--min-loss -30]
Writes data/JANUARY_REVERSAL.json. READ-ONLY; proposes the re-entry basket, never sizes/orders.
"""
from __future__ import annotations
import json, datetime, argparse, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = HERE / "data" / "JANUARY_REVERSAL.json"
DEC_BASKET = HERE / "data" / "DECEMBER_CANDIDATES.json"
sys.path.insert(0, str(ROOT))

HDRS = {"User-Agent": "signalos-research 4tripathy@gmail.com"}


def _next_windows(today: datetime.date) -> dict:
    """The upcoming SELLING (~Dec 1) and REVERSAL (~Dec 20 - Jan 31) windows.

    The relevant reversal window is the current turn-of-year if its Jan-31 end is still ahead,
    else next year's. Selling opens ~Dec 1 of the same turn; reversal spans ~Dec 20 -> Jan 31.
    """
    # anchor the turn-of-year on the reversal END (Jan 31). If we're past this year's Jan 31,
    # the next reversal ends Jan 31 of NEXT year.
    rev_end = datetime.date(today.year, 1, 31)
    if today > rev_end:
        rev_end = datetime.date(today.year + 1, 1, 31)
    # the December that feeds this reversal is the one immediately before rev_end's January
    sell_year = rev_end.year - 1
    sell_start = datetime.date(sell_year, 12, 1)
    sell_end = datetime.date(sell_year, 12, 31)
    rev_start = datetime.date(sell_year, 12, 20)   # bounce buying starts as selling exhausts
    return {
        "selling_window": {"start": sell_start.isoformat(), "end": sell_end.isoformat()},
        "reversal_window": {"start": rev_start.isoformat(), "end": rev_end.isoformat()},
    }


def phase_for(today: datetime.date, w: dict) -> tuple[str, str, dict]:
    """phase + action + days_to milestones, mirroring russell_recon's dated-countdown shape."""
    sell_start = datetime.date.fromisoformat(w["selling_window"]["start"])
    rev_start = datetime.date.fromisoformat(w["reversal_window"]["start"])
    rev_end = datetime.date.fromisoformat(w["reversal_window"]["end"])
    days_to = {
        "selling_window_start": (sell_start - today).days,
        "reversal_window_start": (rev_start - today).days,
        "reversal_window_end": (rev_end - today).days,
    }
    if today < sell_start:
        phase = "DORMANT — off-season (pre-selling)"
        action = ("Nothing to do; the loss basket isn't set until the December tax-loss window. "
                  f"Selling opens ~{sell_start.isoformat()} ({days_to['selling_window_start']:+d}d); "
                  f"the reversal RE-ENTRY window opens ~{rev_start.isoformat()} "
                  f"({days_to['reversal_window_start']:+d}d).")
    elif today < rev_start:
        phase = "SELLING UNDERWAY — loss basket forming"
        action = ("The tax-loss dump is live; december_dislocation is surfacing the loss basket. "
                  "Do NOT front-run the bounce — the forced seller is still pressing. Pre-screen the "
                  "basket through DD+court now so the quality names are ready when the reversal opens "
                  f"~{rev_start.isoformat()} ({days_to['reversal_window_start']:+d}d).")
    elif today <= rev_end:
        phase = "⚡ REVERSAL WINDOW OPEN — buy the bounce"
        action = ("The forced seller is exhausting. Pull the December loss basket and surface the "
                  "re-entry candidates (tax-TECHNICAL selling, not fundamental: small-cap, big YTD "
                  "loss, quality-gauntlet PASS). Ladder into the quality-at-a-loss names ONLY after "
                  f"DD+court. Window exits ~{rev_end.isoformat()} ({days_to['reversal_window_end']:+d}d).")
    else:
        phase = "POST-REVERSAL"
        action = "Reversal window closed; unwind the calendar leg. Next selling window opens ~Dec 1."
    return phase, action, days_to


def in_reversal(today: datetime.date, w: dict) -> bool:
    rev_start = datetime.date.fromisoformat(w["reversal_window"]["start"])
    rev_end = datetime.date.fromisoformat(w["reversal_window"]["end"])
    return rev_start <= today <= rev_end


# --- basket logic reused from december_dislocation (mirror; import the shared quality gates) ---

def _quality(rec: dict) -> tuple[bool, str]:
    """The deep-value gates: TTM EBIT>0, FCF>0, quarter not collapsing (mirrors december_dislocation)."""
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


def _reversal_candidates_from_dec_basket(min_loss: float) -> tuple[list[dict], str]:
    """In-season: reuse december_dislocation's ALREADY-SCREENED loss basket as the re-entry set.

    The December scanner has already applied loss-depth x quality x trap-guards x wash-sale; those
    ARE the tax-technical, non-value-trap, small-cap names. The reversal leg just re-frames them as
    BUY-the-bounce candidates. If the December basket is stale/absent, fall back to a live compute.
    """
    if DEC_BASKET.exists():
        try:
            d = json.loads(DEC_BASKET.read_text())
            cands = []
            for c in d.get("candidates", []):
                if c.get("ytd_pct") is not None and c["ytd_pct"] <= min_loss:
                    cands.append({
                        "sym": c["sym"], "ytd_pct": c["ytd_pct"], "score": c.get("score"),
                        "ebit_ttm": c.get("ebit_ttm"),
                        "note": "REVERSAL re-entry — tax-technical selling, quality-gauntlet PASS; "
                                "DD+court MANDATORY before any ladder (quality-at-a-loss = trap zone)",
                    })
            cands.sort(key=lambda c: -(c.get("score") or 0))
            return cands, f"december_dislocation basket ({d.get('asof')}, {len(cands)} pass min_loss)"
        except Exception as e:
            return [], f"december basket unreadable ({e}); recompute needed"
    return _reversal_candidates_live(min_loss)


def _reversal_candidates_live(min_loss: float) -> tuple[list[dict], str]:
    """Fallback in-season compute if no December basket file exists — mirrors december_dislocation."""
    try:
        from verticals.deep_value import fundamentals as F
        from verticals.deep_value.fundamentals import merger_pending, is_foreign_filer
        import urllib.request, yfinance as yf
        req = urllib.request.Request("https://www.sec.gov/files/company_tickers.json", headers=HDRS)
        with urllib.request.urlopen(req, timeout=45) as r:
            tick = json.load(r)
        cik2sym = {v["cik_str"]: v["ticker"] for v in tick.values()}
        xs = F.build_cross_section()
        rows = [{"sym": cik2sym[c], "cik": c, **rec} for c, rec in xs.items()
                if cik2sym.get(c) and "." not in cik2sym[c] and "-" not in cik2sym[c]]
        syms = [r["sym"] for r in rows]
        ytd = {}
        for i in range(0, len(syms), 100):
            batch = syms[i:i + 100]
            try:
                df = yf.download(batch, start=f"{datetime.date.today().year}-01-01",
                                 progress=False, auto_adjust=True)["Close"]
            except Exception:
                continue
            for s in batch:
                try:
                    ser = df[s].dropna() if hasattr(df, "columns") else df.dropna()
                    if len(ser) > 20:
                        ytd[s] = float(ser.iloc[-1] / ser.iloc[0] - 1)
                except Exception:
                    pass
        cands = []
        for r in rows:
            yret = ytd.get(r["sym"])
            if yret is None or yret > min_loss / 100.0:
                continue
            ok, _ = _quality(r)
            if not ok:
                continue
            if merger_pending(r["cik"]) or is_foreign_filer(r["cik"]):
                continue
            cands.append({"sym": r["sym"], "ytd_pct": round(yret * 100, 1),
                          "score": round(abs(yret) * 100, 1), "ebit_ttm": r.get("OperatingIncomeLoss"),
                          "note": "REVERSAL re-entry (live compute) — DD+court MANDATORY before any ladder"})
        cands.sort(key=lambda c: -c["score"])
        return cands[:40], f"live compute ({len(rows)} universe)"
    except Exception as e:
        return [], f"live compute failed ({e})"


def scan(min_loss: float, force: bool) -> dict:
    today = datetime.date.today()
    w = _next_windows(today)
    phase, action, days_to = phase_for(today, w)
    active = in_reversal(today, w) or force
    candidates, basket_src = [], "dormant — loss basket not set until the December window"
    if active:
        candidates, basket_src = _reversal_candidates_from_dec_basket(min_loss)
    return {
        "asof": today.isoformat(),
        "phase": phase,
        "action": action,
        "next_selling_window": w["selling_window"],
        "next_reversal_window": w["reversal_window"],
        "days_to": days_to,
        "days_to_reversal": days_to["reversal_window_start"],
        "min_loss_pct": min_loss,
        "basket_source": basket_src,
        "candidates": candidates,
        "note": "FLOW class — the REVERSAL leg that pairs with december_dislocation. Small-caps dumped "
                "for December tax losses SNAP BACK in January as the price-INSENSITIVE forced selling "
                "lifts. The effect survives ONLY in small caps too small for the factor funds that "
                "arbitraged it out of large caps (a CAPACITY edge). Off-season = a dated countdown; the "
                "loss basket isn't set until December, so EMPTY candidates off-season is CORRECT. In the "
                "reversal window it re-frames december_dislocation's already-screened basket as BUY-the-"
                "bounce re-entries. The rebound is a FLOW re-rating, not a fundamental call — quality-at-"
                "a-loss DD + court is MANDATORY before any re-entry (that cohort is where value traps hide).",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="pull the basket outside the reversal window (test)")
    ap.add_argument("--sample", type=int, default=None, help="unused off-season; kept for parity")
    ap.add_argument("--min-loss", type=float, default=-30.0, help="min YTD loss %% to count as dumped")
    a = ap.parse_args()
    res = scan(a.min_loss, a.force)
    sw, rw = res["next_selling_window"], res["next_reversal_window"]
    d = res["days_to"]
    print(f"=== JANUARY REVERSAL SCANNER  {res['asof']} ===")
    print(f"  PHASE: {res['phase']}")
    print(f"  SELLING window  {sw['start']} -> {sw['end']}  (opens {d['selling_window_start']:+d}d)")
    print(f"  REVERSAL window {rw['start']} -> {rw['end']}  (opens {d['reversal_window_start']:+d}d, "
          f"closes {d['reversal_window_end']:+d}d)")
    print(f"  ACTION: {res['action']}")
    print(f"  basket: {res['basket_source']}")
    if res["candidates"]:
        for c in res["candidates"][:15]:
            ebit = c.get("ebit_ttm")
            ebit_s = f"{round(ebit/1e6)}M" if ebit else "?"
            print(f"  {c['sym']:<6} YTD {c['ytd_pct']:>7.1f}%  score {c.get('score'):>5}  EBIT ttm {ebit_s}")
    else:
        print("  candidates: [] — DORMANT off-season BY DESIGN (nothing to buy the bounce in yet)")
    OUT.write_text(json.dumps(res, indent=1))
    print(f"[-> {OUT.name}]")


if __name__ == "__main__":
    main()
