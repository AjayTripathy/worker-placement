"""import_nowcast — Census monthly trade data as a P&L nowcast for import-driven smallcaps.

The office thesis's data leg: free structured government data x companies too
small for any desk to staff the join. Census international-trade monthly
imports (by HS code x country, ~5-week lag) lead the quarterly prints of
import-driven names by weeks.

MAP: name -> [(HS code, country_code, label)]. v1: GCT (GigaCloud — furniture
marketplace; HS 9403 ex-China + ex-Vietnam ~= its container flow). Extend as
the pond surfaces importers (the IPW/ONON class).

Weekly check: when a NEW month lands, append to the series, alert with the
MoM/YoY read and the name's next print date. NOWCAST INPUT, not a verdict —
aggregate imports are the market, not the company; courts grade the mapping.

    python3 -m desk.import_nowcast        # registered weekly
READ-ONLY.
"""
from __future__ import annotations
import json, urllib.request, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "desk" / "data" / "import_nowcast.json"
KEY = Path.home() / ".census_key"

MAP = {
    "GCT": {"series": [("9403", "5700", "furniture ex-China"), ("9403", "5520", "furniture ex-Vietnam")],
            "next_print": "~early Aug 2026 (Q2)",
            "note": "GigaCloud GMV ~ containerized furniture flow; watch the ex-Vietnam mix shift (tariff rerouting)"},
    # Added 2026-07-11 (trade-data sweep); CORRECTED 2026-07-11 from FY26 10-K PRIMARY source.
    # VERIFIED figures (10-K filed 2026-04-17): imported casegoods+upholstery = ~60% of net sales
    # (NOT 71%); Vietnam = 87% of import PURCHASES / China = 5% (NOT 76%/13%). Top-5 VN suppliers = 69%.
    # SECTOR-PROXY CAVEAT (do NOT read as a Hooker print-caller): Hooker is ~0.5-0.7% of the national
    # HS9403+9401 VN+CN cell; the biggest in-window move (China import cliff, -40/-50% YoY from May-2025)
    # is OTHER importers' tariff rerouting, not Hooker demand. National flow explains only the low-freq
    # SECTOR direction, not Hooker's quarter-specific beat/miss. A TRUE Hooker nowcast needs a
    # consignee-resolved bill-of-lading pull (aliases: Hooker Casegoods/Bradington-Young/Sam Moore/etc).
    # Realistic landing->sale lead ~0-1 quarter (inventory turns ~4.4x). Post-divestiture: only Hooker
    # Branded imports; Domestic Upholstery is domestically MANUFACTURED (imports components only).
    "HOFT": {"series": [("9403", "5520", "casegoods Vietnam"), ("9401", "5520", "seating Vietnam"),
                        ("9403", "5700", "casegoods China"), ("9401", "5700", "seating China")],
             "next_print": "~early Sep 2026 (FQ2 Aug-end)",
             "note": "Hooker Furnishings — SECTOR-DEMAND PROXY ONLY (~0.6% of the national cell). ~60% imported, VN 87%/CN 5%. Not a company print-caller w/o BOL consignee resolution."},
    # Added 2026-07-11 (trade-data WIDE sweep): the other 3 top import-nowcast finds. CTY-code lesson:
    # 5520=VIETNAM, 5700=CHINA — resolve codes via CTY_CODE=* before trusting a single cell (5880 is JAPAN,
    # not Thailand as an earlier guess had it).
    "CROX": {"series": [("6402", "5520", "clogs Vietnam"), ("6402", "5700", "clogs China"),
                        ("6402", "5600", "clogs Indonesia")],
             "next_print": "~late Oct 2026 (Q3)",
             "note": "Crocs — CLEANEST signature in the sweep: one product (molded clogs), one material, one HS4 "
                     "(6402), Vietnam-led. SCOPE TO CROCS-BRAND — exclude HEYDUDE (~18% rev, China textile 6404) "
                     "which is a separable noisier series. Readability ~0.85."},
    "FLXS": {"series": [("9401", "5520", "upholstery seats Vietnam"), ("9401", "5700", "seats China")],
             "next_print": "~late Aug 2026 (FQ4 Jun-end)",
             "note": "Flexsteel — import leg 'primarily Vietnam' upholstered seating (HS 9401). CAVEAT: captive "
                     "Mexico plants ship US by TRUCK/rail, OUTSIDE the ocean-import series — the cell reads only "
                     "the imported leg, not domestic/Mexico output. Readability ~0.70."},
    "WEYS": {"series": [("6403", "5700", "dress shoes China"), ("6403", "5330", "dress shoes India")],
             "next_print": "~early Nov 2026 (Q3)",
             "note": "Weyco Group — ~100% importer, ONE category (leather dress shoes, HS 6403); disclosed TWO "
                     "China suppliers each >10% + India (CTY 5330, verified 2026-07-11 — 5310 was wrong). "
                     "Small-cap sleeper, thin coverage = the alt-data edge. Readability ~0.75."},
    # ALTERNATES if the top-4 saturate: DECK (UGG 6403 + HOKA 6404 as TWO series, VN/Indonesia; big-cap);
    # CULP (upholstery-fabric basket 5407/630x, CN/VN/Turkey; censor ~33% non-US output; readability ~0.4).
}

