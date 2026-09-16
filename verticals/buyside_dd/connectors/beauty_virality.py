"""beauty_virality — detect cosmeceuticals going viral and map each to the PUBLIC vehicle that profits.

THE EDGE (signal-to-price latency): a product going viral on TikTok/influencers shows up in a PUBLIC
company's earnings print 1-2 quarters LATER. Most viral K-beauty/indie brands are PRIVATE, so the
investable move is the mapping layer below — viral brand -> brand-owner (if listed) | ODM that makes it
(the whale-ID/openFDA route) | distributor | retailer. The market doesn't connect "Anua sunscreen is
viral" to "Cosmecca manufactures it" until the ODM prints. That gap is the trade.

SOURCE LADDER (reachability tested from this egress 2026-06-26):
  REACHABLE: Amazon Movers&Shakers Beauty (demand-velocity, the rank-RISING confirm) + Ulta + WebSearch
             (the agent-driven influencer/press scan) + openFDA NDC (the ODM whale-ID resolver).
  GATED:     TikTok Creative Center (40101 no-permission -> needs Research API/token), Reddit (403),
             Sephora (403), Google Trends (gated). These are the PAID-API escalation tier.

So the connector does the AUTOMATABLE core (Amazon-movers demand velocity + the brand->vehicle map +
openFDA ODM resolution); the upstream INFLUENCER signal is captured by an agent WebSearch scan
(run_virality_scan) that feeds the same mapping. Both share BRAND_TO_VEHICLE.
"""

from __future__ import annotations

# Knowledge-graph dispatch contract (see knowledge_graph/dispatch.py) — added 2026-07-29 gap-close.
APPLIES_TO = {
    "kind": 'm_source',
    "sic_codes": [2844],
    "sic_prefixes": ['284', '512'],
    "issuer_features": ['consumer_beauty_brand', 'consumer_virality_claim'],
    "asset_classes": ['corporate_ipo_dd'],
    "applies_universally": False,
    "summary": 'Viral cosmeceutical -> public-vehicle mapper (brand/ODM/distributor). Latency edge: virality leads the print.',
}
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # signalos repo root

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
H = {"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"}

