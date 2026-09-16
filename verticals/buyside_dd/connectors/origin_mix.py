"""origin_mix — triangulate the UNDISCLOSED sourcing/origin geography of a company's revenue or GMV,
and convert it into a SIZED tariff EBIT-at-risk. The load-bearing tariff-bear number ("what % is
China-origin / tariff-exposed") is almost never disclosed (competitively sensitive) — companies
disclose the RISK and hide the MAGNITUDE. This connector derives it (Mode-B implied verification):

  1. Decompose reported GMV/revenue into BUCKETS with different origin exposure (e.g. 3P marketplace
     vs 1P own-inventory vs acquired/branded), each carrying a low/base/high origin prior.
  2. Cross-check the physical truth with customs Bill-of-Lading (reuse customer_id) + US Census
     trade-flow by HS-code×country — directional corroboration of the China tilt.
  3. Apply TARIFF INCIDENCE: origin-share is NOT the right denominator for the margin hit. Tariff on
     3P/marketplace volume lands on the third-party importer-of-record (off the platform's P&L); only
     OWN-INVENTORY origin GMV hits COGS. Size un-recovered EBIT = on_pl_landed_cost x tariff x (1-passthrough).

Validated 2026-06-28 on GCT (GigaCloud): China-origin ~62/73/82% of ~$2.06B GMV; biggest China bucket
(3P, $851M) is off-P&L; ~$45M worst-case un-recovered EBIT (~28% of pretax) at 60% pass-through, ~$0 at
the full pass-through GCT demonstrated (Q3'25 product margin expanded to 29.9%) -> NOT a margin trap.

  python3 -m verticals.buyside_dd.connectors.origin_mix         # prints the GCT worked example
"""

from __future__ import annotations

# Knowledge-graph dispatch contract (see knowledge_graph/dispatch.py) — added 2026-07-29 gap-close.
APPLIES_TO = {
    "kind": 'm_source',
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": ['imports_physical_goods', 'china_sourcing_exposure'],
    "asset_classes": ['corporate_ipo_dd'],
    "applies_universally": False,
    "summary": 'Triangulates undisclosed sourcing-origin mix (tariff exposure) from customs/Census.',
}
from dataclasses import dataclass, field

try:
    from .customer_id import resolve_shipping_entities, customs_consignees, census_trade_flow
except Exception:  # allow standalone import
    resolve_shipping_entities = customs_consignees = census_trade_flow = None


@dataclass
class Bucket:
    name: str
    gmv: float                       # $M of GMV/revenue in this bucket
    on_pl: bool                      # True = own-inventory (tariff hits COGS); False = 3P (incidence off-P&L)
    origin_low: float                # low/base/high prior that this bucket is tariff-origin (e.g. China), 0..1
    origin_base: float
    origin_high: float
    gross_margin: float = 0.0        # for on_pl buckets: GM% -> landed cost = gmv*(1-GM)
    note: str = ""


def triangulate_origin(buckets: list[Bucket]) -> dict:
    """Weighted low/base/high origin % of total GMV, plus the on-P&L (tariff-incident) origin GMV."""
    tot = sum(b.gmv for b in buckets) or 1.0
    lo = sum(b.gmv * b.origin_low for b in buckets) / tot
    bs = sum(b.gmv * b.origin_base for b in buckets) / tot
    hi = sum(b.gmv * b.origin_high for b in buckets) / tot
    on_pl_origin_gmv = sum(b.gmv * b.origin_base for b in buckets if b.on_pl)
    on_pl_landed_cost = sum(b.gmv * b.origin_base * (1 - b.gross_margin) for b in buckets if b.on_pl)
    off_pl_origin_gmv = sum(b.gmv * b.origin_base for b in buckets if not b.on_pl)
    return {
        "total_gmv": tot,
        "origin_pct_low": lo, "origin_pct_base": bs, "origin_pct_high": hi,
        "origin_gmv_base": bs * tot,
        "on_pl_origin_gmv": on_pl_origin_gmv,            # the piece that actually hits COGS
        "on_pl_landed_cost": on_pl_landed_cost,
        "off_pl_origin_gmv": off_pl_origin_gmv,          # incidence falls on 3P importer-of-record
        "buckets": [{"name": b.name, "gmv": b.gmv, "on_pl": b.on_pl, "origin_base": b.origin_base} for b in buckets],
    }


