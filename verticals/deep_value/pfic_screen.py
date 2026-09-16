"""pfic_screen — flags PFIC (Passive Foreign Investment Company) risk on FOREIGN filers, so the harvest
loop can EXCLUDE the §1291 tax landmine before it ever reaches the book. Only foreign corporations can be
PFICs, so US filers always pass.

A foreign corp is a PFIC if EITHER (the two statutory tests, proxied from financials):
  ASSET test  — >=50% of assets produce/held-for passive income. Proxy: (cash + all investments)/assets.
  INCOME test — >=75% of gross income is passive. Proxy: an operating company with real revenue relative
                to its asset base is active; a cash shell / pre-revenue holdco with near-zero revenue and
                a high passive-asset ratio fails.

LIMITATIONS (this is a RISK FILTER, not a determination — survivors still want tax-counsel sign-off):
  - misses the look-through rule (a holdco looking through to >25%-owned ACTIVE subs can flip non-PFIC),
    the startup-year exception, and year-to-year variation (re-run annually — the loop does this);
  - banks/insurers hold passive-looking assets but have active exceptions — but the deep-value universe is
    ex-financials, so that false-positive is largely avoided;
  - cleanest authoritative signal is the filer's OWN disclosure in its 20-F (see disclosed_pfic()).
"""
from __future__ import annotations

PASSIVE_CONCEPTS = ["CashAndCashEquivalentsAtCarryingValue", "ShortTermInvestments", "LongTermInvestments",
                    "OtherLongTermInvestments", "MarketableSecuritiesNoncurrent",
                    "AvailableForSaleSecuritiesNoncurrent"]


def pfic_risk(r: dict, f: dict) -> dict:
    """r = score.compute_metrics output (needs r['foreign'], r['rev']); f = raw fundamentals row."""
    if not r.get("foreign"):
        return {"pfic": False, "severity": None, "reason": "US filer — PFIC N/A"}
    assets = f.get("Assets")
    if not assets or assets <= 0:
        return {"pfic": None, "severity": "REVIEW", "reason": "no asset data — PFIC UNVERIFIABLE (exclude/confirm)"}
    passive = sum((f.get(c) or 0) for c in PASSIVE_CONCEPTS)
    passive_ratio = passive / assets
    rev = r.get("rev")
    rev_intensity = (rev / assets) if (rev is not None and assets) else None

    asset_fail = passive_ratio >= 0.50
    income_proxy_fail = (rev_intensity is not None and rev_intensity < 0.10 and passive_ratio >= 0.40)
    flag = asset_fail or income_proxy_fail
    if not flag:
        return {"pfic": False, "severity": "clean",
                "reason": f"passive-assets {passive_ratio:.0%} / rev-intensity {rev_intensity if rev_intensity is None else f'{rev_intensity:.0%}'} — active business"}
    sev = "HIGH" if (passive_ratio >= 0.50 and (rev_intensity is None or rev_intensity < 0.05)) else "MED"
    why = []
    if asset_fail:
        why.append(f"asset-test FAIL (passive {passive_ratio:.0%} >=50%)")
    if income_proxy_fail:
        why.append(f"income-proxy FAIL (rev/assets {rev_intensity:.0%} <10%)")
    return {"pfic": True, "severity": sev, "passive_ratio": round(passive_ratio, 3),
            "reason": "; ".join(why) + " — likely PFIC, exclude (confirm vs 20-F)"}


def disclosed_pfic(cik: int) -> str | None:
    """Authoritative-ish: read the filer's own PFIC belief from recent filings via EDGAR full-text search.
    Returns 'asserts-not-pfic' / 'asserts-or-may-be-pfic' / None (not found)."""
    try:
        import urllib.request, json
        url = ('https://efts.sec.gov/LATEST/search-index?q=%22passive+foreign+investment+company%22'
               f'&ciks={cik:010d}&forms=20-F')
        d = json.load(urllib.request.urlopen(urllib.request.Request(
            url, headers={"User-Agent": "signalos research 4tripathy@gmail.com"}), timeout=30))
        hits = d.get("hits", {}).get("total", {}).get("value", 0)
        return "mentions-PFIC-in-20-F (read tax note)" if hits else None
    except Exception:
        return None
