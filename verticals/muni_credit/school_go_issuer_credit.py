"""school_go_issuer_credit — PER-ISSUER credit differentiation for CA school/CC district GOs.

WHY. The grader scores every SB-222 school GO an identical 90 (security-class proxy), so the
credit column has ZERO discrimination inside a school-GO basket — and EMMA carries no agency
rating for these small issuers. This module is the substitute for the missing agency letter:
it resolves each CUSIP to its actual district and attaches verifiable per-issuer facts.

CHAIN (all free, all primary-or-derived):
  1. CUSIP -> issuer name        OpenFIGI mapping API (solves EMMA's JS-rendered-name problem)
  2. issuer -> district record   CA Dept of Education public directory (county, lat/lon, type)
  3. district -> fiscal stress   CDE Interim Status certifications (AB 1200): a district that
     cannot certify it will meet obligations files QUALIFIED or NEGATIVE — the official CA
     fiscal-distress flag (FY24-25: SFUSD & Plumas NEGATIVE; Oakland, Hayward QUALIFIED)
  4. coords -> seismic hazard    USGS design-maps ASCE7-22 (SS = short-period MCE spectral
     acceleration) + county -> named-fault zone, for single-event concentration analysis

SCORING HONESTY. An interim certification reflects OPERATING-fund stress. It does NOT impair
the GO pledge: debt service is paid from a separate ad-valorem levy, county-collected, with the
SB-222 statutory lien (Gov Code §53515); state takeovers (Inglewood 2012, Oakland 2003) did not
interrupt GO payment. So NEGATIVE/QUALIFIED deducts modestly (administration / headline /
disclosure-quality risk), not catastrophically. Community-college districts are NOT covered by
CDE K-12 certification (CCCCO monitors separately) — they are flagged not-covered, never
treated as clean ("UNVERIFIABLE != clean").

SEISMIC is reported as a separate overlay column (feeds the earthquake-concentration analysis),
NOT folded into the credit score: AV-backed GO debt service survived Loma Prieta and Northridge;
the seismic risk is portfolio CONCENTRATION (one event hitting many districts' AV + collections
at once), which is a construction constraint, not a per-issuer credit deduction.
"""
from __future__ import annotations
import json, re, time, csv, datetime, difflib, urllib.request, os
try:
    import accjc_overlay as ACCJC                # CCD accreditation = the CC analog of AB-1200 (resilient import)
except Exception:
    ACCJC = None
# ACCJC accreditation status -> our cert_status. A CCD GO is the same security as a K-12 GO; accreditation
# is its fiscal-distress proxy (AB-1200 is K-12-only). good standing grades like a Positive cert.
# District/OpenFIGI-abbrev name -> the ACCJC college name, for CCDs whose bond/issuer name doesn't
# auto-resolve to the accreditation roster (single-college districts named for the place, not the college).
_CC_COLLEGE_HINT = {
    "imperial": "Imperial Valley College",
    "s wstrn": "Southwestern College", "southwestern": "Southwestern College",
}
def _cc_college_hint(name):
    n = (name or "").lower()
    for k, v in _CC_COLLEGE_HINT.items():
        if k in n:
            return v
    return None


CC_CERT = {"good_standing": "CC-ACCREDITED", "warning": "CC-WARNING", "probation": "CC-PROBATION",
           "show_cause": "CC-SHOWCAUSE", "restoration": "CC-RESTORATION", "unknown": "CC-UNKNOWN"}

def cert_contribution(cs):
    """Map a cert_status to (hard_flags, soft_flags) for the underwrite/regrade. CCD accreditation grades
    like AB-1200: good standing = no flag, probation/show-cause = hard, warning/restoration/unknown/
    uncovered = soft REVIEW (a CCD never auto-excludes on missing data — Option C floor)."""
    hard, soft = [], []
    if cs in ("NEGATIVE", "QUALIFIED"): hard.append(f"fiscal:{cs}")
    elif cs in ("CC-PROBATION", "CC-SHOWCAUSE"): hard.append(f"CC-sanction:{cs[3:].lower()}")
    elif cs in ("CC-WARNING", "CC-RESTORATION", "CC-UNKNOWN", "NOT-COVERED-CC"): soft.append(f"CC-review:{cs}")
    # CC-ACCREDITED / POSITIVE* / N/A-REVENUE -> no cert flag
    if (cs or "").startswith("UNRESOLVED"): hard.append("unresolved-geo")
    return hard, soft

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "issuer_credit")
ASOF = "2026-06-10"

