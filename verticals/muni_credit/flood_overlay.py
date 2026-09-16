"""flood_overlay — per-district FLOOD / levee / subsidence exposure for the CA muni sleeve.

WHY. We cap named-fault seismic zones and high-wildfire names, but we DO NOT screen flood — and
the sleeve's largest geographic cluster is Central Valley school districts (Turlock, Stockton,
Modesto, Chico) sitting behind Sacramento-San Joaquin Delta levees, on the valley floodplain.
The transmission channel is identical to the fire channel and is NOT the flood event itself
(a levee overtop) but the SECOND-ORDER drag: flood / levee-failure hazard -> insurer withdrawal
+ NFIP/private premium repricing -> property unmarketable / values stall -> Prop-8 reassessments
and frozen turnover erode ASSESSED VALUE, the very base the unlimited ad-valorem GO levy rides on.
The historical "no school GO default" record predates accelerating levee-risk repricing.

CHAIN (no GIS required — it's a table join, mirroring wildfire_overlay):
  1. FEMA National Risk Index, census-tract flood fields (official FEMA ArcGIS service):
     - Riverine / inland flooding: IFLD_RISKS (score 0-100), IFLD_RISKR (rating)
     - Coastal flooding:          CFLD_RISKS (score 0-100), CFLD_RISKR (rating)
     - BUILDVALUE (tract building-value exposure), TRACTFIPS
     NOTE ON FIELD NAMES: the brief named RFLD_* for riverine, but the authoritative FEMA NRI
     census-tract FeatureServer (the SAME service that produced nri_ca_tracts_wildfire.json)
     exposes riverine flooding under the prefix IFLD ("Inland Flooding"), not RFLD. We use the
     real service fields IFLD_* / CFLD_* and label them riverine / coastal. No fabrication.
  2. NCES EDGE GRF25 relationship file: school-district (LEA) <-> census-tract membership —
     reused verbatim from wildfire_overlay.load_grf_ca().
  3. District flood metrics = building-value-weighted mean of the per-tract MAX(riverine, coastal)
     flood score, plus the share of district building value in Relatively-High / Very-High flood
     tracts ("flood_high_share"). Same BV weighting and same name-normalization as the fire screen.

"No Rating" / "Not Applicable" tracts are scored 0 — that is FEMA's meaning (no modeled flood
exposure), not missing data. A tract genuinely absent from the pull contributes nothing; a district
with NO matched flood data returns flood_score=None so a no-data district can never read "clean".

SUBSIDENCE. The San Joaquin Valley groundwater-overdraft land-subsidence corridor (Friant-Kern /
Delta-Mendota canal damage, well-casing failure, infrastructure cost) is a slow AV drag distinct
from flood. We carry a lightweight static county flag for the SGMA critically-overdrafted SJV
basins; it is a flag + note only, not a modeled score.

OUTPUT: district_flood(name, grf, tracts) -> dict of flood_* fields (+ subsidence_flag / note).
This module does NOT merge into or mutate issuer_credit_latest.json or any other file; integration
is done separately. __main__ is a read-only self-test over the book.
"""
from __future__ import annotations
import json, os, re, urllib.request, urllib.parse, difflib

# Reuse the wildfire template's CA-GRF loader and name-normalizer VERBATIM (single source of truth).
from wildfire_overlay import load_grf_ca, _norm  # noqa: F401  (imported for reuse + re-export)

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "issuer_credit")
FLOOD_CACHE = os.path.join(DATA, "nri_ca_tracts_flood.json")
HIGH = {"Relatively High", "Very High"}

# Same FEMA NRI census-tract FeatureServer that produced nri_ca_tracts_wildfire.json
# (URL sourced from buyside_dd/source_atlas.py NRI atlas entry).
NRI_URL = ("https://services.arcgis.com/XG15cJAlne2vxtgt/arcgis/rest/services/"
           "National_Risk_Index_Census_Tracts/FeatureServer/0/query")
NRI_FIELDS = "TRACTFIPS,COUNTY,IFLD_RISKS,IFLD_RISKR,CFLD_RISKS,CFLD_RISKR,BUILDVALUE"

# FEMA NRI ordinal rating ladder (low -> high); "Not Applicable"/"No Rating"/None == no exposure.
_LADDER = ["No Rating", "Not Applicable", "Insufficient Data", "Very Low", "Relatively Low",
           "Relatively Moderate", "Relatively High", "Very High"]

# SJV critically-overdrafted subsidence corridor counties (SGMA + USGS land-subsidence record).
_SUBSIDENCE_COUNTIES = {"FRESNO", "KINGS", "KERN", "TULARE", "MADERA", "MERCED"}