# --- THE CORE IP: viral beauty brand -> public investment vehicle ----------------------------------
# type: brand_owner (the listed brand parent) | odm (the contract manufacturer) | distributor | retailer
# Mark conf=LOW where the ODM link is inferred not openFDA-confirmed. Extend as the brain learns each.
BRAND_TO_VEHICLE = {
    # --- brand is PUBLIC (or owned by a listed parent) — the cleanest map ---
    "medicube":          {"type": "brand_owner", "ticker": "278470.KS", "name": "APR Corp", "conf": "HIGH",
                          "note": "Medicube + AGE-R device; APR is the listed parent. NB: APR maximally DISCOVERED (watch/fade)."},
    "cosrx":             {"type": "brand_owner", "ticker": "090430.KS", "name": "Amorepacific", "conf": "HIGH",
                          "note": "Amorepacific acquired COSRX (snail mucin)."},
    "laneige":           {"type": "brand_owner", "ticker": "090430.KS", "name": "Amorepacific", "conf": "HIGH"},
    "sulwhasoo":         {"type": "brand_owner", "ticker": "090430.KS", "name": "Amorepacific", "conf": "HIGH"},
    "innisfree":         {"type": "brand_owner", "ticker": "090430.KS", "name": "Amorepacific", "conf": "HIGH"},
    "cerave":            {"type": "brand_owner", "ticker": "OR.PA",     "name": "L'Oreal", "conf": "HIGH"},
    "la roche-posay":    {"type": "brand_owner", "ticker": "OR.PA",     "name": "L'Oreal", "conf": "HIGH"},
    "skinceuticals":     {"type": "brand_owner", "ticker": "OR.PA",     "name": "L'Oreal", "conf": "HIGH"},
    "vichy":             {"type": "brand_owner", "ticker": "OR.PA",     "name": "L'Oreal", "conf": "HIGH"},
    "rhode":             {"type": "brand_owner", "ticker": "ELF",       "name": "e.l.f. Beauty", "conf": "HIGH",
                          "note": "ELF acquired Rhode (Hailey Bieber) 2025."},
    "naturium":          {"type": "brand_owner", "ticker": "ELF",       "name": "e.l.f. Beauty", "conf": "HIGH"},
    "e.l.f.":            {"type": "brand_owner", "ticker": "ELF",       "name": "e.l.f. Beauty", "conf": "HIGH"},
    "the ordinary":      {"type": "brand_owner", "ticker": "EL",        "name": "Estee Lauder (Deciem)", "conf": "HIGH"},
    "deciem":            {"type": "brand_owner", "ticker": "EL",        "name": "Estee Lauder", "conf": "HIGH"},
    "drunk elephant":    {"type": "brand_owner", "ticker": "4911.T",    "name": "Shiseido", "conf": "HIGH"},
    "eucerin":           {"type": "brand_owner", "ticker": "BEI.DE",    "name": "Beiersdorf", "conf": "HIGH"},
    "aquaphor":          {"type": "brand_owner", "ticker": "BEI.DE",    "name": "Beiersdorf", "conf": "HIGH"},
    "byoma":             {"type": "odm",         "ticker": "241710.KQ", "name": "Cosmecca Korea", "conf": "MED",
                          "note": "Englewood Lab (Cosmecca US sub) confirmed mfr of BYOMA SPF via openFDA NDC."},
    "anua":              {"type": "odm",         "ticker": "241710.KQ", "name": "Cosmecca Korea", "conf": "MED",
                          "note": "Englewood Lab confirmed mfr of Anua Zero-Cast SPF via openFDA (start 2025-04)."},
    # --- brand is PRIVATE; ODM is the play (resolve dynamically via openFDA when possible) ---
    "beauty of joseon":  {"type": "odm",         "ticker": None,        "name": "private brand — resolve ODM", "conf": "LOW",
                          "note": "Goodai Global (private). Resolve manufacturer via openFDA/customs; likely a KR ODM."},
    "tirtir":            {"type": "odm",         "ticker": None,        "name": "private — resolve ODM", "conf": "LOW"},
    "biodance":          {"type": "odm",         "ticker": None,        "name": "private — resolve ODM", "conf": "LOW"},
    "glow recipe":       {"type": "private",     "ticker": None,        "name": "private (VC-backed)", "conf": "HIGH"},
    "summer fridays":    {"type": "private",     "ticker": None,        "name": "private", "conf": "HIGH"},
    # --- new viral entrants 2026-06 weekly scan (all resolve PRIVATE — IPO/M&A watch, no listed vehicle) ---
    "melaxin":           {"type": "odm",         "ticker": None,        "name": "private brand (Brand501 Corp) — ODM BNB Korea UNVERIFIED-listing", "conf": "LOW",
                          "note": "#1 TikTok-Shop beauty brand Q1'26 (~$46.3M). Parent Brand501 PRIVATE; Amazon lists mfr 'BNB Korea Co' — NOT openFDA-confirmed, BNB listing status unverified = UNVERIFIABLE. Non-SPF so openFDA route can't cover."},
    "mixsoon":           {"type": "private",     "ticker": None,        "name": "private (Parket Inc.)", "conf": "HIGH",
                          "note": "PDRN Collagen Tinted Moisturizer = viral makeup debut 2026. Parent Parket Inc PRIVATE; ODM unconfirmed. IPO/M&A watch."},
    "medik8":            {"type": "private",     "ticker": None,        "name": "private (UK, PE-backed)", "conf": "HIGH",
                          "note": "Exo-PDRN Prismatic+ (triple-exosome + PDRN) viral 2026. Private/Inflexion-backed; no clean listed vehicle."},
    "sol de janeiro":    {"type": "brand_owner", "ticker": None,        "name": "L'Occitane (private since 2024 take-private)", "conf": "HIGH",
                          "note": "FADE tell: founder exit + mist slowdown + sales stall 2026. Owner L'Occitane delisted = no clean listed short."},
}

