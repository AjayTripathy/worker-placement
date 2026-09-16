"""fiscal_health — deepened OPERATING-fiscal-health screen for CA school-district GO issuers.

WHY. We currently proxy a district's operating health with the binary AB-1200 interim
certification (POSITIVE / QUALIFIED / NEGATIVE) from school_go_issuer_credit. That is a
single bit. Two more-granular operating dimensions predict the path to a FCMAT takeover /
state receivership long before the cert flips — the Stockton Unified arc (2023 FCMAT
fraud/governance finding, chronic deficit, multi-year enrollment slide):

  1. ENROLLMENT TREND. CA LCFF operating revenue is funded per-ADA (average daily
     attendance, which tracks enrollment). A multi-year enrollment decline mechanically
     erodes the operating base year after year — the slow squeeze behind most distress.
     Source: CA Dept of Education public enrollment census (cde.ca.gov downloadable files).
     We compute a multi-year enrollment CAGR per district.

  2. PENSION / OPEB BURDEN. The district's net pension liability (CalSTRS + CalPERS
     proportionate share) + total/net OPEB liability, scaled by general-fund revenue, from
     the audited ACFR / EMMA continuing-disclosure annual. A heavy long-term-liability stack
     on a shrinking revenue base is the structural-deficit driver.

WHAT THIS IS NOT — GO INSULATION. These are OPERATING (general-fund) stresses. The GO
bonds are paid from a SEPARATE, county-collected ad-valorem tax levy with the SB-222
statutory lien (Gov Code §53515); state takeovers (Inglewood 2012, Oakland 2003, and the
Stockton FCMAT involvement) did NOT interrupt GO debt service. So every flag here is a
MARKETABILITY / HEADLINE / TAIL flag (wider spread on distress headlines, harder secondary
liquidity, governance-event disclosure risk) — NOT a default flag on the GO. The module
states this explicitly in every output (`flag_frame`).

HONESTY. UNVERIFIABLE != clean. A community-college district has no K-12 enrollment census
and no AB-1200 cert (CCCCO monitors separately) -> enrollment and cert dimensions return NA
/ UNVERIFIABLE, never a clean pass. If the audited financials aren't in hand, the pension/
OPEB dimension degrades to UNVERIFIABLE rather than asserting a low burden.

DATA SOURCES (all free / primary).
  Enrollment, 2017-18..2022-23 : www3.cde.ca.gov/demo-downloads/enrsch/enr<span>-v*.txt
       (legacy school-level; rows split by race/gender/ENR_TYPE; ENR_TYPE C duplicates P,
        so sum ENR_TOTAL over ONE type only; aggregate to district by 7-digit CDS prefix)
  Enrollment, 2023-24..2024-25 : www3.cde.ca.gov/demo-downloads/census/cdenroll<yr>.txt
       (CALPADS census-day; the district total is the row with blank SchoolCode,
        Charter='ALL', ReportingCategory='TA')
  Pension/OPEB                 : audited ACFR / EMMA continuing-disclosure PDF text already
                                 saved under outputs/diligence_reports/<cusip>/raw/.

District -> CDS code mapping reuses school_go_issuer_credit.load_cde_directory() (the CDE
directory file carries the 7-digit 'CD Code'); we extend the loaded record to carry it.
"""
from __future__ import annotations
import csv, io, json, os, re, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
DD = os.path.join(HERE, "outputs", "diligence_reports")
CACHE_PATH = os.path.join(DATA, "cde_enrollment_cache.json")
DIRECTORY_FILE = os.path.join(DATA, "issuer_credit", "cde_districts_20260610.txt")

ASOF = "2026-06-19"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

# Every flag this module raises is a marketability/headline/tail flag on a general-fund
# operating stress — NOT a default flag on the (separately-secured, ad-valorem-levied) GO.
FLAG_FRAME = ("OPERATING/general-fund stress; GO debt service is on a separate county-collected "
              "ad-valorem levy (SB-222 lien, Gov Code 53515) and is NOT impaired by these — "
              "treat as marketability/headline/tail risk, not default risk.")

