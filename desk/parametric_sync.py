"""parametric_sync — ingestion + scorecard for the household's core sleeve.

The Parametric bundles land in ~/Downloads (Bundle_*.zip). Parsing now lives in
the first-class statement library `officekit_adapters.morgan_stanley` (MS owns
Parametric; the extracts are MS Prime formats) — this module is a thin CONSUMER
of it, so the bug we hit (reading only the newest bundle and only the first
gain/loss file, undercounting realized losses 3.5x) can't recur in one place and
survive in another. It refreshes:

  desk/data/parametric_holdings.json   — positions + the 131/31 decomposition
  desk/data/parametric_scorecard.json  — the harvest-health scorecard:
                                          harvestable surface, embedded G/L,
                                          lot-age (ossification) clock, trend
  desk/data/parametric_realized.json   — the CUMULATIVE realized-lot ledger,
                                          merged across every daily bundle

Registered daily on the heartbeat; DIAG shows the scorecard. READ-ONLY on the
world.
    python3 -m desk.parametric_sync              # ingest newest bundle
    python3 -m desk.parametric_sync --backfill   # rebuild realized across ALL bundles
"""
from __future__ import annotations

import datetime
import json
from pathlib import Path

from officekit_adapters import morgan_stanley as ms

ROOT = Path(__file__).resolve().parents[1]
HOLD = ROOT / "desk" / "data" / "parametric_holdings.json"
CARD = ROOT / "desk" / "data" / "parametric_scorecard.json"
REAL = ROOT / "desk" / "data" / "parametric_realized.json"

# fee structure (user-provided 2026-07-07): Parametric net 0.51%/yr (mgmt 0.12 + transaction 0.15
# + financing 0.24 — the extension's borrow) PLUS the MFO's 0.40% = 0.91% all-in. MFO scope
# (user 2026-07-06): bills ONLY this sleeve; buys tax review + the negotiated 0.12% institutional
# rate (retail DI ~0.35-0.45% -> ~$21-27k/yr saved) — net marginal MFO cost ~$9-15k/yr, defensible
FEES = {"parametric_pct": 0.0051, "mfo_pct": 0.0040}

# our-book symbols for the wash-sale/offset surface (refreshed manually as the book evolves)
OUR_BOOK = {"BAH", "BRBY", "CAI", "DFIN", "GCT", "HSBK", "HUBS", "J", "MNDY", "SLS", "HRTG", "G",
            "CTSH", "IBEX", "FNF", "BKE", "EQT", "FRO", "STNG", "LPG", "BBD", "EG", "ONON", "SAP",
            "OLLI", "NOW", "AST", "PEO", "POLI", "HCA", "LDOS", "CACI", "MC", "PHYS", "8750", "GOOGL", "GOOG"}


def _scorecard_from_bundle(bundle: ms.Bundle, realized_summary: dict, prev_card: dict) -> tuple[dict, dict]:
    """Harvest scorecard + holdings decomposition. The scorecard computation now
    lives in officekit_adapters.morgan_stanley (migrated 2026-09-10 — one
    implementation, the office generates its own); this desk consumer delegates the
    card and keeps the desk-only holdings decomposition."""
    card = ms.scorecard_from_bundle(bundle, realized_summary, prev_card=prev_card, our_book=OUR_BOOK)
    netpos = {}
    for p in bundle.positions():
        v = p.get("market_value_usd")
        sym = (p.get("symbol") or "").strip()
        if v is None or not sym or sym == "USD" or str(p.get("product_type") or "").upper().replace(" ", "") == "CASH":
            continue
        netpos[sym] = netpos.get(sym, 0) + v
    hold = {"asof": card["asof"], "bundle": bundle.path.name, "account": "038CAG0E4 (Parametric)",
            "total_net_usd": card["structure"]["net"], "structure": card["structure"],
            "positions": {s: round(v) for s, v in sorted(netpos.items(), key=lambda x: -abs(x[1]))}}
    return card, hold


def _rerender_household():
    try:
        from desk import household as _hh
        _hh.main()
    except Exception as e:
        print(f"[parametric_sync] household re-render skipped: {e}")


def main():
    b = ms.newest_bundle()
    if not b:
        print("[parametric_sync] no bundle in ~/Downloads")
        return
    prev_card = json.loads(CARD.read_text()) if CARD.exists() else {}
    if prev_card.get("bundle") == b.name:
        print(f"[parametric_sync] {b.name} already ingested")
        return
    bundle = ms.parse_bundle(b)
    if not bundle.positions() or not bundle.taxlots():
        print(f"[parametric_sync] {b.name}: positions/taxlot extracts not found")
        return

    # realized ledger: merge THIS bundle's daily gain/loss windows (all of them)
    ledger = ms.RealizedLedger.load(REAL)
    added = ledger.merge_bundle(bundle)
    summ = ledger.save(REAL, "accumulated from daily bundles; holding-period split "
                              "(book-side split needs a trades join)")

    card, hold = _scorecard_from_bundle(bundle, summ, prev_card)
    CARD.write_text(json.dumps(card, indent=1))
    HOLD.write_text(json.dumps(hold, indent=1))
    print(f"[parametric_sync] {b.name}: net ${card['structure']['net']:,} ({card['structure']['ratio']}) | "
          f"harvest surface ${card['harvest']['total_surface']:,} | embedded {card['embedded']['gl_pct']}% | "
          f"realized +{added} lots -> {summ['n_lots']} (net ${summ['net']:,}) | our-book: {list(card['our_book_overlap'])}")
    _rerender_household()


def backfill_realized():
    """Rebuild the realized ledger across EVERY bundle in ~/Downloads (all daily
    gain/loss files), then refresh the scorecard + dashboard. The per-bundle
    extract is a DAILY window, not cumulative YTD — so YTD realized only
    reconstructs by merging every day across every bundle (idempotent)."""
    bundles = ms.find_bundles()
    if not bundles:
        print("[parametric_sync] no bundles to backfill")
        return
    ledger = ms.RealizedLedger.load(REAL)
    added = ledger.merge_bundles(bundles)
    summ = ledger.save(REAL, f"backfilled across {len(bundles)} bundles "
                             f"({datetime.date.today().isoformat()}); holding-period split (not book-side)")
    # push the corrected figure into the scorecard the dashboard/tax-reserve reads
    if CARD.exists():
        card = json.loads(CARD.read_text())
        card["realized_ytd"] = summ
        CARD.write_text(json.dumps(card, indent=1))
        _rerender_household()
    print(f"[parametric_sync] backfill: {len(bundles)} bundles, +{added} lots -> {summ['n_lots']} total")
    print(f"  realized net {summ['net']:,} | ST {summ['st_net']:,} / LT {summ['lt_net']:,} "
          f"| gross loss ST {summ['st_loss']:,} / LT {summ['lt_loss']:,}")
    return summ


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(prog="desk.parametric_sync", description=__doc__.splitlines()[0])
    ap.add_argument("--backfill", action="store_true",
                    help="rebuild realized ledger across ALL ~/Downloads bundles (every daily GL file)")
    a = ap.parse_args()
    if a.backfill:
        backfill_realized()
    else:
        main()
