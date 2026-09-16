"""run_virality_scan — re-runnable cosmeceutical VIRALITY RADAR. Seeds the current viral-brand list
(refreshed by the market-researcher WebSearch scan -> VIRALITY_RADAR.md), maps each to its PUBLIC
vehicle via the beauty_virality connector, ranks by tradeable signal, and logs.

THE EDGE: viral TikTok/influencer product -> the PUBLIC manufacturer/brand earnings print ~1-2 quarters
later. Most viral K-beauty brands are PRIVATE, so the trade is the listed beneficiary (brand-owner | ODM
| distributor) BEFORE the market connects them — and only where it's not already discovered/priced.

REFRESH CADENCE: re-run the market-researcher virality scan ~monthly (the gated TikTok/Reddit/Sephora
APIs mean detection is WebSearch-driven), update CURRENT_VIRAL below, re-run this. The brand->vehicle
mapping (beauty_virality.BRAND_TO_VEHICLE) is the durable part; only the viral SET rotates.
"""
from __future__ import annotations
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3]))  # signalos repo root
from verticals.buyside_dd.connectors.beauty_virality import map_to_vehicle

LOG = HERE / "virality_log.jsonl"

# Current viral set (as of the 2026-06-29 weekly scan -> VIRALITY_RADAR.md). momentum: ACCEL / PEAK / FADE.
CURRENT_VIRAL = {
    # --- NEW this week ---
    "Dr. Melaxin":     {"ingredient": "Peel Shot Glow rice ampoule / slow-aging", "momentum": "ACCEL", "influencer": "#1 TikTok-Shop beauty brand ($46.3M Q1'26); paid-creator engine"},
    "Mixsoon":         {"ingredient": "PDRN collagen tinted moisturizer (skin-first makeup)", "momentum": "ACCEL", "influencer": "TikTok glass-skin; Amazon debut"},
    "Medik8":          {"ingredient": "Exo-PDRN Prismatic+ (triple exosome + PDRN)", "momentum": "ACCEL", "influencer": "derm/editor 7-day-revive launch"},
    # --- carry-over ---
    "Anua":            {"ingredient": "heartleaf PDRN / zero-cast SPF", "momentum": "ACCEL", "influencer": "DermDoctor, skinfluencers; Ulta rollout"},
    "BYOMA":           {"ingredient": "barrier / ceramide + SPF", "momentum": "ACCEL", "influencer": "TikTok affordable-barrier"},
    "Biodance":        {"ingredient": "bio-collagen real deep mask", "momentum": "ACCEL", "influencer": "TikTok overnight-mask ritual"},
    "Beauty of Joseon":{"ingredient": "Relief Sun rice SPF (18.5M units) + Revive fermented-retinol", "momentum": "ACCEL", "influencer": "Sephora; derm sunscreen roundups"},
    "Tirtir":          {"ingredient": "Mask Fit cushion (550% color-cosmetics growth)", "momentum": "ACCEL", "influencer": "Black beauty creators; shade-range"},
    "Naturium":        {"ingredient": "actives-forward, multi", "momentum": "ACCEL", "influencer": "Bretman Rock"},
    "Rhode":           {"ingredient": "Caffeine Reset (sculpt/tighten) + peptide lip", "momentum": "ACCEL", "influencer": "Hailey Bieber"},
    "Skin1004":        {"ingredient": "centella ampoule", "momentum": "ACCEL", "influencer": "TikTok centella"},
    "Rejuran":         {"ingredient": "PDRN 'salmon sperm'", "momentum": "ACCEL", "influencer": "Kim K / Kardashian"},
    "Medicube":        {"ingredient": "PDRN + AGE-R device", "momentum": "PEAK", "influencer": "Coachella; viral PDRN"},
    "Glow Recipe":     {"ingredient": "dewy / fruit actives", "momentum": "PEAK", "influencer": "TikTok"},
    # --- FADE (short-side latency tells) ---
    "Sol de Janeiro":  {"ingredient": "fragrance mist / jelly balm", "momentum": "FADE", "influencer": "founder exit; mist slowdown"},
    "Drunk Elephant":  {"ingredient": "legacy actives", "momentum": "FADE", "influencer": "post-peak"},
}

_VELO = {"ACCEL": 2, "PEAK": 1, "FADE": -1}


def run():
    asof = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    rows = []
    for brand, meta in CURRENT_VIRAL.items():
        v = map_to_vehicle(brand)
        rows.append({**meta, **v})
    # rank: investable (has ticker) first, then ACCEL>PEAK>FADE, then confidence
    conf_rank = {"HIGH": 3, "MED": 2, "LOW": 1, "NONE": 0}
    rows.sort(key=lambda r: (r.get("ticker") is not None, _VELO.get(r["momentum"], 0),
                             conf_rank.get(r.get("conf", "NONE"), 0)), reverse=True)

    print(f"=== COSMECEUTICAL VIRALITY RADAR {asof} ===")
    print("  viral SKU -> PUBLIC beneficiary (latency: virality leads the print ~1-2 quarters)")
    print(f"  {'BRAND':<17} {'MOM':<6} {'VEHICLE':<22} {'TYPE':<12} {'CONF':<5} INGREDIENT / DRIVER")
    for r in rows:
        veh = f"{r.get('ticker') or '—'} {r['name'][:16]}" if r.get("ticker") else "PRIVATE/unmapped"
        flag = "  <<<" if r.get("ticker") and r["momentum"] == "ACCEL" and r.get("conf") in ("HIGH", "MED") else ""
        print(f"  {r['brand']:<17} {r['momentum']:<6} {veh:<22} {r['type']:<12} {r.get('conf','-'):<5} "
              f"{r['ingredient']}{flag}")

    investable = [r for r in rows if r.get("ticker")]
    private = [r for r in rows if not r.get("ticker")]
    print(f"\n  STRONGEST (ACCEL + clean vehicle + latency):")
    for r in [r for r in investable if r["momentum"] == "ACCEL" and r.get("conf") in ("HIGH", "MED")][:5]:
        print(f"    {r['brand']} -> {r['ticker']} ({r['name']}) [{r['type']}] — {r.get('note','')[:80]}")
    print(f"\n  PRIVATE / no-vehicle (IPO-or-M&A watch): "
          + ", ".join(sorted({r['brand'] for r in private})))
    print("  influencers (upstream): DermDoctor(Muneeb Shah), Hyram, Shereene Idriss, Whitney Bowe, "
          "Caroline Hirons + Kim K(PDRN)/Hailey Bieber(Rhode)/Bretman Rock(Naturium)")
    print("  NB: Silicon2 carries many of these (distributor read) but our DD = AVOID (decel); APR(Medicube) "
          "= DISCOVERED, latency harvested. Strongest fresh = Anua/BYOMA->Cosmecca.")

    with open(LOG, "a") as f:
        f.write(json.dumps({"asof": asof, "rows": rows}, ensure_ascii=False, default=str) + "\n")
    print(f"\n[-> {LOG.name}]  Refresh: re-run the market-researcher virality scan (~monthly), update CURRENT_VIRAL.")


if __name__ == "__main__":
    run()