# ---- thresholds -----------------------------------------------------------------
# Enrollment CAGR (annualized, over the measured span). Worse than soft -> REVIEW (soft);
# worse than hard -> a harder marketability flag.
ENROLL_CAGR_SOFT = -0.02      # -2%/yr : sustained erosion of the per-ADA operating base
ENROLL_CAGR_HARD = -0.04      # -4%/yr : steep slide (accelerates structural deficit)
# Long-term-liability burden = (net pension liability + net/total OPEB liability) / GF revenue.
PENSION_OPEB_SOFT = 0.50      # >0.5x GF revenue : elevated
PENSION_OPEB_HARD = 1.00      # >1.0x GF revenue : heavy stack on the operating base


# ---------------- year -> enrollment-file source map ----------------
# (url, kind). kind="hist" legacy school-level; kind="census" CALPADS census-day.
_ENR_SOURCES = {
    "2017-18": ("https://www3.cde.ca.gov/demo-downloads/enrsch/enr201719-v2.txt", "hist"),
    "2018-19": ("https://www3.cde.ca.gov/demo-downloads/enrsch/enr201719-v2.txt", "hist"),
    "2019-20": ("https://www3.cde.ca.gov/demo-downloads/enrsch/enr201719-v2.txt", "hist"),
    "2020-21": ("https://www3.cde.ca.gov/demo-downloads/enrsch/enr202022-v2.txt", "hist"),
    "2021-22": ("https://www3.cde.ca.gov/demo-downloads/enrsch/enr202022-v2.txt", "hist"),
    "2022-23": ("https://www3.cde.ca.gov/demo-downloads/enrsch/enr202022-v2.txt", "hist"),
    "2023-24": ("https://www3.cde.ca.gov/demo-downloads/census/cdenroll2324-v2.txt", "census"),
    "2024-25": ("https://www3.cde.ca.gov/demo-downloads/census/cdenroll2425.txt", "census"),
}
# Build a CAGR over the widest available window ending at the latest year (~5y span).
_TARGET_LATEST = "2024-25"
_TARGET_BASE = "2019-20"


# ---------------- 1. district -> 7-digit CDS code ----------------
def load_directory_with_cds(path: str | None = None) -> list[dict]:
    """CDE public directory, carrying the 7-digit county-district 'CD Code'. Extends what
    school_go_issuer_credit.load_cde_directory returns (which drops the code)."""
    path = path or DIRECTORY_FILE
    rows = []
    with open(path, encoding="utf-8", errors="replace") as f:
        rd = csv.DictReader(f, delimiter="\t")
        for r in rd:
            if (r.get("StatusType") or "").strip() != "Active":
                continue
            cds = (r.get("CD Code") or "").strip()
            rows.append({"district": (r.get("District") or "").strip(),
                         "county": (r.get("County") or "").strip(),
                         "doctype": (r.get("DOCType") or "").strip(),
                         "cds7": cds.zfill(7) if cds.isdigit() else cds})
    return rows


def _norm(s: str) -> str:
    s = (s or "").upper()
    s = re.sub(r"\bCA(LIF(ORNIA)?)?\b", "", s)
    s = re.sub(r"\b(SCHOOL )?DISTRICT\b", "", s)
    s = re.sub(r"[^A-Z ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def resolve_cds(district_name: str, county: str | None = None,
                directory: list[dict] | None = None) -> dict:
    """Resolve a district name (+ optional county) to its 7-digit CDS and DOCType.

    Community-college / higher-ed names are flagged is_cc=True (they are NOT in the K-12
    directory; their enrollment & AB-1200 dimensions are NA)."""
    directory = directory if directory is not None else load_directory_with_cds()
    nm = _norm(district_name)
    is_cc = bool(re.search(r"\b(COMMUNITY COLLEGE|COLLEGE|CMNTY|CCD|JR COLL)\b",
                           (district_name or "").upper()))
    if is_cc:
        return {"cds7": None, "doctype": "Community College (CCCCO)", "is_cc": True,
                "matched_name": district_name, "confidence": 0.99, "county": county}
    cands = directory
    if county:
        cn = _norm(county)
        sub = [d for d in directory if _norm(d["county"]) == cn]
        if sub:
            cands = sub
    best, best_score = None, 0.0
    for d in cands:
        dn = _norm(d["district"])
        if dn == nm:
            best, best_score = d, 1.0
            break
        # token-overlap Jaccard, then prefix bonus
        a, b = set(nm.split()), set(dn.split())
        if not a or not b:
            continue
        j = len(a & b) / len(a | b)
        if dn.startswith(nm) or nm.startswith(dn):
            j = max(j, 0.9)
        if j > best_score:
            best, best_score = d, j
    if not best or best_score < 0.5:
        return {"cds7": None, "doctype": None, "is_cc": False,
                "matched_name": None, "confidence": best_score, "county": county}
    return {"cds7": best["cds7"], "doctype": best["doctype"], "is_cc": False,
            "matched_name": best["district"], "confidence": round(best_score, 2),
            "county": best["county"]}