def _notify(msg):
    try:
        from desk.gauntlet_sentinel import _notify as n; n(msg)
    except Exception:
        print("[import_nowcast] NOTIFY:", msg)

def _pull(hs, cty, key):
    url = (f"https://api.census.gov/data/timeseries/intltrade/imports/hs?get=GEN_VAL_MO,CTY_NAME"
           f"&I_COMMODITY={hs}&time=from+2024-01&CTY_CODE={cty}&key={key}")
    rows = json.loads(urllib.request.urlopen(url, timeout=40).read())
    hdr = rows[0]
    ti, vi = hdr.index("time"), hdr.index("GEN_VAL_MO")
    return sorted((r[ti], int(r[vi])) for r in rows[1:])

def main():
    key = KEY.read_text().strip()
    st = json.loads(STATE.read_text()) if STATE.exists() else {"names": {}}
    alerts = []
    for name, cfg in MAP.items():
        rec = st["names"].setdefault(name, {"series": {}, "last_month": ""})
        latest_seen = rec["last_month"]
        newest = ""
        for hs, cty, label in cfg["series"]:
            try:
                data = _pull(hs, cty, key)
            except Exception as e:
                print(f"[import_nowcast] {name}/{label} pull failed: {e}"); continue
            rec["series"][label] = dict(data)
            newest = max(newest, data[-1][0])
        if newest and newest > latest_seen:
            rec["last_month"] = newest
            tot = sum(s.get(newest, 0) for s in rec["series"].values())
            prev_m = f"{newest[:4]}-{int(newest[5:]) - 1:02d}" if newest[5:] != "01" else f"{int(newest[:4]) - 1}-12"
            yoy_m = f"{int(newest[:4]) - 1}{newest[4:]}"
            tot_prev = sum(s.get(prev_m, 0) for s in rec["series"].values())
            tot_yoy = sum(s.get(yoy_m, 0) for s in rec["series"].values())
            mom = (tot / tot_prev - 1) * 100 if tot_prev else 0
            yoy = (tot / tot_yoy - 1) * 100 if tot_yoy else 0
            # plain-language two-axis read (the verdict-email ritual applies to data alerts too):
            seq = "rebounding" if mom > 5 else ("falling" if mom < -5 else "flat")
            ann = "still SHRINKING vs last year" if yoy < -3 else ("GROWING vs last year" if yoy > 3 else "roughly flat vs last year")
            alerts.append(f"IMPORT NOWCAST {name}: {newest} imports = ${tot/1e6:,.0f}M — sequentially {seq} "
                          f"({mom:+.0f}% MoM) but {ann} ({yoy:+.0f}% YoY). "
                          f"WHAT IT MEANS: the sequential axis reads demand momentum; the annual axis reads the channel's size — "
                          f"the print question is share-of-channel. Feeds the {cfg['next_print']} print. {cfg['note']}")
    STATE.write_text(json.dumps(st, indent=1))
    if alerts:
        _notify(" | ".join(alerts)[:900])
    print(f"[import_nowcast] {len(MAP)} names, {len(alerts)} new-month alerts" + (f": {alerts}" if alerts else ""))

if __name__ == "__main__":
    main()
