"""coverage — closes the dispatch gap. Adding a name auto-DISPATCHES on its features, but feature TAGGING
is manual, so an untagged name silently falls through detectors. This module:
  1. infers candidate features from primary data (SEC SIC code) so a new name self-populates,
  2. audits the book: per name x per detector = COVERED / GAP (inferred-should-but-not-tagged) / n-a,
so 'do we auto-update all detectors when we add a stock?' becomes YES — add the ticker, run coverage,
confirm/auto-fill the proposed features, and every applicable detector now scans it.

  python3 -m desk.coverage audit            # coverage matrix + gaps over the current book
  python3 -m desk.coverage infer AAPL       # propose features for a candidate ticker
"""
from __future__ import annotations
import json, sys, urllib.request
from pathlib import Path
from . import book_universe as BU, detector_scan as DS

HDRS = {"User-Agent": "signalos-desk research 4tripathy@gmail.com"}
_TICKER_CIK = None
SIC_CACHE = Path(__file__).resolve().parent / "data" / "sic_cache.json"


def _load_sic_cache():
    return json.loads(SIC_CACHE.read_text()) if SIC_CACHE.exists() else {}


def _save_sic_cache(c):
    SIC_CACHE.write_text(json.dumps(c, indent=1))

# SIC-range -> feature the detector dispatch keys on. ONLY assert what SIC RELIABLY implies. We deliberately
# do NOT infer `undisclosed_cust` from cosmetics SIC (2844): SIC cannot distinguish an ODM/contract-
# manufacturer (whose top CUSTOMER is undisclosed — the whale detector's case) from a brand-owner (whose
# customers are disclosed retailers). That over-fired on ODD (a brand). undisclosed_cust stays a MANUAL tag,
# set only on confirmed contract-manufacturers. gov_revenue is advisory (usaspending self-validates: a
# false tag just returns not_found, a harmless no-op), so it's low-harm to propose.
SIC_FEATURES = [
    (lambda s: 1310 <= s <= 1389, "physical_asset", {"kind": "methane_oil", "aoi": "<set lat/lon>"}),  # crude/natgas E&P — reliable
    (lambda s: s in (8742, 3812), "gov_revenue", True),   # mgmt consulting / defense — advisory (self-validating)
]


def _ticker_cik():
    global _TICKER_CIK
    if _TICKER_CIK is None:
        try:
            d = json.load(urllib.request.urlopen(urllib.request.Request(
                "https://www.sec.gov/files/company_tickers.json", headers=HDRS), timeout=30))
            _TICKER_CIK = {r["ticker"].upper(): (int(r["cik_str"]), r["title"]) for r in d.values()}
        except Exception:
            _TICKER_CIK = {}
    return _TICKER_CIK


def _sic(ticker, cache=None, use_network=True):
    """SIC + description + title, cached in sic_cache.json (SIC is ~static, so the pre-flight stays cheap)."""
    t = ticker.upper()
    cache = _load_sic_cache() if cache is None else cache
    if t in cache:
        c = cache[t]
        return c.get("sic"), c.get("desc"), c.get("title")
    if not use_network:
        return None, None, None
    tc = _ticker_cik().get(t)
    if not tc:
        cache[t] = {"sic": None, "desc": None, "title": None}
        _save_sic_cache(cache)
        return None, None, None
    cik, title = tc
    try:
        sub = json.load(urllib.request.urlopen(urllib.request.Request(
            f"https://data.sec.gov/submissions/CIK{cik:010d}.json", headers=HDRS), timeout=30))
        sic, desc = int(sub.get("sic") or 0), sub.get("sicDescription")
    except Exception:
        sic, desc = None, None
    cache[t] = {"sic": sic, "desc": desc, "title": title}
    _save_sic_cache(cache)
    return sic, desc, title


def infer_features(ticker, cache=None, use_network=True) -> dict:
    """Propose features from SIC + a default. US-listed => litigation True. Returns {feature: value, ...}."""
    sic, desc, title = _sic(ticker, cache=cache, use_network=use_network)
    feats = {}
    if sic is not None:                       # has a US CIK -> federal-docket screen applies
        feats["litigation"] = True
    for pred, feat, val in SIC_FEATURES:
        try:
            if sic and pred(sic):
                feats[feat] = val
        except Exception:
            pass
    return {"ticker": ticker.upper(), "sic": sic, "sicDescription": desc, "legal_name": title,
            "proposed_features": feats}


def audit(use_network=True) -> dict:
    """Per-name coverage vs every detector; flag GAPs where SIC says a feature SHOULD be set but isn't.
    use_network=False => cache-only (the cheap pre-flight the runner calls every heartbeat)."""
    cache = _load_sic_cache()
    rows = []
    for t, f in BU.BOOK.items():
        covered = [d for d, spec in DS.DETECTORS.items() if f.get(spec["feature"])]
        inf = infer_features(t, cache=cache, use_network=use_network)["proposed_features"]
        gaps = [d for d, spec in DS.DETECTORS.items()
                if inf.get(spec["feature"]) and not f.get(spec["feature"])]
        rows.append({"ticker": t, "covered_by": covered, "inferred_gaps": gaps, "thin": len(covered) == 0})
    return {"rows": rows,
            "thin": [r["ticker"] for r in rows if r["thin"]],
            "gaps": [{"ticker": r["ticker"], "missing": r["inferred_gaps"]} for r in rows if r["inferred_gaps"]],
            "n_thin": sum(1 for r in rows if r["thin"]),
            "n_gap": sum(1 for r in rows if r["inferred_gaps"])}


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "audit"
    if cmd == "infer":
        print(json.dumps(infer_features(sys.argv[2]), indent=1))
    else:
        a = audit()
        print(f"=== DESK DETECTOR COVERAGE ({len(a['rows'])} names; {len(DS.DETECTORS)} detectors) ===")
        print(f"  thin (no detector covers it): {a['n_thin']}   |   inferred GAPs: {a['n_gap']}\n")
        for r in sorted(a["rows"], key=lambda x: (not x["thin"], not x["inferred_gaps"], x["ticker"])):
            flag = "  ⚠THIN" if r["thin"] else ("  ⚠GAP" if r["inferred_gaps"] else "")
            cov = ",".join(d.replace("_", "") for d in r["covered_by"]) or "—"
            gap = (" | GAPS: " + ",".join(r["inferred_gaps"])) if r["inferred_gaps"] else ""
            print(f"  {r['ticker']:10} covered: {cov}{gap}{flag}")