# ---------------- 2. enrollment series (CDE), cached ----------------
def _load_cache() -> dict:
    if os.path.exists(CACHE_PATH):
        try:
            with open(CACHE_PATH) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _save_cache(c: dict) -> None:
    os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
    tmp = CACHE_PATH + ".tmp"
    with open(tmp, "w") as f:
        json.dump(c, f, indent=2, sort_keys=True)
    os.replace(tmp, CACHE_PATH)


def _stream_lines(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                               "Accept-Language": "en-US,en;q=0.9"})
    with urllib.request.urlopen(req, timeout=180) as r:
        buf = io.TextIOWrapper(r, encoding="utf-8", errors="replace")
        header = buf.readline().rstrip("\n").split("\t")
        idx = {name: i for i, name in enumerate(header)}
        for line in buf:
            yield line.rstrip("\n").split("\t"), idx


def _district_totals_for_year(year: str) -> dict[str, int]:
    """Return {cds7: total_enrollment} for ALL districts in the given year's source file.
    Streamed so we never hold the 30-95 MB file in memory; we extract every district total
    in one pass and cache them, so subsequent districts hit cache."""
    url, kind = _ENR_SOURCES[year]
    totals: dict[str, int] = {}
    if kind == "hist":
        # legacy: school-level; ENR_TYPE 'C' duplicates 'P' (verified), so count one type.
        # district key = first 7 chars of 14-digit CDS_CODE. Sum ENR_TOTAL over P-type rows.
        for cols, idx in _stream_lines(url):
            try:
                if cols[idx["ACADEMIC_YEAR"]] != year:
                    continue
                if cols[idx["ENR_TYPE"]] != "P":
                    continue
                cds14 = cols[idx["CDS_CODE"]]
                cds7 = cds14[:7]
                v = int(cols[idx["ENR_TOTAL"]] or 0)
            except (KeyError, ValueError, IndexError):
                continue
            totals[cds7] = totals.get(cds7, 0) + v
    else:
        # census: district total = blank SchoolCode, Charter='ALL', ReportingCategory='TA'
        for cols, idx in _stream_lines(url):
            try:
                if cols[idx["SchoolCode"]].strip() not in ("", "0000000"):
                    continue
                if cols[idx["Charter"]] != "ALL":
                    continue
                if cols[idx["ReportingCategory"]] != "TA":
                    continue
                cc = cols[idx["CountyCode"]].strip().zfill(2)
                dd = cols[idx["DistrictCode"]].strip().zfill(5)
                if not cc.isdigit() or not dd.isdigit() or dd == "00000":
                    continue
                cds7 = cc + dd
                totals[cds7] = int(cols[idx["TOTAL_ENR"]] or 0)
            except (KeyError, ValueError, IndexError):
                continue
    return totals


def enrollment_series(cds7: str, years: list[str] | None = None,
                      refresh: bool = False) -> dict[str, int]:
    """Enrollment by year for one district (by 7-digit CDS). Uses + populates the on-disk
    per-year district-totals cache, so the first district in a year pays the download and
    every later one is free."""
    years = years or list(_ENR_SOURCES.keys())
    cache = _load_cache()
    by_year = cache.get("by_year", {})
    out: dict[str, int] = {}
    dirty = False
    for y in years:
        if refresh or y not in by_year:
            by_year[y] = {k: v for k, v in _district_totals_for_year(y).items()}
            dirty = True
        v = by_year[y].get(cds7)
        if v is not None:
            out[y] = v
    if dirty:
        cache["by_year"] = by_year
        cache["_source_map"] = {y: _ENR_SOURCES[y][0] for y in _ENR_SOURCES}
        cache["asof"] = ASOF
        _save_cache(cache)
    return out


