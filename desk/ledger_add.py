"""ledger_add — upsert a researched name into the research ledger (the Watchlist book the UI reads),
so every DD conclusion lands in the book + dashboard the moment it's reached. Standing rule: whenever a
diligence concludes, the name goes here with its verdict; if the research built a detector it's picked up
by rebuilding the KG (knowledge_graph/build_knowledge_graph.py), and if it built a price watcher it goes
in desk/registry.py. This closes the research->UI gap that kept surfacing.

  # add or update a name (upsert by ticker):
  python3 -m desk.ledger_add SFM --name "Sprouts" --sleeve k_shaped_bottom --verdict OWNABLE \\
      --thesis "..." --entry "..." --source "..." [--yf SFM] [--alert-below 70] [--conviction "..."]

  # or programmatically:
  from desk.ledger_add import upsert
  upsert({"ticker":"X","name":"...","sleeve":"...","verdict":"WATCH","thesis":"...","source":"..."})
"""
from __future__ import annotations
import argparse, datetime, json
from pathlib import Path

LEDGER = Path(__file__).resolve().parent / "data" / "research_ledger.json"
VERDICTS = {"HELD", "OWN", "OWNABLE", "STARTER", "WATCH", "WAIT", "NOT_YET", "AVOID", "SHORT", "TO_DILIGENCE"}

# EDGE SOURCE — the PRIMARY organizing axis (why is this mispriced, and why is it ours?).
# Determines the clock, the exit doctrine, and — critically — which CALIBRATION COHORT it grades
# into. Grade WITHIN class, never pooled (a FLOW win is a different skill than an INFO win).
#   FLOW       event-driven / corporate-action: a price-INSENSITIVE agent is forced to trade
#              (index recon, spin deletion, forced liquidation) — we provide liquidity. Event-dated;
#              pre-registered mechanical exit ("the exit is the trade"). e.g. MFP.
#   INFO       nowcast / MFT: we read the operating trajectory before the analyst does. Exit at the
#              catalyst; grade nowcast Brier THEN price edge. This cohort == the MFT forward test.
#   VALUE      fundamental mispricing: worth != price; months-quarters; exit at FV or thesis-break.
#   CARRY      risk premium / RP_FAIR: paid to hold a real, BOUNDED risk others avoid (rented risk,
#              not an edge). Open-ended; exit when the risk re-rates or comp compresses. e.g. ELE.
#   CONVEXITY  tail / regime: asymmetric payoff to a regime shift (crisis/inflation/gold bid).
#   EXCLUSION  honesty / diligence-alpha: the value is in what we DON'T own (the anti-portfolio).
#   UNCLASSIFIED  not yet assigned — flagged by the class rollup for review (never silently counted).
EDGE_SOURCES = {"FLOW", "INFO", "VALUE", "CARRY", "CONVEXITY", "EXCLUSION", "UNCLASSIFIED"}


def upsert(entry: dict) -> str:
    """Add or update a ledger name by ticker. Returns 'added' or 'updated'. Defaults yf=ticker."""
    assert entry.get("ticker"), "ticker required"
    assert entry.get("verdict") in VERDICTS, f"verdict must be one of {sorted(VERDICTS)}"
    es = entry.get("edge_source")
    if es is not None and es not in EDGE_SOURCES:
        raise AssertionError(f"edge_source must be one of {sorted(EDGE_SOURCES)}")
    entry.setdefault("yf", entry["ticker"])
    entry["state"] = entry["verdict"]          # keep the STRUCTURED state in sync (FNF stale-state bug 2026-07-04)
    entry["asof"] = datetime.date.today().isoformat()   # last-sweep stamp — staleness audits query this
                                               # instead of regexing dates out of conviction text (2026-07-16)
    explicit_stage = "stage" in entry          # did the caller assert a stage (e.g. ADJUDICATED post-court)?
    d = json.loads(LEDGER.read_text())
    for i, n in enumerate(d["names"]):
        if n["ticker"] == entry["ticker"]:
            merged = {**n, **entry}                       # merge-update
            if not explicit_stage:                        # PRESERVE the existing stage on update (don't downgrade
                merged["stage"] = n.get("stage", "SCREENED")  # an ADJUDICATED name to SCREENED on a re-score)
            d["names"][i] = merged
            LEDGER.write_text(json.dumps(d, indent=2, ensure_ascii=False))
            _regen()
            return "updated"
    entry.setdefault("stage", "SCREENED")      # NEW name: truthful default — only ADJUDICATED once DD/court is done
    d["names"].append(entry)
    LEDGER.write_text(json.dumps(d, indent=2, ensure_ascii=False))
    _regen()
    return "added"


def _regen():
    """Refresh the thesis-index page so the 'theses' tab reflects the change immediately."""
    try:
        from desk.thesis_index import main as _ti
        _ti()
    except Exception:
        pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ticker")
    ap.add_argument("--name", required=True)
    ap.add_argument("--sleeve", required=True)
    ap.add_argument("--verdict", required=True, choices=sorted(VERDICTS))
    ap.add_argument("--thesis", required=True)
    ap.add_argument("--entry", default="")
    ap.add_argument("--source", required=True)
    ap.add_argument("--conviction", default="")
    ap.add_argument("--yf", default=None)
    ap.add_argument("--alert-below", type=float, default=None, dest="alert_below")
    a = ap.parse_args()
    e = {"ticker": a.ticker, "yf": a.yf or a.ticker, "name": a.name, "sleeve": a.sleeve,
         "verdict": a.verdict, "conviction": a.conviction, "thesis": a.thesis,
         "entry": a.entry, "source": a.source}
    if a.alert_below is not None:
        e["alert_below"] = a.alert_below
    print(f"[{upsert(e)}] {a.ticker} -> {a.verdict} ({a.sleeve}) in the Watchlist book")


if __name__ == "__main__":
    main()
