"""catalyst_watch — dated, named catalysts the Desk tracks across the book. Surfaces a catalyst as it
APPROACHES (within the window) and flags overdue ones, so a dated tell (a product launch, a panel vote,
a tariff date, an earnings binary) can't slip by unwatched. Each catalyst names WHAT to watch and the
thesis it resolves. READ-ONLY.

  python3 -m desk.catalyst_watch          # imminent/overdue catalysts -> Desk signals
"""
from __future__ import annotations
import datetime

# date = the catalyst date (best estimate); window_days = surface it this many days ahead
CATALYSTS = [
    {"ticker": "KER.PA", "date": "2026-10-21", "catalyst": "Q3-2026 print: Gucci comp inflection under Demna (H2 sell-through)",
     "thesis": "WATCH-ONLY turnaround (two-stage verdict): not AVOID (BBB+/2.2x survivable), not buy (62x trough, no cushion). FLIP to BUY only if Gucci comp inflects ~flat-or-positive + self-help cash shows, WHILE stock still <~EUR268 (before re-rate)",
     "watch": "Gucci comparable revenue (does Q1 NA +8% generalize to comp-flat?) + EUR1bn inventory cut / store closures in FCF-margin; entry only sub-268"},
    {"ticker": "INSP", "date": "2026-09-15", "catalyst": "AMA CPT panel (Cat-I code decision)",
     "thesis": "the binary — a Cat-I code drives a Jan-2028 re-rate; the 2025 collapse was the lost code",
     "watch": "panel outcome; Cat-I = re-rate, status-quo = bear extends"},
    {"ticker": "EOLS", "date": "2026-09-29", "catalyst": "Section 232 Korea tariff EFFECTIVE (15% Jeuveau)",
     "thesis": "tariff exposure vs the inventory pre-buy/mitigation; the year-end 'update' tell",
     "watch": "Q3 inventory (Sept-30) for pre-buy; does the 'longer-term solution' get a noun"},
    {"ticker": "BAH", "date": "2026-07-28", "catalyst": "FY27 Q1 print (quarter ended Jun-2026)",
     "thesis": "is the federal-cuts/Civil deterioration troughing (held position, down ~25%)?",
     "watch": "funded backlog + quarterly book-to-bill turning positive = troughing confirmed"},
    {"ticker": "SILICON2", "date": "2026-08-07", "catalyst": "2Q26 print — the AVOID/short INVERT-trigger",
     "thesis": "currently AVOID/short-bias (thin-margin K-beauty redistribution wholesaler, parabola rolled over, disintermediation risk)",
     "watch": "INVERT to LONG only if YoY re-accel >45% + Europe inflects + OM recovers >17%; else AVOID holds. Reaching ₩18-22k band = 2nd-leg-down target reached (cover/informational, NOT a buy). Own COSMECCA (the ODM) not SILICON2 (the reseller) for K-beauty"},
    {"ticker": "COSMECCA", "date": "2026-08-15", "catalyst": "Q2 print",
     "thesis": "re-rate (OPM 13-14% + Englewood>=15% + Korea>30%) vs unwind (Korea->12%, OPM<12%)",
     "watch": "OPM + segment mix; RPT note + clean FCF (both were UNVERIFIABLE pre-size)"},
    {"ticker": "BOOK", "date": "2026-12-31", "catalyst": "Tax-loss-harvest deadline (2026 gain needs 2026 losses)",
     "thesis": "the $2.4M harvest goal — losses must realize by year-end (no carryback)",
     "watch": "harvest_ledger projection vs $2.4M goal; deploy/accept-tax decision by ~Oct"},
    {"ticker": "TBCG.L", "date": "2026-08-15", "catalyst": "Q2 print + geopol de-risk watch (MEGOBARI Senate / Moody's outlook / EU-US thaw)",
     "thesis": "verified STARTER — funding moat audited, geopol natural-experiment passed; WATCH is the de-risk add-path, not earnings",
     "watch": "add toward ~3% on: MEGOBARI dies in Senate | Moody's NEG->STABLE | EU-US thaw | non-tail dislocation <=GBp4000. TAIL-KILL (EXIT not add): any Georgian bank named OFAC / USD-correspondent curtailment"},
    {"ticker": "UKRAIN-StepUp-B", "date": "2026-12-31", "catalyst": "Ukraine ceasefire-durability / security-guarantee watch (upsize variable)",
     "thesis": "convexity sleeve (~2-4%) in the restructured sovereign Step-Up B bond; the binary is ceasefire-hold, not a print",
     "watch": "UPSIZE on a credible security guarantee + EU-accession track. TAIL-KILL: ceasefire collapse -> bond to ~30c floor, do NOT average into a 2nd restructuring. Verify FIRST: live IBKR quote contract 726401416 + A-vs-B ISIN + retail min denomination"},
    {"ticker": "REPL", "date": "2026-07-30", "catalyst": "FDA ODAC advisory vote (late-July, exact date UNVERIFIED) -> PDUFA goal Aug-2; RP1+nivolumab accelerated approval, advanced melanoma",
     "thesis": "WATCH-ONLY defined-risk binary — NO pre-position. THIRD BLA attempt (2 prior CRLs: Jul-22-2025 + Apr-2026); accelerated approval on SINGLE-ARM IGNYTE; the CRL objection (single-arm adequacy + contribution-of-components) is unchanged. Fairly priced (EV~=$10 spot; IV~328% => ~90% implied move; targets $1-$17). Honesty-axis CLEAN (going concern + CRL history disclosed). Thesis+court carried: desk/reports/REPL_ADCOM_THESIS_20260724.html; edge REPL.json",
     "watch": "LEADING TRIPWIRE = FDA briefing documents posted ~2 biz days pre-AdCom (agency's own read, moves stock before the vote). Branch YES(approve): don't chase the gap, re-diligence ramp for a lower re-entry. Branch NO(CRL#3): don't catch the knife, ~$1.5-3 floor + distressed raise (observed Apr-2026 crash $5.90->$1.70). Verify exact ODAC date + voting question when Fed Register posts"},
]


def _load_antibook():
    """Anti-book turnaround watches (triage WATCH names) — data-driven from desk/data/antibook_watch.json."""
    import json, os
    p = os.path.join(os.path.dirname(__file__), "data", "antibook_watch.json")
    if not os.path.exists(p):
        return []
    try:
        return [{**c, "antibook": True} for c in json.load(open(p))]
    except Exception:
        return []


def snapshot(today=None, window=60):
    today = today or datetime.date.today()
    rows = []
    for c in CATALYSTS + _load_antibook():
        d = datetime.date.fromisoformat(c["date"])
        days = (d - today).days
        rows.append({**c, "days": days})
    rows.sort(key=lambda r: r["days"])
    return rows, today


def main(window=60):
    rows, today = snapshot(window=window)
    print(f"=== CATALYST WATCH {today} (window {window}d) ===")
    for r in rows:
        d = r["days"]
        if -10 <= d <= window:                 # imminent or just-passed -> a Desk signal
            sev = "HIGH" if -3 <= d <= 21 else "MED"
            tag = f"in {d}d" if d >= 0 else f"{-d}d AGO (resolve)"
            print(f"DETFIRE|catalyst|{r['ticker']}|{sev}|{r['catalyst']} ({tag}) — {r['watch']}")
        print(f"  {r['ticker']:9} {r['date']}  ({r['days']:+4d}d)  {r['catalyst']}")


if __name__ == "__main__":
    main()