def _cagr(series: dict[str, int]) -> tuple[float | None, str | None, str | None]:
    """Annualized enrollment CAGR over the widest available window. Returns
    (cagr, base_year, latest_year)."""
    yrs = sorted(series.keys())
    if len(yrs) < 2:
        return None, None, None
    base, latest = yrs[0], yrs[-1]
    # prefer the canonical ~5y window if both endpoints present
    if _TARGET_BASE in series and _TARGET_LATEST in series:
        base, latest = _TARGET_BASE, _TARGET_LATEST
    v0, v1 = series[base], series[latest]
    if v0 <= 0 or v1 <= 0:
        return None, base, latest
    span = int(latest[:4]) - int(base[:4])
    if span <= 0:
        return None, base, latest
    return (v1 / v0) ** (1.0 / span) - 1.0, base, latest


# ---------------- 3. pension / OPEB burden (audited financials) ----------------
_PDF_CACHE: dict[str, str] = {}


def _pdf_text(path: str) -> str:
    if path in _PDF_CACHE:
        return _PDF_CACHE[path]
    txt = ""
    try:
        from pypdf import PdfReader  # type: ignore
        txt = "\n".join((pg.extract_text() or "") for pg in PdfReader(path).pages)
    except Exception:
        try:
            import subprocess
            txt = subprocess.run(["pdftotext", "-layout", path, "-"],
                                 capture_output=True, text=True, timeout=120).stdout
        except Exception:
            txt = ""
    _PDF_CACHE[path] = txt
    return txt


def _num(s: str) -> float | None:
    m = re.search(r"\(?\$?\s*([0-9]{1,3}(?:,[0-9]{3})+|[0-9]{4,})(?:\.[0-9]+)?\)?", s)
    if not m:
        return None
    val = float(m.group(1).replace(",", ""))
    return -val if "(" in s and ")" in s else val


def _first_after(text: str, label_re: str, want_positive: bool = False,
                 min_abs: float = 1000.0) -> float | None:
    """Dollar amount on the same line as a label match. Scans ALL occurrences of the label
    (audit text repeats line items across the statement-of-net-position, RSI schedules and
    notes) and returns the modal plausible value, so a single mis-extracted occurrence (a
    negative deferred-inflow column, or a page-number artifact) doesn't win. When
    want_positive, parenthesized/negative hits are skipped — a *liability* line item is a
    positive balance; a negative there is the wrong column."""
    vals = []
    for line in text.splitlines():
        m = re.search(label_re, line, re.I)
        if not m:
            continue
        v = _num(line[m.end():])
        if v is None or abs(v) < min_abs:
            continue
        if want_positive and v <= 0:
            continue
        vals.append(v)
    if not vals:
        return None
    # modal value (most-repeated figure across the document) breaks ties robustly
    from collections import Counter
    return Counter(vals).most_common(1)[0][0]