# brands whose virality flows to a DISTRIBUTOR/retailer regardless of brand owner
DISTRIBUTOR_HINT = {"257720.KQ": "Silicon2 (K-beauty export aggregator — many indie brands)"}

# --- CONSUMER (non-beauty) viral brand -> public vehicle. cat: food|bev|apparel|tech|home.
# Curated to DISTINCTIVE tokens (matcher strips spaces: key 'texas roadhouse' hits #texasroadhouse);
# ticker=None flags a PRIVATE/foreign viral brand (the gap = IPO/M&A watch). conf MED (hashtag heuristic).
CONSUMER_BRAND_TO_VEHICLE = {
    # food / beverage / restaurant
    "texas roadhouse": {"type": "consumer_brand", "cat": "food", "ticker": "TXRH", "name": "Texas Roadhouse", "conf": "MED"},
    "chipotle":     {"type": "consumer_brand", "cat": "food", "ticker": "CMG",  "name": "Chipotle", "conf": "MED"},
    "cava":         {"type": "consumer_brand", "cat": "food", "ticker": "CAVA", "name": "CAVA", "conf": "MED"},
    "wingstop":     {"type": "consumer_brand", "cat": "food", "ticker": "WING", "name": "Wingstop", "conf": "MED"},
    "dutch bros":   {"type": "consumer_brand", "cat": "food", "ticker": "BROS", "name": "Dutch Bros", "conf": "MED"},
    "shake shack":  {"type": "consumer_brand", "cat": "food", "ticker": "SHAK", "name": "Shake Shack", "conf": "MED"},
    "krispy kreme": {"type": "consumer_brand", "cat": "food", "ticker": "DNUT", "name": "Krispy Kreme", "conf": "MED"},
    "starbucks":    {"type": "consumer_brand", "cat": "food", "ticker": "SBUX", "name": "Starbucks", "conf": "MED"},
    "celsius":      {"type": "consumer_brand", "cat": "bev",  "ticker": "CELH", "name": "Celsius Holdings", "conf": "MED"},
    "alani":        {"type": "consumer_brand", "cat": "bev",  "ticker": "CELH", "name": "Celsius (Alani Nu)", "conf": "MED"},
    "poppi":        {"type": "consumer_brand", "cat": "bev",  "ticker": "PEP",  "name": "PepsiCo (Poppi)", "conf": "MED"},
    "monster energy": {"type": "consumer_brand", "cat": "bev", "ticker": "MNST", "name": "Monster Beverage", "conf": "MED"},
    # apparel / footwear
    "crocs":        {"type": "consumer_brand", "cat": "apparel", "ticker": "CROX", "name": "Crocs", "conf": "MED"},
    "lululemon":    {"type": "consumer_brand", "cat": "apparel", "ticker": "LULU", "name": "Lululemon", "conf": "MED"},
    "on running":   {"type": "consumer_brand", "cat": "apparel", "ticker": "ONON", "name": "On Holding", "conf": "MED"},
    "hoka":         {"type": "consumer_brand", "cat": "apparel", "ticker": "DECK", "name": "Deckers (Hoka)", "conf": "MED"},
    "birkenstock":  {"type": "consumer_brand", "cat": "apparel", "ticker": "BIRK", "name": "Birkenstock", "conf": "MED"},
    "skechers":     {"type": "consumer_brand", "cat": "apparel", "ticker": "SKX", "name": "Skechers", "conf": "MED"},
    "abercrombie":  {"type": "consumer_brand", "cat": "apparel", "ticker": "ANF", "name": "Abercrombie & Fitch", "conf": "MED"},
    "aerie":        {"type": "consumer_brand", "cat": "apparel", "ticker": "AEO", "name": "American Eagle (Aerie)", "conf": "MED"},
    "ralph lauren": {"type": "consumer_brand", "cat": "apparel", "ticker": "RL", "name": "Ralph Lauren", "conf": "MED"},
    "nike":         {"type": "consumer_brand", "cat": "apparel", "ticker": "NKE", "name": "Nike", "conf": "MED"},
    # tech / gadgets
    "gopro":        {"type": "consumer_brand", "cat": "tech", "ticker": "GPRO", "name": "GoPro", "conf": "MED"},
    "sonos":        {"type": "consumer_brand", "cat": "tech", "ticker": "SONO", "name": "Sonos", "conf": "MED"},
    "logitech":     {"type": "consumer_brand", "cat": "tech", "ticker": "LOGI", "name": "Logitech", "conf": "MED"},
    # home / household / appliances
    "ninja creami": {"type": "consumer_brand", "cat": "home", "ticker": "SN", "name": "SharkNinja", "conf": "MED"},
    "sharkninja":   {"type": "consumer_brand", "cat": "home", "ticker": "SN", "name": "SharkNinja", "conf": "MED"},
    "yeti":         {"type": "consumer_brand", "cat": "home", "ticker": "YETI", "name": "YETI", "conf": "MED"},
    "hydro flask":  {"type": "consumer_brand", "cat": "home", "ticker": "HELE", "name": "Helen of Troy (Hydro Flask)", "conf": "MED"},
    "rubbermaid":   {"type": "consumer_brand", "cat": "home", "ticker": "NWL", "name": "Newell (Rubbermaid)", "conf": "MED"},
    # PRIVATE / foreign viral = the gap (IPO/M&A watch, ticker None)
    "stanley":      {"type": "consumer_brand", "cat": "home", "ticker": None, "name": "Stanley/PMI (private)", "conf": "MED"},
    "owala":        {"type": "consumer_brand", "cat": "home", "ticker": None, "name": "Owala (private)", "conf": "MED"},
    "scrub daddy":  {"type": "consumer_brand", "cat": "home", "ticker": None, "name": "Scrub Daddy (private)", "conf": "MED"},
    "anker":        {"type": "consumer_brand", "cat": "tech", "ticker": None, "name": "Anker (Shenzhen 300866 — foreign)", "conf": "MED"},
    "alo yoga":     {"type": "consumer_brand", "cat": "apparel", "ticker": None, "name": "Alo (private)", "conf": "MED"},
    "vuori":        {"type": "consumer_brand", "cat": "apparel", "ticker": None, "name": "Vuori (private)", "conf": "MED"},
    "gymshark":     {"type": "consumer_brand", "cat": "apparel", "ticker": None, "name": "Gymshark (private)", "conf": "MED"},
    "halara":       {"type": "consumer_brand", "cat": "apparel", "ticker": None, "name": "Halara (private)", "conf": "MED"},
    "skims":        {"type": "consumer_brand", "cat": "apparel", "ticker": None, "name": "SKIMS (private, Kim K)", "conf": "MED"},
}

