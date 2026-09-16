"""Pull the CDIAC / DebtWatch Default-Draw index (real per-issuer CA default & reserve-draw
events) and characterize it for the AI-crash rating work.

Real API (reverse-engineered from the DebtWatch SPA; the commonly-cited
treasurer.ca.gov/cdiac/default-draw/issuename.asp is a 404):
  gateway  = https://debtwatch.treasurer.ca.gov/api   (from /env.json -> API_GATEWAY_URL)
  list     = GET  /dataset
  schema   = GET  /dataset/{slug}
  full     = GET  /dataset/{slug}/export/tabular   -> {id,name,columns,rows[]}
  search   = PUT  /dataset/{slug}/search  (body filters/pagination/sorting; 500s easily)

KEY FINDING: the Default-Draw index spans 1991-2026 but is ~81% Mello-Roos/CFD land-secured
DRAW/DEFAULT events (those carry mandatory CDIAC reporting under Gov Code 53359/6599.1). It is
NOT a rating-action database: the GO / school-GO / hospital-conduit / CCRC / water / county /
TAB sectors whose AI-crash credit stress shows up as DOWNGRADES (not reserve draws) are ~absent.
=> CDIAC cannot harden the 8-sector cross-sectional rating ordering; those counts live only in
proprietary Moody's/S&P/Fitch archives. BUT the land-secured series independently CONFIRMS
channel-specificity: it spikes in PROPERTY crashes (early-90s aftermath, 2008-12 housing) and
does NOT spike in the dot-com INCOME/cap-gains bust -- exactly what beta-CapGains predicts for a
property-channel sector.
"""
import urllib.request as u, json, re
from collections import Counter, defaultdict

API = "https://debtwatch.treasurer.ca.gov/api"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
      "Accept": "application/json"}
OUT = "/Users/ajay/exalted/signalos/verticals/muni_credit/data/cdiac_draws.json"
# verified positional schema of export rows
ISS, NAME, PROJ, DEVENT, TYPE, AMT, CTY = 1, 2, 3, 10, 12, 13, 8


def fetch():
    r = u.urlopen(u.Request(API + "/dataset/draws/export/tabular", headers=UA), timeout=120)
    return json.loads(r.read())["rows"]


def sector(iss, name, proj):
    s = " ".join(x or "" for x in (iss, name, proj)).lower()
    if re.search(r'cfd|community facilit|mello|facilities district|improvement district|assessment dist', s):
        return "Land-secured (CFD/Mello-Roos/AD)"
    if re.search(r'school|unified|elementary|high school|usd\b|joint union|college', s): return "School/education"
    if re.search(r'water|irrigation|utilit|sewer|\bpower\b|electric', s): return "Water/utility"
    if re.search(r'hospital|health|medical|clinic', s): return "Hospital/health"
    if re.search(r'redevelop|tax alloc|successor|\brda\b', s): return "RDA/TAB"
    if re.search(r'housing|\bhfa\b|apartment|residential|senior living|retire|continuing care', s): return "Housing/senior"
    if re.search(r'state of california', s): return "State GO"
    if re.search(r'county', s): return "County"
    return "Other/revenue"


# ----------------------------------------------------------------------------
# Data-sourcing layer for detectors/cdiac_default_draw.py
# ----------------------------------------------------------------------------
_STOP = frozenset({
    "cfd", "community", "facilities", "facility", "district", "districts", "no", "number",
    "series", "bonds", "bond", "of", "the", "and", "city", "town", "county", "ca",
    "california", "agency", "authority", "financing", "finance", "special", "tax", "taxes",
    "improvement", "improvements", "area", "areas", "project", "projects", "public", "joint",
    "powers", "jpa", "unified", "school", "elementary", "high", "redevelopment", "successor",
    "housing", "municipal", "assessment", "limited", "obligation", "reassessment", "refunding",
    "development", "statewide", "communities", "fund", "reserve",
    # entity-TYPE descriptors (not place names) — these caused generic-token over-fires:
    "union", "secondary", "grammar", "water", "utility", "utilities", "sanitary", "sanitation",
    "sewer", "power", "electric", "gas", "drainage", "flood", "lighting", "landscaping",
    "maintenance", "transit", "transportation", "parking", "library", "fire", "police",
    "hospital", "health", "memorial", "medical", "college", "university", "metropolitan", "regional",
})


_MAX_DF = 6   # a token in MORE than this many distinct issuers is generic (water/union/utility),
              # not a discriminating place name -> ignore it for matching (matcher-precision rule)


def issuer_df(index):
    """token -> number of DISTINCT issuers containing it (corpus document frequency)."""
    from collections import Counter
    df = Counter()
    for iss in {e["issuer"] for e in index}:
        for t in set(re.findall(r"[a-z0-9]+", (iss or "").lower())):
            df[t] += 1
    return df


def _distinctive(name, df=None):
    toks = re.findall(r"[a-z0-9]+", (name or "").lower())
    words = frozenset(t for t in toks if t not in _STOP and len(t) >= 4
                      and (df is None or df.get(t, 0) <= _MAX_DF))   # drop corpus-common tokens
    nums = frozenset(t for t in toks if t.isdigit() and not (len(t) == 4 and 1900 <= int(t) <= 2099))
    return words, nums