def parse_pension_opeb(audit_path: str) -> dict:
    """Extract net pension liability + net/total OPEB liability + GF revenue from an audited
    ACFR / continuing-disclosure PDF or text file. Heuristic + best-effort; returns a
    `confidence` and degrades values to None when a figure can't be pinned (caller then
    marks the dimension UNVERIFIABLE)."""
    if not audit_path or not os.path.exists(audit_path):
        return {"available": False}
    text = _pdf_text(audit_path) if audit_path.lower().endswith(".pdf") else \
        open(audit_path, encoding="utf-8", errors="replace").read()
    if not text.strip():
        return {"available": False, "note": "no extractable text"}

    # Liabilities are positive balances; require positive and material (>= $1M) values so a
    # mis-read deferred-inflow/"change" column or a page-number artifact is rejected (degrade
    # to UNVERIFIABLE) rather than fabricating a (possibly negative) ratio.
    npl = _first_after(text, r"\bnet pension liabilit(y|ies)\b",
                       want_positive=True, min_abs=1_000_000)
    opeb = (_first_after(text, r"\bnet OPEB liabilit(y|ies)\b",
                         want_positive=True, min_abs=1_000_000)
            or _first_after(text, r"\btotal OPEB liabilit(y|ies)\b",
                            want_positive=True, min_abs=1_000_000))
    gf_rev = (_first_after(text, r"general fund\s+total revenues", want_positive=True,
                           min_abs=1_000_000)
              or _first_after(text, r"\btotal revenues\b", want_positive=True,
                              min_abs=1_000_000))

    comps = {"net_pension_liability": npl, "opeb_liability": opeb,
             "general_fund_revenue": gf_rev}
    found = sum(v is not None for v in comps.values())
    ratio = None
    if npl is not None and gf_rev and gf_rev > 0:
        ratio = round((npl + (opeb or 0.0)) / gf_rev, 3)
    return {"available": True, "components": comps,
            "pension_opeb_to_genfund": ratio,
            "confidence": ("high" if found == 3 else "low" if found else "none"),
            "source": os.path.basename(audit_path)}


def _autofind_audit(district_name: str) -> str | None:
    """Look for a saved audit / continuing-disclosure PDF under the DD outputs that names
    this district (so book names with prior DD auto-attach their audit)."""
    if not os.path.isdir(DD):
        return None
    key = _norm(district_name).split()[0] if _norm(district_name) else ""
    pref = ("audit", "continuing_disclosure", "financial", "cd_full", "acfr")
    hits = []
    for cusip in os.listdir(DD):
        raw = os.path.join(DD, cusip, "raw")
        if not os.path.isdir(raw):
            continue
        ss = os.path.join(raw, "screens_and_sources.json")
        names = ""
        if os.path.exists(ss):
            try:
                names = json.dumps(json.load(open(ss)))
            except Exception:
                names = ""
        if key and key.lower() not in names.lower():
            continue
        for fn in os.listdir(raw):
            low = fn.lower()
            if low.endswith((".pdf", ".txt")) and any(p in low for p in pref):
                # rank: prefer audit > continuing_disclosure > cd_full > financial
                rank = next((i for i, p in enumerate(pref) if p in low), 9)
                hits.append((rank, os.path.join(raw, fn)))
    if not hits:
        return None
    hits.sort()
    return hits[0][1]


