"""facilities_resolver — ticker -> geocoded physical sites (R1.13).

The missing link that made every satellite/thermal detector UNCHECKABLE in court:
plant_thermal needs extra.lat/lon, sentinel2_buildout needs an address — both are
SITE-keyed while the conveyor is TICKER-keyed, and no component resolved one into
the other (UPB "no collateral address schedule"; BTDR's blue contested the
undispatched Tydal shell check). Historically a human put the address in the case
file (Bozeman, Woods Lane); the conveyor has no human.

Resolution ladder (deterministic-first, LLM for the free-text part):
  1. HQ        free from SEC submissions JSON (addresses.business) — always tried
  2. SITES     latest 10-K/20-F primary doc -> Properties section (Item 2, or the
               20-F "Property, Plants and Equipment" item) -> one volume-tier
               extraction pass -> JSON site list (name/location/purpose).
               The extractor is told: named, locatable, physical sites ONLY.
  3. GEOCODE   US Census geocoder for US-shaped addresses (free, reliable),
               OSM Nominatim fallback for everything else (Tydal, Norway) —
               1 req/sec pacing, desk UA.
Cache: desk/data/facilities/<ticker>.json, 30-day TTL, provenance on every site
(accession + raw extracted line). Consumers: detector_preflight (planner prompt
gets the geocoded site table -> can emit extra.lat/lon runlists) and the benches
(atlas section shows the same table, so a misresolved site is visible and
contestable rather than silently trusted).

  python3 -m desk.facilities_resolver TICKER [--refresh]
"""
from __future__ import annotations

import datetime
import json
import re
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE_DIR = ROOT / "desk" / "data" / "facilities"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
UA = "SignalOS research desk (contact: 4tripathy@gmail.com)"
TTL_DAYS = 30
MAX_SITES = 10

US_STATE = re.compile(r",\s*(A[LKZR]|C[AOT]|D[EC]|FL|GA|HI|I[DLNA]|K[SY]|LA|M[EDAINSOT]|"
                      r"N[EVHJMYCD]|O[HKR]|PA|RI|S[CD]|T[NX]|UT|V[TA]|W[AVIY])\b", re.I)


def _curl(url: str, timeout: int = 25) -> str:
    r = subprocess.run(["curl", "-s", "--max-time", str(timeout), url,
                        "-H", f"User-Agent: {UA}"], capture_output=True, text=True)
    return r.stdout


def _geocode_us(addr: str) -> tuple[float, float] | None:
    from urllib.parse import quote
    js = _curl("https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"
               f"?address={quote(addr)}&benchmark=Public_AR_Current&format=json")
    try:
        m = json.loads(js)["result"]["addressMatches"]
        return (float(m[0]["coordinates"]["y"]), float(m[0]["coordinates"]["x"])) if m else None
    except Exception:
        return None


def _geocode_osm(addr: str) -> tuple[float, float] | None:
    from urllib.parse import quote
    time.sleep(1.1)                                    # Nominatim policy: 1 req/sec
    js = _curl(f"https://nominatim.openstreetmap.org/search?q={quote(addr)}&format=json&limit=1")
    try:
        rows = json.loads(js)
        return (float(rows[0]["lat"]), float(rows[0]["lon"])) if rows else None
    except Exception:
        return None


def _geocode(addr: str) -> tuple[tuple[float, float] | None, str]:
    if US_STATE.search(addr):
        pt = _geocode_us(addr)
        if pt:
            return pt, "census"
    # Nominatim chokes on building/unit-heavy strings ("Aperia Tower 1, 08 Kallang
    # Avenue, ...") but resolves simplified ones — try progressively coarser forms.
    # drop unit/floor tokens ("#09-0", "Suite 400", "Fl 3") before simplifying —
    # they anchor Nominatim to garbage matches
    parts = [p.strip() for p in addr.split(",")
             if p.strip() and not re.match(r"^(#|Suite|Ste|Unit|Fl(oor)?|Level)\b|^#?[\d\-/]+$",
                                           p.strip(), re.I)]
    tries = [addr]
    if len(parts) >= 3:
        tries.append(", ".join(parts[-3:]))
    if len(parts) >= 2:
        tries.append(", ".join(parts[-2:]))
    for i, q in enumerate(tries):
        pt = _geocode_osm(q)
        if pt:
            return pt, ("nominatim" if i == 0 else f"nominatim-simplified:{q[:60]}")
    return None, "failed"