# ---------------- 1. OpenFIGI: CUSIP -> issuer name ----------------
def resolve_cusips(cusips: list[str]) -> dict:
    out = {}
    for i in range(0, len(cusips), 10):                       # keyless: 10 jobs/req, 25 req/min
        batch = cusips[i:i + 10]
        req = urllib.request.Request(
            "https://api.openfigi.com/v3/mapping",
            data=json.dumps([{"idType": "ID_CUSIP", "idValue": c} for c in batch]).encode(),
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as r:
            res = json.loads(r.read())
        for cu, item in zip(batch, res):
            d = (item.get("data") or [{}])[0]
            out[cu] = {"figi_name": d.get("name"), "figi_ticker": d.get("ticker")}
        time.sleep(2.6)
    return out


# ---------------- 2. CDE directory: district -> county/coords ----------------
def load_cde_directory(path=None) -> list[dict]:
    path = path or os.path.join(DATA, "cde_districts_20260610.txt")
    rows = []
    with open(path, encoding="utf-8", errors="replace") as f:
        rd = csv.DictReader(f, delimiter="\t")
        for r in rd:
            if (r.get("StatusType") or "").strip() != "Active":
                continue
            try: lat, lon = float(r["Latitude"]), float(r["Longitude"])
            except (ValueError, KeyError, TypeError): lat = lon = None
            rows.append({"district": r["District"].strip(), "county": r["County"].strip(),
                         "lat": lat, "lon": lon, "doc": (r.get("DOCType") or "").strip()})
    return rows


_SUB = [("UNIF SCH DIST", "UNIFIED"), ("UNIF SD", "UNIFIED"), ("UNIF", "UNIFIED"),
        ("USD", "UNIFIED"), ("UHSD", "UNION HIGH"), ("UESD", "UNION ELEMENTARY"),
        ("ELEM SCH DIST", "ELEMENTARY"), ("ELEM SD", "ELEMENTARY"), ("ELEM", "ELEMENTARY"),
        ("ESD", "ELEMENTARY"),                                         # FIGI: Elementary Sch Dist
        ("HIGH SCH DIST", "HIGH"), ("HSD", "HIGH"), ("HS", "HIGH"),
        ("SCH DIST", ""), ("SD", ""), ("SCHS", ""), ("SCH", ""),
        ("CMNTY COLLEGE DIST", "COMMUNITY COLLEGE"), ("CMNTY COLL", "COMMUNITY COLLEGE"),
        ("CCD", "COMMUNITY COLLEGE"), ("CMNTY", "COMMUNITY COLLEGE"),   # bare CMNTY = CC in muni tickers
        ("CLG", "COMMUNITY COLLEGE"), ("COLL", "COMMUNITY COLLEGE"),    # FIGI: 'CLG'/'COLL' = college
        ("JT", "JOINT"), ("UN ", "UNION "), ("VLY", "VALLEY"),          # FIGI place shorthand (Victor VLY)
        ("DT", "")]                                                     # FIGI: 'DT' = District (CLG DT)

def _norm(name: str) -> str:
    s = re.sub(r"[-#].*$", "", (name or "").upper())          # strip series suffixes "-A-2016", "SCH#1"
    s = re.sub(r"\bCA(LIF(ORNIA)?)?\b", "", s)
    for a, b in _SUB:
        s = re.sub(r"\b" + re.escape(a) + r"\b", b, s)
    s = re.sub(r"\b(\w+)( \1\b)+", r"\1", s)                   # collapse immediate dup words (COMMUNITY COMMUNITY)
    return re.sub(r"\s+", " ", re.sub(r"[^A-Z ]", " ", s)).strip()


# District TYPE class — the most discriminating token (Elementary vs High vs Unified vs College).
# A FIGI name whose type is known must NOT silently bind to a directory district of a different type.
_CC_RE = re.compile(r"\b(C(MN?TY)?\s*COLL(EGE)?|CLG|CCD|JR\s*COLL)\b")
def _is_college(figi_name: str, ticker: str = "") -> bool:
    if _CC_RE.search((figi_name or "").upper()): return True
    return "HGR" in (ticker or "").upper()                    # FIGI muni ticker higher-ed marker (PVDHGR)

def _type_of(s: str) -> str | None:
    s = (s or "").upper()
    if "COMMUNITY COLLEGE" in s or "CCCCO" in s: return "CC"
    if "UNIFIED" in s: return "UNIFIED"
    if "HIGH" in s: return "HIGH"
    if "ELEMENTARY" in s: return "ELEM"
    return None


def match_district(figi_name: str, directory: list[dict],
                   ticker: str = "") -> tuple[dict | None, float, dict]:
    """Returns (district_row|None, confidence, info). info carries ambiguity/type diagnostics so the
    caller can route low-confidence or type-ambiguous resolutions to authoritative confirmation (the
    EMMA Official Statement) instead of silently labeling the wrong same-place-name entity."""
    q = _norm(figi_name)
    info = {"ambiguous": False, "type_mismatch": False, "runner_up": None, "qtype": None}
    if not q: return None, 0.0, info
    if _is_college(figi_name, ticker):                        # CCs aren't in the K-12 directory at all
        return ({"district": figi_name, "county": None, "lat": None, "lon": None,
                 "doc": "Community College (CCCCO)"}, 0.99, {**info, "qtype": "CC"})
    qtype = _type_of(q); info["qtype"] = qtype
    scored = []
    for d in directory:
        c = _norm(d["district"])
        r = difflib.SequenceMatcher(None, q, c).ratio()
        if q.split()[0] in c: r += 0.08                       # anchor on the place-name token
        dtype = _type_of(d.get("doc") or d["district"])
        if qtype and dtype and qtype != dtype: r -= 0.25      # TYPE-AGREEMENT gate: cross-type = heavy penalty
        scored.append((r, d, dtype))
    scored.sort(key=lambda x: -x[0])
    (score, best, btype) = scored[0]
    if len(scored) > 1:
        s2, d2, t2 = scored[1]
        # ambiguous when the runner-up is within a hair AND is a different real entity (different place
        # or different type) — the two silent-mislabel cases (Palo Verde USD-vs-CC, Victor Elem-vs-Valley).
        if score - s2 < 0.05 and (d2["district"] != best["district"]):
            info.update(ambiguous=True, runner_up=f"{d2['district']} ({s2:.2f})")
        if qtype and btype and qtype != btype:
            info["type_mismatch"] = True
    if score < 0.62:
        return None, score, info
    return best, score, info


# ---------------- 3. CDE interim certification (AB 1200 fiscal stress) ----------------
def _fy_code(yr=None, month=None):
    """CDE interim-cert fiscal-year code (e.g. '2526' for FY2025-26). The academic FY ends in June, so
    Jan-Jun belongs to the FY that started the prior July."""
    today = datetime.date.today()
    yr = yr or today.year; month = month or today.month
    end = yr if month >= 7 else yr        # FY2025-26's 2nd interim lands ~Mar-Apr 2026 -> end year 2026
    return f"{str(end-1)[2:]}{str(end)[2:]}"

# Full Chrome fingerprint — CDE sits behind a Radware captcha that a bare UA does NOT pass but the
# complete Sec-Ch-Ua / Sec-Fetch-* set does (the gated-gov-portal playbook).
_UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
                     "Chrome/124.0.0.0 Safari/537.36",
       "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
       "Accept-Language": "en-US,en;q=0.9", "Upgrade-Insecure-Requests": "1",
       "Sec-Ch-Ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
       "Sec-Ch-Ua-Mobile": "?0", "Sec-Ch-Ua-Platform": '"macOS"',
       "Sec-Fetch-Dest": "document", "Sec-Fetch-Mode": "navigate", "Sec-Fetch-Site": "none",
       "Sec-Fetch-User": "?1", "Referer": "https://www.cde.ca.gov/fg/fi/ir/"}