# ---------------- 4. top-level screen ----------------
def fiscal_health(district_name: str, county: str | None = None,
                  audit_path: str | None = None,
                  directory: list[dict] | None = None) -> dict:
    """Operating-fiscal-health screen for one CA school-district GO issuer.

    Returns enrollment_cagr_5y / enrollment_latest / enrollment_base, pension_opeb_to_genfund
    (+ components), and a fiscal_flags list (each flag dict carries severity hard|soft|info,
    a plain-language reason, and flag_frame stating these are marketability/tail not default).
    """
    res = {
        "district": district_name, "county": county, "asof": ASOF,
        "cds7": None, "doctype": None,
        "enrollment_series": {}, "enrollment_latest": None, "enrollment_base": None,
        "enrollment_cagr_5y": None, "enrollment_span_years": None,
        "enrollment_status": "UNVERIFIABLE",
        "pension_opeb_to_genfund": None, "pension_opeb_components": None,
        "pension_opeb_status": "UNVERIFIABLE",
        "fiscal_flags": [], "flag_frame": FLAG_FRAME,
    }
    flags = res["fiscal_flags"]

    r = resolve_cds(district_name, county, directory=directory)
    res["cds7"], res["doctype"] = r["cds7"], r["doctype"]
    res["resolution_confidence"] = r["confidence"]

    # --- community college: K-12 dimensions are NA, not clean ---
    if r.get("is_cc"):
        res["enrollment_status"] = "NA"
        res["pension_opeb_status"] = "UNVERIFIABLE" if not audit_path else res["pension_opeb_status"]
        flags.append({"severity": "info", "dimension": "scope",
                      "reason": "Community-college / higher-ed district: NOT covered by CDE "
                                "K-12 enrollment census or AB-1200 certification (CCCCO "
                                "monitors separately). Enrollment dimension NA; do not treat "
                                "absence of a flag as clean.",
                      "frame": FLAG_FRAME})
        # still attempt pension/OPEB if an audit was supplied
        if audit_path:
            _apply_pension(res, flags, parse_pension_opeb(audit_path))
        return res

    if not r["cds7"]:
        flags.append({"severity": "info", "dimension": "resolution",
                      "reason": f"Could not resolve '{district_name}' to a CDE district "
                                f"(confidence {r['confidence']}). Enrollment UNVERIFIABLE.",
                      "frame": FLAG_FRAME})
    else:
        # --- enrollment trend ---
        try:
            series = enrollment_series(r["cds7"])
        except Exception as e:  # network / source failure -> UNVERIFIABLE, never clean
            series = {}
            flags.append({"severity": "info", "dimension": "enrollment",
                          "reason": f"CDE enrollment fetch failed ({type(e).__name__}); "
                                    f"enrollment UNVERIFIABLE.", "frame": FLAG_FRAME})
        res["enrollment_series"] = series
        cagr, base, latest = _cagr(series)
        if cagr is not None:
            res["enrollment_status"] = "VERIFIED"
            res["enrollment_cagr_5y"] = round(cagr, 4)
            res["enrollment_latest"] = series.get(latest)
            res["enrollment_base"] = series.get(base)
            res["enrollment_span_years"] = int(latest[:4]) - int(base[:4])
            res["enrollment_window"] = f"{base} -> {latest}"
            if cagr <= ENROLL_CAGR_HARD:
                flags.append({"severity": "hard", "dimension": "enrollment",
                              "reason": f"Enrollment falling {cagr*100:.1f}%/yr "
                                        f"({series[base]:,} -> {series[latest]:,}, {res['enrollment_span_years']}y); "
                                        f"steep erosion of the per-ADA operating base.",
                              "frame": FLAG_FRAME})
            elif cagr <= ENROLL_CAGR_SOFT:
                flags.append({"severity": "soft", "dimension": "enrollment",
                              "reason": f"Enrollment declining {cagr*100:.1f}%/yr "
                                        f"({series[base]:,} -> {series[latest]:,}, {res['enrollment_span_years']}y); "
                                        f"sustained per-ADA operating-base erosion.",
                              "frame": FLAG_FRAME})
        elif series:
            res["enrollment_status"] = "PARTIAL"
            res["enrollment_latest"] = series[sorted(series)[-1]]

    # --- pension / OPEB burden ---
    ap = audit_path or _autofind_audit(district_name)
    if ap:
        res["pension_opeb_audit"] = os.path.basename(ap)
    _apply_pension(res, flags, parse_pension_opeb(ap) if ap else {"available": False})
    return res


def _apply_pension(res: dict, flags: list, pe: dict) -> None:
    if not pe.get("available"):
        res["pension_opeb_status"] = "UNVERIFIABLE"
        flags.append({"severity": "info", "dimension": "pension_opeb",
                      "reason": "No audited financials in hand -> pension/OPEB burden "
                                "UNVERIFIABLE (not assumed low).", "frame": FLAG_FRAME})
        return
    res["pension_opeb_components"] = pe.get("components")
    ratio = pe.get("pension_opeb_to_genfund")
    if ratio is None:
        res["pension_opeb_status"] = "UNVERIFIABLE"
        flags.append({"severity": "info", "dimension": "pension_opeb",
                      "reason": "Audit present but pension/OPEB or GF-revenue figure could "
                                "not be pinned from the text -> burden UNVERIFIABLE.",
                      "frame": FLAG_FRAME})
        return
    res["pension_opeb_to_genfund"] = ratio
    res["pension_opeb_status"] = "VERIFIED" if pe.get("confidence") == "high" else "ESTIMATE"
    if ratio >= PENSION_OPEB_HARD:
        flags.append({"severity": "hard", "dimension": "pension_opeb",
                      "reason": f"Net pension + OPEB liability {ratio:.2f}x general-fund "
                                f"revenue: heavy long-term-liability stack on the operating base.",
                      "frame": FLAG_FRAME})
    elif ratio >= PENSION_OPEB_SOFT:
        flags.append({"severity": "soft", "dimension": "pension_opeb",
                      "reason": f"Net pension + OPEB liability {ratio:.2f}x general-fund "
                                f"revenue: elevated long-term-liability burden.",
                      "frame": FLAG_FRAME})