def _properties_section(cik: int) -> tuple[str, str]:
    """(section_text, accession) from the latest 10-K/20-F primary doc."""
    sub = json.loads(_curl(f"https://data.sec.gov/submissions/CIK{cik:010d}.json") or "{}")
    r = sub.get("filings", {}).get("recent", {})
    rows = list(zip(r.get("form", []), r.get("accessionNumber", []), r.get("primaryDocument", [])))
    # Newest-first, but a 10-K/A is often a Part-III-only amendment (director bios,
    # no Item 2 — the PSIX 0001193125-26-196674 miss): keep walking until a doc
    # whose Properties item actually resolves, holding the first fetch as fallback.
    fallback = None
    tried = 0
    for form, acc, doc in rows:
        if form not in ("10-K", "10-K/A", "20-F", "20-F/A") or not doc:
            continue
        if tried >= 4:
            break
        tried += 1
        accn = acc.replace("-", "")
        html = _curl(f"https://www.sec.gov/Archives/edgar/data/{cik}/{accn}/{doc}", timeout=50)
        if not html.strip():
            # 403/timeout on the primary doc — an INFRA failure, not "no properties"
            # (fc34665d doctrine: near-empty fetch output aborts loud, never a no-fire)
            return "", acc, False
        text = re.sub(r"<[^>]+>", " ", html)
        text = re.sub(r"&[a-z#0-9]+;", " ", text)
        text = re.sub(r"\s+", " ", text)
        # Item 2 Properties (10-K) or Property, Plant(s) and Equipment (20-F item 4)
        m = re.search(r"Item\s*2\s*[.:]?\s*Propert(?:ies|y)(.{200,30000}?)Item\s*3\s*[.:]",
                      text, re.I) or \
            re.search(r"Propert(?:y|ies),?\s*Plants?\s*and\s*Equipment(.{200,30000}?)Item\s*4A",
                      text, re.I)
        section = m.group(1) if m else ""
        if not section and form.endswith("/A"):
            if fallback is None:
                fallback = (text, acc)
            continue                     # Part-III-only amendment — try the original
        # The Properties item is often just the office lease; operating sites (data
        # centers, plants, mines) are described elsewhere (BTDR: Tydal/Rockdale/
        # Clarington live in the business section). Sweep keyword windows doc-wide
        # and append them so the extractor sees the whole physical footprint.
        KEY = re.compile(r"data\s?cent|mining site|facilit|plant|factory|campus|"
                         r"substation|refinery|mine\b|\bMW\b", re.I)
        windows, pos = [], 0
        while len(windows) < 12:
            k = KEY.search(text, pos)
            if not k:
                break
            windows.append(text[max(0, k.start() - 300): k.start() + 500])
            pos = k.start() + 800
        combined = (section + "\n\n=== OTHER FACILITY MENTIONS (doc-wide sweep) ===\n"
                    + "\n---\n".join(windows))
        return (combined if combined.strip() else text[:20000]), acc, True
    if fallback is not None:             # only amendments existed — sweep the best one
        text, acc = fallback
        return text[:20000], acc, True
    return "", "", True


def _extract_sites(section: str, entity: str) -> list[dict] | None:
    """One volume-tier pass: free-text Properties section -> JSON site list.
    Returns None on INFRA failure (dispatch/auth/credits) — the caller must not
    cache that as an observation; [] means the section was read and held nothing."""
    if len(section) < 200:
        return []
    prompt = f"""Extract the PHYSICAL SITES of {entity} from this SEC-filing Properties section.
Rules: named, locatable, physical sites only (plants, factories, mines, data centers,
distribution centers, major offices). NO leased-vs-owned commentary, NO aggregate square
footage rows without a location. For each site give the most geocodable location string
you can (street address if present, else "City, State" / "City, Country").
Output ONLY:
```json
[{{"name": "...", "location": "...", "purpose": "..."}}]
```
Max {MAX_SITES} sites, most operationally important first.

SECTION:
{section[:22000]}"""
    try:
        from desk.court_runner import _dispatch, MODEL_VOLUME
        res = _dispatch(prompt, MODEL_VOLUME)
    except Exception:
        return None            # infra failure (auth/credits/timeout) — never a no-fire
    m = re.search(r"```json\s*(\[.*?\])\s*```", res.get("text", ""), re.S)
    try:
        sites = json.loads(m.group(1)) if m else []
    except Exception:
        sites = []
    return [s for s in sites if s.get("location")][:MAX_SITES]