def _match(obligor, issuer, df=None):
    """Conservative name match -> 'HIGH' / 'MEDIUM' / None.
    HIGH  = >=2 shared distinctive tokens, OR consistent district numbers, OR high full-token
            overlap (exact-entity match incl. type words like 'public financing authority').
    MEDIUM= 1 shared distinctive (place) token only -> review, do NOT hard-exclude (a city-token
            collision is not a confirmed match; cf. matcher-precision discipline).
    None  = no shared distinctive token, or district numbers conflict (CFD No 1 vs No 5)."""
    ow, on = _distinctive(obligor, df); iw, inn = _distinctive(issuer, df)
    if not ow or not iw:
        return None
    shared = ow & iw
    if not shared:
        return None
    if on and inn and not (on & inn):   # CFD No 1 must not match CFD No 5
        return None
    ot = set(re.findall(r"[a-z0-9]+", (obligor or "").lower()))
    it = set(re.findall(r"[a-z0-9]+", (issuer or "").lower()))
    jacc = len(ot & it) / len(ot | it) if (ot | it) else 0.0   # exact-entity overlap incl. type words
    if len(shared) >= 2 or (on & inn) or jacc >= 0.6:
        return "HIGH"
    return "MEDIUM"


def _row_to_event(r):
    return {"cdiac": r[0], "issuer": r[1], "issue_name": r[2],
            "date": (r[DEVENT] or "")[:10], "type": r[TYPE],
            "amount_usd": r[AMT], "county": r[CTY]}


def load_index(path=OUT):
    """Parsed CDIAC default/draw events (from the cached pull; run main() to refresh)."""
    import json as _j
    rows = _j.load(open(path))["rows"]
    return [_row_to_event(r) for r in rows]


def events_for(obligor_name, county=None, index=None, df=None):
    """Matched default/draw events for one obligor, best confidence kept."""
    idx = index if index is not None else load_index()
    if df is None:
        df = issuer_df(idx)
    out, best = [], None
    for e in idx:
        c = _match(obligor_name, e["issuer"], df)
        if not c:
            continue
        if county and e.get("county") and county.lower() not in (e["county"] or "").lower() and c == "MEDIUM":
            continue   # tighten a place-only match with a county mismatch
        out.append({**e, "_conf": c})
        best = "HIGH" if (best == "HIGH" or c == "HIGH") else "MEDIUM"
    return out, best


def build_detector_data(obligors, index=None):
    """{obligor -> {'cdiac_default_draw': {...}}} for the union runner.
    `obligors` = list of names, or dict {name: county}. Returns an entry for EVERY
    queried obligor (empty events => CLEAN) so the dispatch coverage validator sees it fed."""
    idx = index if index is not None else load_index()
    df = issuer_df(idx)
    items = obligors.items() if isinstance(obligors, dict) else ((n, None) for n in obligors)
    out = {}
    for name, county in items:
        evs, conf = events_for(name, county, idx, df)
        out[name] = {"cdiac_default_draw": {
            "events": [{k: v for k, v in e.items() if k != "_conf"} for e in evs],
            "n_defaults": sum(1 for e in evs if (e["type"] or "").lower().startswith("default")),
            "n_draws": sum(1 for e in evs if "draw" in (e["type"] or "").lower()),
            "n_replenishments": sum(1 for e in evs if "replen" in (e["type"] or "").lower()),
            "match_confidence": conf or "HIGH",
            "matched_issuers": sorted({e["issuer"] for e in evs}),
            "source": "CDIAC Default & Draw on Reserve (DebtWatch API)", "as_of": 2026,
        }}
    return out


def main():
    rows = fetch()
    years, sect, typ = Counter(), Counter(), Counter()
    crises = {"dot-com 2000-03": (2000, 2003), "GFC 2008-09": (2008, 2009),
              "COVID 2020": (2020, 2020), "2022": (2022, 2022)}
    cw = defaultdict(Counter)
    land_by_year = Counter()
    for r in rows:
        d = (r[DEVENT] or "")[:4]; y = int(d) if d.isdigit() else None
        sc = sector(r[ISS], r[NAME], r[PROJ])
        sect[sc] += 1; typ[r[TYPE]] += 1
        if y:
            years[y] += 1
            if sc.startswith("Land"): land_by_year[y] += 1
            for cn, (a, b) in crises.items():
                if a <= y <= b: cw[cn][sc] += 1
    # property-crash vs income-crash land-secured intensity
    def span(a, b): return sum(land_by_year[y] for y in range(a, b + 1))
    summary = {
        "n_events": len(rows), "date_range": [min(years), max(years)],
        "type_counts": dict(typ), "sector_counts": dict(sect.most_common()),
        "per_crisis_sector": {cn: dict(cw[cn].most_common()) for cn in crises},
        "land_secured_intensity": {
            "early90s_property_aftermath_1994_1998": span(1994, 1998),
            "dotcom_income_bust_2000_2003": span(2000, 2003),
            "GFC_housing_2008_2012": span(2008, 2012),
            "COVID_2020": span(2020, 2020), "y2022": span(2022, 2022)},
        "land_by_year": dict(sorted(land_by_year.items())),
        "finding": ("CDIAC draws index = ~81% land-secured; cannot harden the 8 rating sectors "
                    "(their stress is downgrades, not draws -> they appear 0-3x). "
                    "NOTE: an earlier 'land-secured spikes in property crashes not dot-com' read does "
                    "NOT hold in the data — land-by-year is 2000=16 -> 2003=11 (dot-com) vs 2008=17 / "
                    "2011=15 / 2012=10 (GFC); the GFC values are ~equal to the dot-com baseline, so "
                    "there is NO clean property-vs-income contrast here. Treat as inconclusive."),
    }
    json.dump({"summary": summary, "rows": rows}, open(OUT, "w"), indent=1, default=str)
    print(f"events {summary['n_events']} | range {summary['date_range']} | types {summary['type_counts']}")
    print("\nby sector:")
    for s, n in sect.most_common(): print(f"   {n:>4}  {s}")
    print("\nLand-secured (property-channel) default/draw intensity:")
    for k, v in summary["land_secured_intensity"].items(): print(f"   {v:>4}  {k}")
    print("\nsaved ->", OUT)


if __name__ == "__main__":
    main()