# ======================= validation =======================
if __name__ == "__main__":
    DD_CASES = [
        ("Chico Unified", "Butte", None),
        ("Stockton Unified", "San Joaquin", None),
        ("Victor Valley Union High", "San Bernardino",
         os.path.join(DD, "926055KH6", "raw", "vvuhsd_audit_fy2025.pdf")),
        ("Victor Elementary", "San Bernardino",
         os.path.join(DD, "925836KH0", "raw", "cd_full.txt")),
        ("Palo Verde Community College", "Riverside", None),  # CC: enrollment/cert NA
    ]
    BOOK_CASES = [
        ("Palo Verde Unified", "Riverside", None),
        ("Oakland Unified", "Alameda", None),
    ]

    print(f"\nfiscal_health screen  (asof {ASOF})")
    print(FLAG_FRAME)
    print("=" * 132)
    hdr = (f"{'District':<28}{'CDS':<9}{'Enr base->latest':<22}{'CAGR/yr':>9}"
           f"  {'EnrStat':<10}{'P+OPEB/GF':>10} {'PenStat':<11} Flags")
    print(hdr)
    print("-" * 132)

    results = []
    for name, cty, ap in DD_CASES + BOOK_CASES:
        try:
            r = fiscal_health(name, cty, audit_path=ap)
        except Exception as e:
            print(f"{name:<28}ERROR {type(e).__name__}: {e}")
            continue
        results.append(r)
        cagr = (f"{r['enrollment_cagr_5y']*100:+.1f}%" if r['enrollment_cagr_5y'] is not None
                else "  --")
        enr_win = ""
        if r.get("enrollment_base") and r.get("enrollment_latest"):
            enr_win = f"{r['enrollment_base']:,}->{r['enrollment_latest']:,}"
        elif r.get("enrollment_latest"):
            enr_win = f"~{r['enrollment_latest']:,}"
        po = (f"{r['pension_opeb_to_genfund']:.2f}x" if r['pension_opeb_to_genfund'] is not None
              else "--")
        sev = [f["severity"] for f in r["fiscal_flags"]]
        nflag = (f"{sev.count('hard')}H/{sev.count('soft')}S"
                 + (f"/{sev.count('info')}i" if 'info' in sev else ""))
        print(f"{name:<28}{(r['cds7'] or '-'):<9}{enr_win:<22}{cagr:>9}"
              f"  {r['enrollment_status']:<10}{po:>10} {r['pension_opeb_status']:<11} {nflag}")

    # Per-flag detail
    print("\n" + "=" * 132)
    print("FLAG DETAIL (marketability/headline/tail on the GO — not default):")
    for r in results:
        if r["fiscal_flags"]:
            print(f"\n  {r['district']}  [{r.get('doctype') or '-'}]")
            for f in r["fiscal_flags"]:
                print(f"    [{f['severity'].upper():4}] {f['dimension']}: {f['reason']}")

    # Stockton operating-stress note
    print("\n" + "=" * 132)
    stk = next((r for r in results if r["district"] == "Stockton Unified"), None)
    if stk:
        print("STOCKTON UNIFIED operating-stress note:")
        print(f"  Enrollment {stk.get('enrollment_window','?')}: "
              f"{stk.get('enrollment_base'):,} -> {stk.get('enrollment_latest'):,} "
              f"({stk['enrollment_cagr_5y']*100:+.1f}%/yr).")
        print("  Multi-year per-ADA base erosion is the documented backdrop to the 2023 FCMAT "
              "fraud/governance finding and chronic deficit — a headline/marketability/tail "
              "channel. GO debt service remains on the separate county ad-valorem levy and is "
              "not impaired by the operating distress.")
    print()