def _fetch_flood_tracts() -> list:
    """Pull all CA census-tract flood rows from the FEMA NRI FeatureServer (paged)."""
    rows, offset = [], 0
    while True:
        params = {
            "where": "STATEABBRV='CA'",
            "outFields": NRI_FIELDS,
            "f": "json",
            "returnGeometry": "false",
            "resultOffset": offset,
            "resultRecordCount": 2000,
        }
        url = NRI_URL + "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 SignalOS muni flood overlay"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            j = json.load(resp)
        if "error" in j:
            raise RuntimeError(f"FEMA NRI error: {j['error']}")
        feats = j.get("features", [])
        rows.extend(f["attributes"] for f in feats)
        if not j.get("exceededTransferLimit") or not feats:
            break
        offset += len(feats)
    if not rows:
        raise RuntimeError("FEMA NRI returned zero CA flood tracts")
    return rows


def load_tracts(refresh: bool = False) -> dict | None:
    """{TRACTFIPS: {score(max riverine/coastal), riv, cst, rating(worse of two), bv}} or None.

    Returns None (never an empty/clean dict) if neither the cache nor a live pull is available —
    the consumer must treat None as 'no data', not as 'no flood risk'.
    """
    rows = None
    if not refresh and os.path.exists(FLOOD_CACHE):
        try:
            rows = json.load(open(FLOOD_CACHE))
        except Exception:
            rows = None
    if rows is None:
        try:
            rows = _fetch_flood_tracts()
            json.dump(rows, open(FLOOD_CACHE, "w"), indent=1)
        except Exception as e:
            print(f"[flood_overlay] FEMA NRI flood pull FAILED ({type(e).__name__}: {e}); "
                  f"no cache at {FLOOD_CACHE}. Flood fields will be None.")
            return None
    out = {}
    for r in rows:
        def sc(v):
            try: return float(v)
            except (TypeError, ValueError): return 0.0
        def rt(v):
            return v if (v in _LADDER) else "No Rating"
        riv_s, cst_s = sc(r.get("IFLD_RISKS")), sc(r.get("CFLD_RISKS"))
        riv_r, cst_r = rt(r.get("IFLD_RISKR")), rt(r.get("CFLD_RISKR"))
        score = max(riv_s, cst_s)
        rating = riv_r if _LADDER.index(riv_r) >= _LADDER.index(cst_r) else cst_r
        out[str(r["TRACTFIPS"]).zfill(11)] = {
            "score": score, "riv": riv_s, "cst": cst_s,
            "riv_rating": riv_r, "cst_rating": cst_r, "rating": rating,
            "bv": sc(r.get("BUILDVALUE")),
        }
    return out


def _subsidence(county: str | None) -> tuple[bool, str]:
    if county and county.strip().upper() in _SUBSIDENCE_COUNTIES:
        return True, (f"{county.strip().title()} County sits in the San Joaquin Valley "
                      "critically-overdrafted groundwater / land-subsidence corridor (SGMA + USGS); "
                      "subsidence damages infrastructure and is a slow AV drag distinct from flood.")
    return False, ""


def district_flood(name: str, grf: dict, tracts: dict | None, county: str | None = None) -> dict | None:
    """Per-district flood exposure.

    Returns a dict with:
      flood_score        BV-weighted mean of per-tract max(riverine, coastal) flood score (0-100)
      flood_high_share   share of district building value in Relatively-High/Very-High flood tracts
      flood_worst_tract  worst (riverine-or-coastal) FEMA flood rating across member tracts
      flood_riv_share    BV share in high RIVERINE tracts (Central-Valley channel)
      flood_cst_share    BV share in high COASTAL tracts
      flood_match        matched GRF LEA name
      flood_match_conf   fuzzy-match confidence (0-1)
      flood_n_tracts     number of matched member tracts
      subsidence_flag    bool — county in SJV subsidence corridor
      subsidence_note    str  — explanation if flagged

    If `tracts` is None (data pull failed) every flood_* field is None and a no_flood_data flag is
    set, so a screen can NEVER come back "clean" without data. Subsidence (static) still resolves.
    """
    sub_flag, sub_note = _subsidence(county)
    if tracts is None:
        return {"flood_score": None, "flood_high_share": None, "flood_worst_tract": None,
                "flood_riv_share": None, "flood_cst_share": None, "flood_match": None,
                "flood_match_conf": None, "flood_n_tracts": None, "no_flood_data": True,
                "subsidence_flag": sub_flag, "subsidence_note": sub_note}

    q = _norm(name)
    best, conf = None, 0.0
    for nm in grf:
        r = difflib.SequenceMatcher(None, q, nm).ratio()
        if q and q.split()[0] in nm:
            r += 0.08
        if r > conf:
            best, conf = nm, r
    base = {"subsidence_flag": sub_flag, "subsidence_note": sub_note, "no_flood_data": False}
    if best is None or conf < 0.6:
        base.update({"flood_score": None, "flood_high_share": None, "flood_worst_tract": None,
                     "flood_riv_share": None, "flood_cst_share": None, "flood_match": None,
                     "flood_match_conf": round(conf, 2), "flood_n_tracts": 0})
        return base
    member = [(tracts[t], a) for t, a in grf[best] if t in tracts]
    if not member:
        base.update({"flood_score": None, "flood_high_share": None, "flood_worst_tract": None,
                     "flood_riv_share": None, "flood_cst_share": None, "flood_match": best,
                     "flood_match_conf": round(conf, 2), "flood_n_tracts": 0})
        return base
    tot_bv = sum(m["bv"] for m, _ in member) or 1.0
    score = sum(m["score"] * m["bv"] for m, _ in member) / tot_bv
    high_share = sum(m["bv"] for m, _ in member if m["rating"] in HIGH) / tot_bv
    riv_share = sum(m["bv"] for m, _ in member if m["riv_rating"] in HIGH) / tot_bv
    cst_share = sum(m["bv"] for m, _ in member if m["cst_rating"] in HIGH) / tot_bv
    worst = max((m["rating"] for m, _ in member), key=lambda r: _LADDER.index(r))
    base.update({
        "flood_score": round(score, 1),
        "flood_high_share": round(high_share, 3),
        "flood_worst_tract": worst,
        "flood_riv_share": round(riv_share, 3),
        "flood_cst_share": round(cst_share, 3),
        "flood_match": best,
        "flood_match_conf": round(conf, 2),
        "flood_n_tracts": len(member),
    })
    return base