def refresh_certifications(codes=None):
    """Re-fetch the CDE interim certification lists for the current (and prior) fiscal year and cache them.
    FIX 2026-06-20: the cache was a full CYCLE stale (held FY24-25 while Antioch was certified NEGATIVE in
    FY25-26), so AB-1200 downgrades were missed. Run from the daily cron each interim period."""
    codes = codes or [_fy_code(), _fy_code(datetime.date.today().year - 1, 12)]  # current FY + prior FY
    got = []
    for code in dict.fromkeys(codes):
        for per in ("first", "second"):
            url = f"https://www.cde.ca.gov/fg/fi/ir/{per}{code}.asp"
            try:
                html = urllib.request.urlopen(urllib.request.Request(url, headers=_UA), timeout=30).read().decode("utf-8", "replace")
                if "ertification" in html:                       # sanity: it's a cert page, not a 404
                    open(os.path.join(DATA, f"cde_{per}{code}.html"), "w", encoding="utf-8").write(html)
                    got.append(f"cde_{per}{code}.html")
            except Exception as e:
                print(f"[cert-refresh] {url} -> {e}")
            time.sleep(0.5)
    return got

def parse_certifications() -> dict:
    """{normalized district name: ('NEGATIVE'|'QUALIFIED', period)} from ALL cached CDE cert pages, newest
    period winning (so a current-FY downgrade overrides a prior-FY clean read)."""
    import glob
    out = {}
    files = glob.glob(os.path.join(DATA, "cde_first[0-9][0-9][0-9][0-9].html")) + \
            glob.glob(os.path.join(DATA, "cde_second[0-9][0-9][0-9][0-9].html"))
    def key(p):                                                  # sort oldest->newest so newest overwrites
        b = os.path.basename(p); code = b[-9:-5]; per = 0 if "first" in b else 1
        return (code, per)
    for p in sorted(files, key=key):
        b = os.path.basename(p); period = f"FY{b[-9:-7]}-{b[-7:-5]} {'1st' if 'first' in b else '2nd'} interim"
        t = open(p, encoding="utf-8", errors="replace").read()
        sections = re.split(r"Qualified Certification", t, maxsplit=1)
        for sec, label in zip(sections, ["NEGATIVE", "QUALIFIED"]):
            for row in re.findall(r"<tr[^>]*>(.*?)</tr>", sec, re.S):
                cells = [re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", c)).strip()
                         for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, re.S)]
                if len(cells) >= 3 and cells[0].isdigit():
                    out[_norm(cells[2])] = (label, period, cells[1])
    return out