_ALL_REG = {**BRAND_TO_VEHICLE, **CONSUMER_BRAND_TO_VEHICLE}


def map_to_vehicle(brand: str) -> dict:
    """Map a (viral) brand to its public vehicle. Beauty + consumer registry first, then openFDA ODM."""
    b = (brand or "").strip().lower()
    bns = b.replace(" ", "")  # space-insensitive: hashtag '#texasroadhouse' vs key 'texas roadhouse'
    if b in _ALL_REG:
        return {"brand": brand, **_ALL_REG[b]}
    # contains-match (longest keys first to avoid short false hits), space-insensitive
    for k in sorted(_ALL_REG, key=len, reverse=True):
        if k in b or k.replace(" ", "") in bns:
            return {"brand": brand, **_ALL_REG[k]}
    # unknown brand: attempt openFDA ODM resolution (the whale-ID route from the Cosmecca DD)
    odm = resolve_odm_via_fda(brand)
    if odm:
        return {"brand": brand, "type": "odm", "ticker": odm.get("ticker"), "name": odm["manufacturer"],
                "conf": "MED", "note": "ODM resolved via openFDA NDC drug-listing (OTC/SPF only)"}
    return {"brand": brand, "type": "unmapped", "ticker": None, "name": "UNMAPPED — private or non-OTC",
            "conf": "NONE", "note": "not in registry; not an OTC/SPF product in openFDA. Likely private brand."}