def resolve(ticker: str, refresh: bool = False) -> dict:
    p = CACHE_DIR / f"{ticker.replace('.', '_')}.json"
    if p.exists() and not refresh:
        try:
            d = json.loads(p.read_text())
            age = (datetime.date.today()
                   - datetime.date.fromisoformat(d["asof"][:10])).days
            if age <= TTL_DAYS and not d.get("degraded"):
                return d
        except Exception:
            pass
    out = {"ticker": ticker, "asof": datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z",
           "hq": None, "sites": [], "note": ""}
    try:
        from desk.court_evidence import _cik
        cik = _cik(ticker)
    except Exception:
        cik = None
    if not cik:
        out["note"] = "no CIK — non-SEC filer; resolver covers US filers only (v1)"
        p.write_text(json.dumps(out, indent=1))
        return out
    sub = json.loads(_curl(f"https://data.sec.gov/submissions/CIK{cik:010d}.json") or "{}")
    entity = sub.get("name") or ticker
    biz = (sub.get("addresses") or {}).get("business") or {}
    if biz.get("city"):
        addr = ", ".join(x for x in [biz.get("street1"), biz.get("city"),
                                     biz.get("stateOrCountry")] if x)
        pt, how = _geocode(addr)
        out["hq"] = {"address": addr, "lat": pt[0] if pt else None,
                     "lon": pt[1] if pt else None, "geocoder": how}
    section, acc, fetch_ok = _properties_section(cik)
    sites = _extract_sites(section, entity) if fetch_ok else None
    if sites is None:
        # INFRA failure (doc fetch 403'd or the extraction dispatch died) — surface
        # loud and DO NOT cache: a transient outage must not become a sticky
        # "0 sites" observation for TTL_DAYS (the SEZL/TTD/PSIX 2026-08-10 vintage).
        out["degraded"] = ("properties-doc fetch empty (SEC 403?)" if not fetch_ok
                          else "site-extraction dispatch failed (auth/credits?)")
        out["note"] = f"DEGRADED — {out['degraded']} (acc {acc or 'none'}); not cached, will retry"
        return out
    for s in sites:
        pt, how = _geocode(s["location"])
        out["sites"].append({**s, "lat": pt[0] if pt else None, "lon": pt[1] if pt else None,
                             "geocoder": how, "provenance": f"Properties section, acc {acc}"})
    n_ok = sum(1 for s in out["sites"] if s["lat"] is not None)
    out["note"] = f"{len(out['sites'])} sites extracted, {n_ok} geocoded (acc {acc or 'none'})"
    p.write_text(json.dumps(out, indent=1))
    return out


def render_facilities(ticker: str) -> str:
    """Compact table for planner + bench prompts. Empty string when nothing resolved."""
    try:
        d = resolve(ticker)
    except Exception as e:
        return f"(facilities resolver failed: {type(e).__name__})"
    lines = []
    if d.get("hq") and d["hq"].get("lat") is not None:
        h = d["hq"]
        lines.append(f"- HQ: {h['address']} -> lat={h['lat']:.5f} lon={h['lon']:.5f} [{h['geocoder']}]")
    for s in d.get("sites", []):
        loc = f"lat={s['lat']:.5f} lon={s['lon']:.5f} [{s['geocoder']}]" \
              if s.get("lat") is not None else "GEOCODE FAILED"
        lines.append(f"- {s.get('name','?')} ({s.get('purpose','')[:40]}): {s.get('location')} -> {loc}")
    if not lines:
        return ""
    return ("RESOLVED FACILITIES (from the issuer's own Properties disclosure — geocoded; "
            "sanity-check any site you rely on, extraction is LLM-assisted):\n" + "\n".join(lines))


if __name__ == "__main__":
    import sys
    t = sys.argv[1]
    d = resolve(t, refresh="--refresh" in sys.argv)
    print(json.dumps(d, indent=1))