# ---------------- 4. USGS seismic hazard ----------------
def seismic_ss(lat, lon) -> float | None:
    if lat is None: return None
    url = (f"https://earthquake.usgs.gov/ws/designmaps/asce7-22.json?latitude={lat}"
           f"&longitude={lon}&riskCategory=II&siteClass=Default&title=s")
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            d = json.loads(r.read())
        return round(float(d["response"]["data"]["ss"]), 2)
    except Exception:
        return None


FAULT_ZONE = {  # county -> named-fault system for single-event concentration
 "BAY (San Andreas N / Hayward)": ["San Francisco", "Alameda", "Contra Costa", "San Mateo",
     "Santa Clara", "Marin", "Sonoma", "Napa", "Solano", "Santa Cruz"],
 "LA BASIN (San Andreas S / Newport-Inglewood / Puente Hills)": ["Los Angeles", "Orange", "Ventura"],
 "INLAND EMPIRE (San Andreas S / San Jacinto)": ["Riverside", "San Bernardino"],
 "SAN DIEGO (Rose Canyon / Elsinore)": ["San Diego", "Imperial"],
 "CENTRAL VALLEY / SIERRA (low)": ["Sacramento", "San Joaquin", "Stanislaus", "Merced", "Fresno",
     "Kings", "Tulare", "Kern", "Yolo", "Placer", "Sutter", "Butte", "Madera", "El Dorado"],
}
def fault_zone(county):
    for z, cs in FAULT_ZONE.items():
        if county in cs: return z
    return "OTHER CA" if county else None