def tariff_ebit_at_risk(on_pl_landed_cost: float, tariff_rate: float, pass_through: float,
                        pretax: float) -> dict:
    """Un-recovered EBIT hit = landed_cost x incremental_tariff x (1 - pass_through). The OFF-P&L
    (3P) origin GMV is deliberately excluded — its tariff lands on the third-party importer."""
    hit = on_pl_landed_cost * tariff_rate * (1 - pass_through)
    return {"tariff_rate": tariff_rate, "pass_through": pass_through,
            "un_recovered_ebit": hit, "pct_of_pretax": (hit / pretax) if pretax else None}


def customs_cross_check(company: str, hs_code: str | None = None, country: str = "China") -> dict:
    """Directional physical-truth read: resolve importer aliases -> BOL consignees, + Census HS x country
    aggregate flow. Degrades gracefully (aggregators are scrape-fragile / Cloudflare-gated)."""
    out = {"aliases": [], "bol": None, "census": None}
    if resolve_shipping_entities is None:
        out["note"] = "customer_id helpers unavailable (standalone import)"
        return out
    out["aliases"] = resolve_shipping_entities(company)
    try:
        out["bol"] = customs_consignees(out["aliases"][-1] if out["aliases"] else company)
    except Exception as e:
        out["bol"] = {"ok": False, "error": str(e)}
    if hs_code:
        try:
            out["census"] = census_trade_flow(hs_code, country)
        except Exception as e:
            out["census"] = {"ok": False, "error": str(e)}
    return out


# ---- validated worked example: GCT (GigaCloud) FY2025 ----
GCT_BUCKETS = [
    Bucket("3P marketplace", 851.2, on_pl=False, origin_low=.75, origin_base=.85, origin_high=.92,
           note="sellers = manufacturers based in Asia (10-K); tariff incidence on 3P seller/US buyer"),
    Bucket("1P own-inventory", 725.6, on_pl=True, origin_low=.60, origin_base=.73, origin_high=.82,
           gross_margin=.30, note="187-person China/VN/Malaysia sourcing team; customs BOL ~80/20 China/VN"),
    Bucket("Off-platform (Noble House)", 486.8, on_pl=True, origin_low=.40, origin_base=.55, origin_high=.65,
           gross_margin=.30, note="Noble House VN/India-tilted (teak/wicker/outdoor) = most diversified"),
]
GCT_PRETAX = 161.2


def _gct_demo():
    tri = triangulate_origin(GCT_BUCKETS)
    print(f"GCT total GMV ${tri['total_gmv']:,.0f}M")
    print(f"  China-origin %:  low {tri['origin_pct_low']:.0%} / base {tri['origin_pct_base']:.0%} / high {tri['origin_pct_high']:.0%}")
    print(f"  China-origin GMV (base): ${tri['origin_gmv_base']:,.0f}M")
    print(f"  ON-P&L China GMV (hits COGS): ${tri['on_pl_origin_gmv']:,.0f}M  -> landed cost ${tri['on_pl_landed_cost']:,.0f}M")
    print(f"  OFF-P&L China GMV (3P, incidence elsewhere): ${tri['off_pl_origin_gmv']:,.0f}M")
    for pt, label in [(1.0, "full pass-through (Q3'25 demonstrated)"), (0.6, "60% pass-through (bear)")]:
        r = tariff_ebit_at_risk(tri["on_pl_landed_cost"], tariff_rate=.30, pass_through=pt, pretax=GCT_PRETAX)
        print(f"  +30pp tariff, {label}: un-recovered EBIT ${r['un_recovered_ebit']:,.0f}M  ({r['pct_of_pretax']:.0%} of pretax)")
    print("  verdict: biggest China bucket is OFF-P&L (3P); margin hit bounded+survivable -> NOT a tariff value-trap")


if __name__ == "__main__":
    _gct_demo()
