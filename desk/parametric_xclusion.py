"""parametric_xclusion — keeps your IBKR book and the Parametric SMA MUTUALLY EXCLUSIVE so the two
harvesting programs never trigger cross-account wash sales (§1091 aggregates across all accounts you
control, and Parametric is blind to your IBKR custodian). Parametric holds an OPTIMIZED ~314-name subset
that DRIFTS monthly, so a name disjoint today can be added next month -> a silent collision. This watch
reads the live Parametric positions and flags any overlap with your book, and emits the restriction list
to hand Parametric (the airtight fix: tell the SMA to never hold your names).

  python3 -m desk.parametric_xclusion            # drift check -> DETFIRE on overlaps (Desk-ingested)
  python3 -m desk.parametric_xclusion restrict   # print the restriction list to send Parametric

Emits DETFIRE| lines (reuses the detector_scan extractor). READ-ONLY.
"""
from __future__ import annotations
import os, sys, sqlite3
from . import book_universe as BU

MSPRIME_DB = os.environ.get("MSPRIME_DB", "/Users/ajay/msprime/app/data/msprime.db")

# securities that are "substantially identical" beyond the exact ticker — expand the restriction list
SHARE_CLASS = {"GOOGL": ["GOOG"], "GOOG": ["GOOGL"], "FOX": ["FOXA"], "FOXA": ["FOX"],
               "BRK.B": ["BRK.A"], "BRK.A": ["BRK.B"]}


def parametric_holdings(db=MSPRIME_DB) -> set[str]:
    if not os.path.exists(db):
        return set()
    con = sqlite3.connect(db)
    try:
        d = con.execute("SELECT MAX(reporting_date) FROM positions WHERE reporting_date LIKE '2_%-%-%' AND length(reporting_date)=10").fetchone()[0]
        rows = con.execute("SELECT DISTINCT symbol FROM positions WHERE reporting_date=? AND symbol!='USD'", (d,)).fetchall()
        return {r[0] for r in rows}, d
    finally:
        con.close()


def our_universe() -> set[str]:
    """The names you own / intend to own / harvest in IBKR (book_universe + held)."""
    return set(BU.BOOK.keys())


def overlaps():
    held, asof = parametric_holdings()
    ours = our_universe()
    direct = sorted(ours & held)
    # share-class adjacency: if Parametric holds GOOG and you hold GOOGL, that's an overlap too
    adj = []
    for t in ours:
        for sc in SHARE_CLASS.get(t, []):
            if sc in held:
                adj.append((t, sc))
    return direct, adj, asof, held


def restriction_list() -> list[str]:
    out = set(our_universe())
    for t in list(out):
        out.update(SHARE_CLASS.get(t, []))
    return sorted(out)


def main():
    direct, adj, asof, held = overlaps()
    print(f"# parametric_xclusion: Parametric={len(held)} holdings @ {asof}; book={len(our_universe())} names")
    for t in direct:
        print(f"DETFIRE|parametric_overlap|{t}|HIGH|Parametric SMA now holds {t} (drift) — RESTRICT it at Parametric or don't harvest {t} in IBKR for 30d (wash-sale)")
    for t, sc in adj:
        print(f"DETFIRE|parametric_overlap|{t}|HIGH|share-class collision: you hold {t}, Parametric holds {sc} (substantially identical) — restrict both")
    if not direct and not adj:
        print("# books mutually exclusive — no overlap (no action)")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "restrict":
        rl = restriction_list()
        print(f"# Parametric restriction list ({len(rl)} tickers) — instruct the SMA to NEVER hold these:")
        print(", ".join(rl))
    else:
        main()
