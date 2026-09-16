"""wildfire_overlay — per-district wildfire exposure for the CA muni sleeve.

WHY. The earthquake work capped named-fault zones, but the sleeve's "low seismic" comfort names
(Chico/Butte, Bellevue/Sonoma, Mendocino) sit in FIRE country — and the live transmission channel
is not the burn itself (Paradise USD's GO kept paying) but INSURANCE WITHDRAWAL: insurers exiting
high-hazard zips → property unmarketable/uninsurable → market values stall → Prop 8 reassessments
and frozen turnover drag assessed value, the very base the unlimited ad-valorem levy rides on.
The historical "no school GO default" record predates this channel.

CHAIN (no GIS required — it's a table join):
  1. FEMA National Risk Index, census-tract wildfire fields (official FEMA ArcGIS service):
     WFIR_RISKS (score 0-100), WFIR_RISKR (rating), BUILDVALUE (tract building-value exposure)
  2. NCES EDGE GRF25 relationship file: school-district (LEA) <-> census-tract membership with
     land-area overlap — maps every district to its member tracts
  3. District fire metrics = building-value-weighted mean tract risk score, plus the share of
     district building value sitting in Relatively-High / Very-High tracts ("fire_high_share")

"No Rating" tracts (urban, no modeled wildfire exposure) are scored 0 — that is FEMA's meaning,
not missing data. District matching is by normalized name within the GRF's CA LEA universe
(same normalization as school_go_issuer_credit).

OUTPUT: merges fire_score / fire_high_share / fire_rating into
data/issuer_credit/issuer_credit_latest.json per CUSIP. The blend then caps high-fire par.
"""
from __future__ import annotations
import json, os, re, zipfile, difflib

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "issuer_credit")
HIGH = {"Relatively High", "Very High"}


def load_tracts() -> dict:
    rows = json.load(open(os.path.join(DATA, "nri_ca_tracts_wildfire.json")))
    out = {}
    for r in rows:
        score = r.get("WFIR_RISKS")
        rating = r.get("WFIR_RISKR") or "No Rating"
        if rating == "No Rating" or score is None:
            score = 0.0
        out[r["TRACTFIPS"]] = {"score": float(score), "rating": rating,
                               "bv": float(r.get("BUILDVALUE") or 0)}
    return out


def load_grf_ca() -> dict:
    """{normalized LEA name: [(tractfips, landarea_overlap), ...]} for CA from GRF25."""
    import openpyxl, io
    zp = zipfile.ZipFile(os.path.join(DATA, "GRF25.zip"))
    name = next(n for n in zp.namelist() if "tract" in n.lower() and n.lower().endswith(".xlsx"))
    wb = openpyxl.load_workbook(io.BytesIO(zp.read(name)), read_only=True)
    ws = wb[wb.sheetnames[0]]
    hdr = [str(c.value or "").upper() for c in next(ws.iter_rows(min_row=1, max_row=1))]
    def col(*cands):
        for c in cands:
            if c in hdr: return hdr.index(c)
        raise KeyError(f"{cands} not in {hdr}")
    i_leaid, i_name, i_tract = col("LEAID"), col("NAME_LEA25", "NAME_LEA", "NAME"), col("TRACT", "TRACTFIPS", "GEOID_TRACT")
    try: i_area = col("LANDAREA", "AREALAND", "LANDAREA_SQMI")
    except KeyError: i_area = None
    out = {}
    for row in ws.iter_rows(min_row=2, values_only=True):
        leaid = str(row[i_leaid] or "")
        if not leaid.startswith("06"):            # CA LEAs only
            continue
        nm = _norm(str(row[i_name] or ""))
        tract = str(row[i_tract] or "").zfill(11)
        area = float(row[i_area] or 0) if i_area is not None else 1.0
        out.setdefault(nm, []).append((tract, area))
    return out


_SUB = [("UNIFIED SCHOOL DISTRICT", "UNIFIED"), ("SCHOOL DISTRICT", ""), ("ELEMENTARY", "ELEMENTARY"),
        ("UNION HIGH", "UNION HIGH"), ("HIGH SCHOOL", "HIGH"), ("COMMUNITY COLLEGE DISTRICT", "COMMUNITY COLLEGE")]
def _norm(s: str) -> str:
    s = s.upper()
    for a, b in _SUB: s = s.replace(a, b)
    return re.sub(r"\s+", " ", re.sub(r"[^A-Z ]", " ", s)).strip()


def district_fire(name: str, grf: dict, tracts: dict):
    q = _norm(name)
    best, conf = None, 0.0
    for nm in grf:
        r = difflib.SequenceMatcher(None, q, nm).ratio()
        if q.split()[0] in nm: r += 0.08
        if r > conf: best, conf = nm, r
    if best is None or conf < 0.6:
        return None
    member = [(tracts[t], a) for t, a in grf[best] if t in tracts]
    if not member:
        return None
    tot_bv = sum(m["bv"] for m, _ in member) or 1.0
    score = sum(m["score"] * m["bv"] for m, _ in member) / tot_bv
    high_share = sum(m["bv"] for m, _ in member if m["rating"] in HIGH) / tot_bv
    worst = max((m["rating"] for m, _ in member),
                key=lambda r: ["No Rating", "Very Low", "Relatively Low", "Relatively Moderate",
                               "Relatively High", "Very High"].index(r))
    return {"fire_score": round(score, 1), "fire_high_share": round(high_share, 3),
            "fire_worst_tract": worst, "fire_match": best, "fire_match_conf": round(conf, 2),
            "fire_n_tracts": len(member)}


def main():
    tracts = load_tracts(); grf = load_grf_ca()
    p = os.path.join(DATA, "issuer_credit_latest.json")
    recs = json.load(open(p))
    print(f"{'cusip':11} {'fire':>5} {'hiBV%':>6} {'worst tract':18} {'conf':>4}  district")
    for r in recs:
        if not r.get("district") or r.get("cert_status") == "NOT-COVERED-CC" and not r.get("county"):
            r["fire_score"] = None; continue
        f = district_fire(r["district"], grf, tracts)
        if f: r.update(f)
        print(f"{r['cusip']:11} {(r.get('fire_score') if r.get('fire_score') is not None else -1):5.1f} "
              f"{100*(r.get('fire_high_share') or 0):6.1f} {(r.get('fire_worst_tract') or '?'):18} "
              f"{(r.get('fire_match_conf') or 0):4.2f}  {r.get('district')}")
    json.dump(recs, open(p, "w"), indent=1)
    print("merged into issuer_credit_latest.json")


if __name__ == "__main__":
    main()