# manufacturer name -> public ticker (the ODM resolver's last hop)
_ODM_TICKER = {
    "englewood lab": "241710.KQ", "cosmecca": "241710.KQ",
    "cosmax": "192820.KS", "kolmar": "161890.KS",
}


def resolve_odm_via_fda(brand: str) -> dict | None:
    """openFDA NDC/SPL: for an OTC/SPF cosmetic, the drug listing names the manufacturer establishment.
    Free, authoritative US channel — beats Cloudflare-blocked customs BOL (lesson from the Cosmecca DD).
    Returns {manufacturer, ticker?} or None. OTC/SPF subset only (non-drug skincare not covered)."""
    import requests
    try:
        q = f'openfda.brand_name:"{brand}"'
        url = f"https://api.fda.gov/drug/ndc.json?search={q}&limit=3"
        r = requests.get(url, timeout=15)
        if r.status_code != 200:
            return None
        results = r.json().get("results", [])
        for res in results:
            mfr = (res.get("openfda", {}).get("manufacturer_name") or res.get("labeler_name") or [None])
            mfr = mfr[0] if isinstance(mfr, list) else mfr
            if not mfr:
                continue
            tk = next((t for k, t in _ODM_TICKER.items() if k in mfr.lower()), None)
            return {"manufacturer": mfr, "ticker": tk}
    except Exception:
        return None
    return None


def amazon_movers_beauty(limit: int = 30) -> dict:
    """Amazon Movers & Shakers (Beauty) = biggest 24h rank RISERS in beauty — the demand-velocity confirm
    DOWNSTREAM of virality. Reachable (200) but the page is partly JS-lazy; we parse what's in static HTML
    (product titles + brand tokens). Best-effort: returns {status, items:[{rank, title, brand_guess}], note}."""
    import requests
    try:
        r = requests.get("https://www.amazon.com/gp/movers-and-shakers/beauty/", headers=H, timeout=20)
        if r.status_code != 200:
            return {"status": f"HTTP_{r.status_code}", "items": []}
        html = r.text
        # product titles appear in alt= / aria-label / title attributes on the rank cards
        titles = re.findall(r'alt="([^"]{12,140})"', html)
        seen, items = set(), []
        for t in titles:
            t = re.sub(r"\s+", " ", t).strip()
            if len(t) < 12 or t.lower() in seen:
                continue
            seen.add(t.lower())
            brand_guess = next((k for k in BRAND_TO_VEHICLE if k in t.lower()), t.split()[0])
            items.append({"title": t[:120], "brand_guess": brand_guess})
            if len(items) >= limit:
                break
        return {"status": "OK" if items else "EMPTY_STATIC_SHELL",
                "items": items,
                "note": "static-HTML parse; full rank-delta needs JS render or the paid Product Advertising API"}
    except Exception as e:
        return {"status": "ERR", "items": [], "note": str(e)[:120]}


def scan(brands: list[str] | None = None) -> dict:
    """Map a list of viral brands (from the agent WebSearch scan and/or Amazon movers) to public vehicles,
    ranked by investability: a listed brand-owner or a confirmed ODM with a ticker > private/unmapped."""
    brands = brands or []
    mapped = [map_to_vehicle(b) for b in brands]
    investable = [m for m in mapped if m.get("ticker")]
    private = [m for m in mapped if not m.get("ticker")]
    return {"n_brands": len(brands), "investable": investable, "private_or_unmapped": private,
            "note": "viral->public-vehicle map. ticker present = a tradeable beneficiary (latency trade: "
                    "virality leads the manufacturer/brand earnings print ~1-2 quarters)."}


if __name__ == "__main__":
    import json
    demo = ["medicube", "Anua", "Beauty of Joseon", "CeraVe", "Rhode", "Tirtir", "Glow Recipe", "BYOMA"]
    print("== brand->vehicle map (demo) ==")
    print(json.dumps(scan(demo), indent=2, ensure_ascii=False))
    print("\n== amazon movers&shakers beauty (reachability) ==")
    print(json.dumps(amazon_movers_beauty(8), indent=2, ensure_ascii=False))