# ---------------- 5. Score ----------------
def score_issuer(rec: dict) -> dict:
    base, notes = 90, []     # SB-222 statutory first lien on an unlimited ad-valorem levy
    cert = rec.get("cert_status")
    if cert == "NEGATIVE":
        base -= 14; notes.append("NEGATIVE interim certification (official CA fiscal-distress flag): "
            "GO lien intact & county-collected, but state-administration/headline/disclosure risk")
    elif cert == "QUALIFIED":
        base -= 6; notes.append("QUALIFIED interim certification: operating-fund stress, GO lien unaffected")
    elif cert == "NOT-COVERED-CC":
        notes.append("community-college district: CDE certification does not apply (CCCCO monitors); "
                     "fiscal-stress status UNVERIFIED, not clean")
    elif cert == "UNRESOLVED":
        base -= 2; notes.append("issuer->district resolution failed; fiscal status UNVERIFIED")
    rec["credit_score"] = base
    rec["credit_notes"] = "; ".join(notes) if notes else "no AB 1200 stress flag on record"
    return rec


# Revenue/utility bonds (sewer, water, wastewater, financing authority, pollution-control, PFA) are NOT
# tax-secured GOs and must NOT be matched to a same-place-name school district (the Tulare 899124 case:
# "TULARE SWR REV-REF" / ticker CA TULUTL was matched to Tulare City school district). Fires on a revenue
# marker UNLESS a school marker is also present (so "ENTERPRISE SD" = the Enterprise *school* district,
# not a revenue bond, stays school). Keyed off the FIGI name + ticker.
_REV_KW = re.compile(r"\b(SWR|SEWER|WASTEWATER|WTR|WATER|UTIL|UTL|SANITAT\w*|POLLUTION|PFA|PUBLIC FAC\w*"
                     r"|ELECTRIC|ELEC|PWR|POWER|PUB\s*PWR|\bIRR\b|IRRIG\w*|FINANC\w*\s*AUTH\w*|FING\s*AUTH\w*"
                     r"|ENTERPRISE\s*REV|REVENUE|\bREV\b)\b")
_SCHOOL_KW = re.compile(r"\b(SD|SCD|USD|ESD|HSD|UHSD|UESD|CCD|SCH|SCHOOL|ELEM|UNIF\w*|HIGH|COLL\w*|CLG|EDU\w*)\b")
def _is_revenue(figi_name: str, ticker: str = "") -> bool:
    s = (figi_name or "").upper() + " " + (ticker or "").upper()
    if _SCHOOL_KW.search(s): return False        # a school marker wins (Enterprise SD, etc.)
    return bool(_REV_KW.search(s))