# --- Banded thresholds (analogous to the wildfire screen) ------------------------------------
# Decision is driven by flood_high_share (BV share in Relatively-High/Very-High flood tracts):
#   flood_high_share >= 0.30           -> hard FLAG   (cap / haircut the name's par)
#   0.15 <= flood_high_share <  0.30   -> soft REVIEW  (surface for analyst review)
#   flood_high_share <  0.15           -> pass
#   subsidence_flag is an INDEPENDENT soft REVIEW overlay (SJV corridor), even at low flood share.
FLAG_HIGH_SHARE = 0.30
REVIEW_HIGH_SHARE = 0.15


def flood_band(rec: dict) -> str:
    """FLAG / REVIEW / PASS / NO-DATA from a district_flood() dict."""
    if rec is None or rec.get("no_flood_data") or rec.get("flood_high_share") is None:
        # No flood data: cannot clear. Subsidence may still elevate to REVIEW.
        return "REVIEW" if (rec and rec.get("subsidence_flag")) else "NO-DATA"
    hs = rec["flood_high_share"]
    if hs >= FLAG_HIGH_SHARE:
        return "FLAG"
    if hs >= REVIEW_HIGH_SHARE or rec.get("subsidence_flag"):
        return "REVIEW"
    return "PASS"


def main():
    tracts = load_tracts()
    if tracts is None:
        print("\n*** FLOOD DATA UNAVAILABLE — every district returns flood fields = None. "
              "This is NOT a clean result. Resolve the FEMA NRI pull before relying on the screen. ***")
    else:
        print(f"[flood_overlay] loaded {len(tracts)} CA flood tracts "
              f"(cache: {os.path.basename(FLOOD_CACHE)})")
    grf = load_grf_ca()
    p = os.path.join(DATA, "issuer_credit_latest.json")
    recs = json.load(open(p))
    print(f"\n{'cusip':11} {'band':7} {'flood':>5} {'hiBV%':>6} {'rivBV%':>6} {'cstBV%':>6} "
          f"{'worst rating':17} {'conf':>4} {'sub':>3}  district")
    n_flag = n_review = n_pass = n_nodata = 0
    for r in recs:
        if not r.get("district"):
            continue
        f = district_flood(r["district"], grf, tracts, county=r.get("county"))
        band = flood_band(f)
        n_flag += band == "FLAG"; n_review += band == "REVIEW"
        n_pass += band == "PASS"; n_nodata += band == "NO-DATA"
        fs = f.get("flood_score"); hs = f.get("flood_high_share")
        rv = f.get("flood_riv_share"); cs = f.get("flood_cst_share")
        print(f"{r['cusip']:11} {band:7} "
              f"{(fs if fs is not None else -1):5.1f} "
              f"{(100*hs if hs is not None else -1):6.1f} "
              f"{(100*rv if rv is not None else -1):6.1f} "
              f"{(100*cs if cs is not None else -1):6.1f} "
              f"{(f.get('flood_worst_tract') or '?'):17} "
              f"{(f.get('flood_match_conf') or 0):4.2f} "
              f"{('Y' if f.get('subsidence_flag') else '-'):>3}  {r.get('district')}")
    print(f"\nbands: FLAG={n_flag}  REVIEW={n_review}  PASS={n_pass}  NO-DATA={n_nodata}")
    print("(read-only self-test; no files written except the flood-tract cache.)")


if __name__ == "__main__":
    main()
