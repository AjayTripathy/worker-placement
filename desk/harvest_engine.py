"""Harvest engine v0 — Phase 0/1 of the in-house TLH automation (principal-directed 2026-08-26).

The build ladder (architecture doc §4.5 + session ruling):
  Phase 0 (this module): pair-map validation, wash-window ledger, CONSTRUCTIVE-SALE guard.
  Phase 1 (this module, --staged-basket): rotation rules R1/R2 -> STAGED BasketTrader CSV.
           Computation is automated; EXECUTION is the principal's click. BETA keeps zero
           automated order paths.
  Phase 2 (pilot, separate ratification): completion-set short clip, sector/beta matched.
  Phase 3 (closed loop): only after a graded pilot AND an explicit autonomy-rung change.

Tax rails codified here, not in anyone's memory:
  WASH (§1091):        loss sale washed by a buy of substantially-identical within +/-30d,
                       ACROSS ALL HOUSEHOLD ACCOUNTS (ALPHA + BETA + Parametric + GOOGL lot).
  CONSTRUCTIVE (§1259): shorting a name the household holds APPRECIATED = deemed sale of the
                       appreciated long. Short candidates must clear the ENTIRE household
                       long book — Parametric's embedded winners above all. The anti-TLH trap.
  ST-ALWAYS:           short gains are short-term regardless of holding period — the engine
                       prefers realizing short LOSSES and carrying short winners.

Usage:
  python3 -m desk.harvest_engine --validate-pairs      # pair map vs newest Parametric bundle
  python3 -m desk.harvest_engine --wash-check TICKER   # is a loss-sale of TICKER wash-safe today?
  python3 -m desk.harvest_engine --short-screen A,B,C  # constructive-sale + household screen
  python3 -m desk.harvest_engine --staged-basket       # R1 scan -> staged CSV (needs BETA lots)
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sqlite3
import sys
from pathlib import Path

DESK = Path(__file__).parent
DATA = DESK / "data"
MSPRIME = Path("/Users/ajay/msprime/app/data/msprime.db")
PAIR_MAP = DATA / "harvest_pair_map_20260821.json"
ALPHA_CACHE = DATA / "alpha_positions_cache.json"
WASH_WINDOW_DAYS = 30  # each side of the loss sale

HOUSEHOLD_ASSERTED = {"GOOGL", "GOOG"}  # the external lot — asserted, never assumed


def _parametric(as_of_check: bool = False):
    """Latest Parametric bundle symbols (+ reporting date)."""
    c = sqlite3.connect(MSPRIME)
    maxd = c.execute("select max(reporting_date) from positions").fetchone()[0]
    syms = {r[0] for r in c.execute(
        "select distinct symbol from positions where reporting_date=?", (maxd,))}
    c.close()
    return syms, maxd


def _parametric_longs_with_sign():
    """symbol -> net qty sign from the latest bundle (shorts are negative)."""
    c = sqlite3.connect(MSPRIME)
    maxd = c.execute("select max(reporting_date) from positions").fetchone()[0]
    rows = c.execute(
        "select symbol, sum(current_quantity) from positions where reporting_date=? group by symbol",
        (maxd,)).fetchall()
    c.close()
    return {r[0]: (r[1] or 0) for r in rows}, maxd


def _alpha_symbols():
    try:
        cache = json.loads(ALPHA_CACHE.read_text())
        syms = set()
        for p in cache.get("positions", []):
            syms.add(p.get("symbol") or p.get("localSymbol"))
        for o in cache.get("orders", []):
            syms.add(o.get("symbol"))
        return {s for s in syms if s}
    except Exception:
        return set()


def validate_pairs() -> int:
    """Every pair partner must be OUTSIDE the current wash surface (Parametric newest bundle +
    ALPHA book + asserted names). A partner that drifted INTO the surface is a broken pair."""
    pm = json.loads(PAIR_MAP.read_text())
    para, bundle_date = _parametric(True)
    alpha = _alpha_symbols()
    surface = para | alpha | HOUSEHOLD_ASSERTED
    stale_days = (dt.date.today() - dt.date.fromisoformat(pm["asof"])).days
    print(f"pair map asof {pm['asof']} ({stale_days}d old) vs bundle {bundle_date}")
    broken = []
    for slot, row in pm["pairs"].items():
        partner = row.get("partner")
        if partner and partner.split(".")[0] in surface:
            broken.append((slot, partner))
    if broken:
        print(f"BROKEN PAIRS ({len(broken)}) — partner drifted into the wash surface:")
        for s, p in broken:
            print(f"  {s}: partner {p} now held household-side — re-pair before harvesting {s}")
    else:
        print(f"all {len(pm['pairs'])} pairs clear the current surface")
    if stale_days > 14:
        print(f"WARN: pair map {stale_days}d old vs a weekly-refresh surface — revalidate after "
              f"each new Bundle_*.zip")
    return 1 if broken else 0


def _household_trades_near(symbol: str, window: int = WASH_WINDOW_DAYS):
    """Household BUYS of symbol within the window (Parametric gainloss table + ALPHA trades
    would slot in here; v0 checks Parametric position deltas + flags the manual legs)."""
    notes = []
    para, maxd = _parametric(True)
    if symbol in para:
        notes.append(f"Parametric HOLDS {symbol} (bundle {maxd}) — PARAMETRIC_SELF protocol: "
                     f"pull their trade file for +/-{window}d before harvesting")
    if symbol in HOUSEHOLD_ASSERTED:
        notes.append(f"{symbol} is an asserted household name — never harvested, never repurchased")
    return notes


def wash_check(symbol: str) -> None:
    notes = _household_trades_near(symbol)
    pm = json.loads(PAIR_MAP.read_text())
    row = pm["pairs"].get(symbol, {})
    print(f"WASH CHECK {symbol}:")
    for n in notes:
        print(f"  ! {n}")
    if row:
        print(f"  pair: {row.get('partner')} (fallback {row.get('fallback_etf')}) — "
              f"buy the partner, sell the loser, 31 days, swap back or keep")
    else:
        print(f"  NO PAIR ROW — per doctrine: no pair, no harvest. Add to the map first.")


def short_screen(cands: list[str]) -> None:
    """§1259 constructive-sale + household screen for Phase-2 short candidates."""
    para_qty, maxd = _parametric_longs_with_sign()
    alpha = _alpha_symbols()
    print(f"SHORT SCREEN vs bundle {maxd} + ALPHA book + asserted:")
    for s in cands:
        s = s.strip().upper()
        why = []
        q = para_qty.get(s, 0)
        if q > 0:
            why.append(f"Parametric LONG {q:,.0f} sh — §1259 CONSTRUCTIVE-SALE RISK on their "
                       f"appreciated lot (the anti-TLH trap)")
        if q < 0:
            why.append("Parametric already SHORT — cross-book short-wash/duplication")
        if s in alpha:
            why.append("ALPHA book touches it — judgment name, belongs behind courts")
        if s in HOUSEHOLD_ASSERTED:
            why.append("asserted household name")
        print(f"  {s}: {'REJECT — ' + '; '.join(why) if why else 'CLEAR (completion-set)'}")


def staged_basket() -> None:
    print("R1 scan needs BETA lots — account not yet live. This command becomes real at landing:")
    print("  trigger: index lot loss >= $5k or a <= -1.5% index day")
    print("  output: specific-lot sells (highest basis) + slot buys at bands -> BasketTrader CSV")
    print("  the CSV is STAGED WORK — the principal clicks; no automated path exists in BETA.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--validate-pairs", action="store_true")
    ap.add_argument("--wash-check", type=str)
    ap.add_argument("--short-screen", type=str)
    ap.add_argument("--staged-basket", action="store_true")
    a = ap.parse_args()
    if a.validate_pairs:
        sys.exit(validate_pairs())
    if a.wash_check:
        wash_check(a.wash_check)
    elif a.short_screen:
        short_screen(a.short_screen.split(","))
    elif a.staged_basket:
        staged_basket()
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