def analyze(cusips: list[str]) -> list[dict]:
    directory = load_cde_directory()
    certs = parse_certifications()
    names = resolve_cusips(cusips)
    out = []
    for cu in cusips:
        nm = names.get(cu, {})
        if _is_revenue(nm.get("figi_name"), nm.get("figi_ticker")):   # revenue/utility -> water track, NOT a school GO
            rec = {"cusip": cu, "issuer": nm.get("figi_name"), "match_conf": 0.0, "is_revenue": True,
                   "pledge": "water", "district": None, "county": None, "lat": None, "lon": None,
                   "cert_status": "N/A-REVENUE", "seismic_ss": None, "fault_zone": None, "credit_score": None}
            out.append(rec); time.sleep(0.1); continue
        d, conf, info = match_district(nm.get("figi_name") or "", directory, nm.get("figi_ticker") or "")
        rec = {"cusip": cu, "issuer": nm.get("figi_name"), "match_conf": round(conf, 2),
               "district": d["district"] if d else None, "county": d["county"] if d else None,
               "lat": d["lat"] if d else None, "lon": d["lon"] if d else None,
               "match_ambiguous": info.get("ambiguous"), "match_runner_up": info.get("runner_up")}
        if d and d.get("doc") == "Community College (CCCCO)":
            rec["cert_status"] = "NOT-COVERED-CC"             # ACCJC accreditation = the CCD fiscal proxy
            if ACCJC:
                try:
                    _nm = rec.get("issuer") or rec.get("district") or ""
                    a = ACCJC.accjc_status(_nm, college_hint=_cc_college_hint(_nm))
                    rec["accjc_status"] = a.get("accjc_status"); rec["accjc_sanction"] = a.get("accjc_sanction")
                    rec["accjc_match"] = a.get("accjc_match")
                    rec["cert_status"] = CC_CERT.get(a.get("accjc_status"), "NOT-COVERED-CC")
                    rec["cert_detail"] = (f"ACCJC {a.get('accjc_status')} ({a.get('confidence')})"
                                          + (f": {a['accjc_sanction']}" if a.get("accjc_sanction") else ""))
                except Exception:
                    pass
        elif not d:
            rec["cert_status"] = "UNRESOLVED"
        elif info.get("ambiguous"):
            # do NOT silently pick one of two plausible same-place-name entities — route to OS confirmation
            rec["cert_status"] = "UNRESOLVED-AMBIG"
            rec["cert_detail"] = f"matcher: {d['district']} vs {info['runner_up']} — confirm vs EMMA OS issuer"
        else:
            hit = certs.get(_norm(d["district"]))
            rec["cert_status"] = hit[0] if hit else "POSITIVE(absent)"
            if hit: rec["cert_detail"] = f"{hit[1]}, {hit[2]} County"
        rec["seismic_ss"] = seismic_ss(rec["lat"], rec["lon"])
        rec["fault_zone"] = fault_zone(rec["county"])
        out.append(score_issuer(rec))
        time.sleep(0.4)
    # cross-CUSIP collision guard: distinct CUSIP-6 issuers should not collapse to ONE district (the
    # Victor-Elementary failure — both 926055 and 925836 fuzzy-matched to it). Flag every colliding set.
    from collections import defaultdict
    by_dist = defaultdict(set)
    for r in out:
        if r.get("district"): by_dist[r["district"]].add(r["cusip"][:6])
    for r in out:
        if r.get("district") and len(by_dist[r["district"]]) > 1 and r["cert_status"] not in (
                "UNRESOLVED", "UNRESOLVED-AMBIG"):
            r["cert_status"] = "UNRESOLVED-COLLISION"
            r["cert_detail"] = (f"{len(by_dist[r['district']])} distinct CUSIP-6 mapped to "
                                f"'{r['district']}' — confirm each vs EMMA OS issuer")
    return out


if __name__ == "__main__":
    import sys
    cusips = sys.argv[1:]
    if not cusips:    # default: all school/CC GOs across the current baskets
        seen = []
        for fn in ("muni_etf_option_B_highyield.json", "muni_etf_option_A_execclean.json"):
            try: d = json.load(open(fn))
            except FileNotFoundError: continue
            for b in d["barbell"]:
                sec = (b.get("sectype") or b.get("security") or "")
                if ("SCHOOL" in sec.upper() or "school" in sec) and b["cusip"] not in seen:
                    seen.append(b["cusip"])
        cusips = seen
    res = analyze(cusips)
    # MERGE into the shared overlay (do NOT overwrite — a partial run must not wipe other issuers'
    # records or their wildfire_overlay fire fields, which this module doesn't compute). 2026-06-17.
    p = "data/issuer_credit/issuer_credit_latest.json"
    try: existing = {r["cusip"]: r for r in json.load(open(p))}
    except Exception: existing = {}
    for r in res:
        old = existing.get(r["cusip"], {})
        for k in ("fire_score", "fire_high_share", "fire_worst_tract"):   # preserve fire (set elsewhere)
            if old.get(k) is not None and r.get(k) is None: r[k] = old[k]
        existing[r["cusip"]] = r
    json.dump(list(existing.values()), open(p, "w"), indent=1, default=str)
    print(f"{'cusip':11} {'cr':>3} {'cert':18} {'SS':>5} {'county':15} {'conf':>4}  district")
    for r in res:
        print(f"{r['cusip']:11} {r['credit_score']:3d} {(r['cert_status'] or ''):18} "
              f"{(r['seismic_ss'] if r['seismic_ss'] is not None else -1):5.2f} "
              f"{(r['county'] or '?'):15} {r['match_conf']:4.2f}  {r['district'] or r['issuer']}")
