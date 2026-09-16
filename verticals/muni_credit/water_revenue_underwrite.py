"""water_revenue_underwrite — fit-for-purpose underwriting screen for ESSENTIAL-SERVICE
WATER / WASTEWATER REVENUE bonds.

WHY THIS IS SEPARATE FROM THE SCHOOL-GO LOGIC
---------------------------------------------
The scanner now qualifies water/wastewater REVENUE bonds (e.g. 27677SCN1 Eastern Muni WD,
49228YAX6 Kern County WA, 68442CBH8 Orange County WD). These are NOT tax-secured. There is
no ad-valorem levy and no SB-222 statutory lien behind them — running them through
school_go_issuer_credit (which credits a "first lien on an unlimited ad-valorem levy") is a
category error. A water-revenue bond is secured by NET SYSTEM REVENUES (gross operating
revenue minus O&M) and a RATE COVENANT (the issuer covenants to set rates that yield net
revenues equal to e.g. 1.10x-1.25x of debt service). The credit question is therefore:

  1. Does the system actually generate the covenanted coverage?        (DSCR)
  2. Can the issuer legally raise rates to maintain it?                 (Prop 218)
  3. Is the revenue base concentrated in one customer?                  (customer concentration)
  4. Will the physical water supply still exist?                        (supply risk — the tail)
  5. Is it water (supply-exposed) or wastewater (regulatory-exposed)?   (system type)

HONESTY-ALPHA POSTURE
---------------------
This is an UNDERWRITING screen, not a liar-detector — it grades the security on its own
disclosed financials. A system that honestly discloses thin (sub-1.10x) coverage is FLAGged
because the SECURITY is weak, not because the issuer lied. UNVERIFIABLE (OS un-fetchable or
un-parseable) is NEVER treated as clean — coverage is never assumed.

DATA PATH
---------
EMMA CUSIP -> issue_id -> Official Statement PDF (reuses emma_scraper). pdftotext extracts
text; a deterministic regex pass pulls the rate covenant + concentration + supply mentions,
and a claude-opus-4-8 fallback reads the multi-column coverage tables that pdftotext mangles
(the historical DSCR rows are nearly always laid out as untabbed numeric columns). Results
cache to data/water_revenue_cache.json keyed by CUSIP.

FIELD CONTRACT (returned by underwrite_water)
---------------------------------------------
  cusip                str
  issuer               str | None
  system_type          'water' | 'wastewater' | 'combined' | 'groundwater_mgmt' | None
  dscr                 float | None   most-recent historical debt-service coverage (x)
  dscr_basis           str | None     e.g. 'FY2016 all-in', senior vs all-in, source line
  rate_covenant        float | None   covenanted minimum coverage (x), e.g. 1.10
  prop218_note         str            rate-raising constraint / adopted multi-year schedule
  customer_top_share   float | None   top-customers as % of system revenue (e.g. 8.78)
  customer_basis       str | None     what the share measures (top-10 of sales, etc.)
  supply_risk          'none' | 'low' | 'moderate' | 'high' | 'unknown'
  supply_note          str
  verdict              'PASS' | 'REVIEW' | 'FLAG' | 'UNVERIFIABLE'
  flags                list[str]      individual triggered conditions
  os_source            str | None     OS PDF url
  asof                 str

THRESHOLDS (hard FLAG vs soft REVIEW)
-------------------------------------
  dscr < 1.10x                          -> FLAG  (hard: below typical covenant, thin net rev)
  1.10x <= dscr < 1.25x                 -> REVIEW (soft: covenant-tight margin of safety)
  supply_risk == 'high'                 -> FLAG  (hard: physical tail — Colorado River cut /
                                                  critically-overdrafted SGMA basin)
  supply_risk == 'moderate'             -> REVIEW
  customer_top_share >= 25%             -> FLAG  (hard: single-customer revenue dependency)
  15% <= customer_top_share < 25%       -> REVIEW
  dscr unknown AND covenant unknown     -> UNVERIFIABLE (never PASS on missing coverage)
A FLAG dominates REVIEW dominates PASS. UNVERIFIABLE only when coverage couldn't be read AT ALL.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import emma_scraper as E  # noqa: E402

HERE = Path(__file__).parent
DATA = HERE / "data"
OS_CACHE = DATA / "_water_os"
CACHE_PATH = DATA / "water_revenue_cache.json"
ASOF = "2026-06-19"

REVIEW_DSCR = 1.25     # soft: covenant-tight
FLAG_DSCR = 1.10       # hard: thin / below typical covenant
REVIEW_CONC = 15.0     # soft: top-customer share %
FLAG_CONC = 25.0       # hard: single-customer dependency

# --- model fallback (only used for the multi-column coverage table) ---
_MODEL = "claude-opus-4-8"


# ======================================================================================
# 1. CUSIP -> Official Statement text (reuse emma_scraper)
# ======================================================================================
def _resolve_issue_id(cusip: str, session) -> tuple[Optional[str], Optional[str]]:
    """Resolve a CUSIP to its EMMA issue_id (for the OS partial) + the security description.

    The /Security/Details/<cusip> page renders the issue's title and links the parent issue.
    EMMA assigns a stable issue_id; the OS PDF partial keys off that. We prefer the
    description-search issue_id (ES.../ER.../EP... form) because the hex issue ids that the
    Security page sometimes carries don't resolve through OfficialStatementPartialView.
    """
    url = E.BASE + "/Security/Details/" + cusip
    t = session.get(url, headers={"Referer": E.BASE + "/"}, timeout=40).text
    if "yesButton" in t:
        session.post(
            E.BASE + "/Disclaimer.aspx",
            data={"__VIEWSTATE": E._hidden("__VIEWSTATE", t),
                  "__VIEWSTATEGENERATOR": E._hidden("__VIEWSTATEGENERATOR", t),
                  "__EVENTVALIDATION": E._hidden("__EVENTVALIDATION", t),
                  "ctl00$mainContentArea$disclaimerContent$yesButton": "Accept"},
            headers={"Content-Type": "application/x-www-form-urlencoded",
                     "Origin": E.BASE, "Referer": url}, timeout=40)
        time.sleep(1)
        t = session.get(url, headers={"Referer": E.BASE + "/"}, timeout=40).text
    flat = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t))
    sec_m = re.search(r"CUSIP:\s*(.{0,160})", flat.upper())
    sec_desc = sec_m.group(1).strip() if sec_m else None
    ids = re.findall(r"/IssueView/Details/([A-Z0-9]+)", t)
    # prefer a letter-prefixed id (resolvable via the partial) over a bare hex one
    pref = [i for i in ids if re.match(r"^(E[PRS]|P|RE)\d", i)]
    issue_id = (pref or ids or [None])[0]
    return issue_id, sec_desc


def _pdftotext(pdf_path: Path, dest: Path, layout: bool) -> None:
    args = ["pdftotext"] + (["-layout"] if layout else []) + ["-nopgbrk",
            str(pdf_path), str(dest)]
    subprocess.run(args, check=False, capture_output=True)


def fetch_os_text(cusip: str, session=None) -> tuple[Optional[str], Optional[str],
                                                      Optional[str], Optional[str]]:
    """Return (flow_text, layout_text, os_pdf_url, security_desc) for a CUSIP.

    Two extractions of the same PDF:
      flow_text   (default)   — reflowed prose; best for the covenant / concentration / supply
                                regexes that read sentences.
      layout_text (-layout)   — column alignment preserved; required for the historical DSCR
                                table where row labels must stay attached to their numbers
                                (e.g. Kern's 0.79x without-transfer coverage).
    Returns (None, None, None, desc) if the OS can't be fetched. Caches under data/_water_os/.
    """
    OS_CACHE.mkdir(parents=True, exist_ok=True)
    flow_path = OS_CACHE / f"{cusip}.txt"
    layout_path = OS_CACHE / f"{cusip}.layout.txt"
    url_path = OS_CACHE / f"{cusip}.osurl"
    if flow_path.exists() and flow_path.stat().st_size > 1000:
        url = url_path.read_text().strip() if url_path.exists() else None
        lay = layout_path.read_text(errors="replace") if layout_path.exists() else None
        return flow_path.read_text(errors="replace"), lay, url, None

    s = session or E._session()
    issue_id, sec_desc = _resolve_issue_id(cusip, s)
    if not issue_id:
        return None, None, None, sec_desc
    E.accept_disclaimer(s, issue_id)
    os_pdf = E.get_official_statement(issue_id, s)
    if not os_pdf:
        return None, None, None, sec_desc
    pdf_path = OS_CACHE / f"{cusip}.pdf"
    E.download_pdf(os_pdf, pdf_path, s)
    _pdftotext(pdf_path, flow_path, layout=False)
    _pdftotext(pdf_path, layout_path, layout=True)
    url_path.write_text(os_pdf)
    flow = flow_path.read_text(errors="replace") if flow_path.exists() else None
    lay = layout_path.read_text(errors="replace") if layout_path.exists() else None
    return flow, lay, os_pdf, sec_desc


# ======================================================================================
# 2. Deterministic regex parse (covenant, system type, concentration, supply mentions)
# ======================================================================================
def parse_rate_covenant(text: str) -> tuple[Optional[float], Optional[str]]:
    """Extract the covenanted minimum coverage (x). Rate covenants state net revenues must
    equal at least N% of debt service. We take the LOWEST stated coverage % near the word
    'covenant' (the binding floor; some OSs state a 115% rate-setting target above a 110%
    master-resolution floor — the floor is the default-trigger covenant)."""
    pcts = []
    for m in re.finditer(r"(?:Net\s+(?:\w+\s+){0,3}Revenues?|coverage|covenant)"
                         r"[^.]{0,160}?(\d{3})\s*%|"
                         r"(\d{3})\s*%[^.]{0,40}?(?:of\s+(?:the\s+)?Debt\s+Service|debt service)",
                         text, re.I):
        raw = m.group(1) or m.group(2)
        if raw:
            v = int(raw) / 100.0
            if 1.0 <= v <= 3.0:
                pcts.append(v)
    # also "one hundred ten per cent (110%)" / "one hundred twenty-five percent (125%)"
    for m in re.finditer(r"\((\d{3})\s*%\)\s*of\s+(?:the\s+)?Debt\s+Service", text, re.I):
        v = int(m.group(1)) / 100.0
        if 1.0 <= v <= 3.0:
            pcts.append(v)
    if not pcts:
        return None, None
    floor = min(pcts)
    note = f"covenanted floor {floor:.2f}x"
    if max(pcts) != floor:
        note += f" (rate-setting target up to {max(pcts):.2f}x)"
    return floor, note


def classify_system_type(text: str, sec_desc: Optional[str]) -> tuple[Optional[str], str]:
    """water / wastewater / combined / groundwater_mgmt from the OS + security description."""
    blob = ((sec_desc or "") + " " + text[:6000]).lower()
    has_water = "water" in blob
    has_sewer = ("wastewater" in blob or "sewer" in blob)
    # a groundwater-management agency (e.g. OCWD) levies replenishment assessments, not retail
    # water sales — physically different security; flag it distinctly.
    gw_mgmt = bool(re.search(r"replenishment assessment|groundwater (?:basin|replenishment) "
                             r"(?:management|system)|manage the .{0,40}groundwater basin", text, re.I))
    if gw_mgmt and "replenishment assessment" in text.lower():
        return "groundwater_mgmt", ("groundwater-management agency: revenue = replenishment "
                                    "assessments on pumpers, not retail water sales")
    if has_water and has_sewer:
        return "combined", "combined water + wastewater system (water supply risk applies)"
    if has_sewer and not has_water:
        return "wastewater", "wastewater system: no supply risk; NPDES/regulatory risk instead"
    if has_water:
        return "water", "water system"
    return None, "system type not determined from OS"


def parse_customer_concentration(text: str) -> tuple[Optional[float], Optional[str]]:
    """Top-customer share of system revenue/consumption. OSs report this as a PROSE SENTENCE,
    e.g. 'the ten largest customers accounted for approximately X% of total water sales
    revenues'. We require the X% to be tied to an 'accounted for / represented / X% of ...
    (revenues|consumption|sales|production)' phrase — a bare '%' in a table HEADER (e.g. a
    column captioned 'Acre Feet Produced ... %') is NOT a verified concentration figure and
    must be rejected (UNVERIFIABLE != a fabricated number)."""
    pats = [
        # "ten largest [potable water] customers ... accounted for ~X% of ... revenues/consumption"
        r"(?:ten\s+largest|top\s+ten|10\s+largest)\s+(?:\w+\s+){0,3}"
        r"(?:customers|users|ratepayers|producers)[^.]{0,80}?(?:accounted\s+for|"
        r"represent(?:ed)?|comprised|were|account\s+for)[^.]{0,40}?(\d{1,2}(?:\.\d+)?)\s*%"
        r"[^.]{0,40}?(?:revenues?|sales|consumption|production)",
        r"(\d{1,2}(?:\.\d+)?)\s*%\s*of\s+(?:total\s+)?(?:water\s+)?(?:sales\s+)?"
        r"(?:revenues?|consumption|water\s+production)[^.]{0,80}?(?:ten\s+largest|largest|top\s+ten)",
        r"largest\s+(?:single\s+)?(?:customer|ratepayer)[^.]{0,120}?(?:accounted\s+for|"
        r"represent(?:ed)?)[^.]{0,30}?(\d{1,2}(?:\.\d+)?)\s*%",
    ]
    for p in pats:
        m = re.search(p, text, re.I)
        if m:
            v = float(m.group(1))
            if 0 < v <= 100:
                ctx = re.sub(r"\s+", " ", m.group(0))[:150]
                return v, ctx
    return None, None


# ======================================================================================
# 3. Supply-risk overlay (Colorado River + critically-overdrafted SGMA basins)
# ======================================================================================
# Lower Colorado River Basin shortage: post-2026 interim-guidelines cuts hit the SE-CA
# Colorado-River-Aqueduct / MWD-imported-water and direct-priority-right service areas.
# Imperial Irrigation District holds the senior Priority-3 right (least cut); MWD's Colorado
# River Aqueduct supply is junior and the marginal supply that gets cut first.
_COLORADO_RIVER_HIGH = re.compile(
    r"Colorado River Aqueduct|Imperial Irrigation|Coachella Valley Water|"
    r"sole source of .{0,40}imported water is MWD|"
    r"Metropolitan Water District", re.I)
_COLORADO_RIVER_DIRECT = re.compile(r"Colorado River", re.I)

# Critically-overdrafted SGMA basins (DWR 2019 priority list, the 21 critically-overdrafted
# basins that face the harshest 2020/2022 GSP pumping-reduction glide paths). A water system
# whose supply is groundwater from one of these basins faces a mandated supply cut.
_SGMA_CRITICAL_BASINS = [
    "kern county", "tulare lake", "tule", "kaweah", "kings", "westside",
    "pleasant valley", "san joaquin river", "chowchilla", "madera", "merced",
    "delta-mendota", "cuyama", "paso robles", "oxnard", "pajaro valley",
    "eastern san joaquin", "borrego",
]
_SGMA_CONTEXT = re.compile(
    r"critically[- ]overdraft|sustainable groundwater management act|\bSGMA\b|"
    r"groundwater sustainability (?:plan|agency)|overdraft", re.I)


def assess_supply_risk(text: str, system_type: Optional[str],
                       sec_desc: Optional[str], issuer: Optional[str] = None,
                       county: Optional[str] = None) -> tuple[str, str]:
    """Return (level, note). Wastewater has no supply risk. Build a lightweight basin/source flag.

    GEOGRAPHIC ANCHOR (the fix): the keyword scan alone keys off whether 'Colorado River' / an SGMA
    basin name *appears* in the OS — but a large system's OS routinely mentions those in statewide-
    context / risk-factor boilerplate, which false-flagged local-surface systems (EBMUD = Mokelumne
    snowmelt) as 'Colorado River high'. So we first resolve the system's ACTUAL supply region from the
    issuer/county (utility_supply.supply_bucket). When that region is a local-surface source
    (NorCal-Delta / Sierra-local / coastal), a Colorado/SGMA keyword hit is treated as statewide context
    and CANNOT escalate to high — it only fires high where the geography makes import/groundwater the
    real supply (Colorado-River / SWP / groundwater / unknown)."""
    if system_type == "wastewater":
        return "none", "wastewater system — no water-supply tail (NPDES/regulatory instead)"

    # FIRST-PRINCIPLES (R/f/M): verify the supply against PUBLISHED registries (DWR SWP contractors / MWD
    # members / USBR Colorado-River contractors / DWR Bulletin 118 critical basins) BEFORE any OS-keyword
    # heuristic. A registry-VERIFIED determination wins outright; otherwise the heuristic stands but inherits
    # the connector's UWMP escalation (authority-unverified != clean). See detectors/water_supply_authority.
    _auth = None
    try:
        from detectors import water_supply_authority as _WSA
        _auth = _WSA.verify_supply(issuer, county, district=issuer, system_type=system_type)
    except Exception:
        _auth = None
    if _auth and _auth.get("confidence") == "VERIFIED":
        src = ", ".join(sorted({a.split("—")[0].split("(")[0].strip() for a in _auth.get("authorities", [])}))
        return _auth["risk_level"], f"[verified vs {src[:70]}] {_auth['note']}"

    try:
        import utility_supply as _US
        geo = _US.supply_bucket(issuer=issuer, county=county, system_type=system_type)
    except Exception:
        geo = "UNKNOWN"
    local_surface = geo in ("NORCAL_DELTA", "SIERRA_LOCAL", "COASTAL_LOCAL")
    groundwater = (system_type or "") in ("groundwater", "groundwater_mgmt") or geo == "GROUNDWATER"
    src = geo.replace("_", " ").title()

    notes = []
    level = "low"
    blob = text

    # (a) Colorado River dependency — gated by geography (a local-surface system can't be "Colorado high")
    if _COLORADO_RIVER_HIGH.search(blob):
        if local_surface:
            notes.append(f"OS references MWD/Colorado-River water, but this system's supply is {src} "
                         f"(local surface water) — statewide context, not its own dependency")
        else:
            level = "high"
            notes.append("imported-water supply via MWD / Colorado River Aqueduct — exposed to "
                         "Lower Basin shortage & post-2026 interim-guidelines cuts")
    elif _COLORADO_RIVER_DIRECT.search(blob) and not local_surface:
        level = max(level, "moderate", key=_risk_rank)
        notes.append("references Colorado River supply — partial shortage exposure")

    # (b) SGMA critically-overdrafted groundwater basin — only escalates where supply is actually
    # groundwater (or geography unknown); a surface-water system's OS basin mention is context.
    # scan the FULL OS for the basin name (not the first 40k) — the geographic gate above now prevents the
    # false-positive this truncation used to guard against (Corcoran's Tulare-Lake mention sat past 40k).
    blob_l = (blob + " " + (sec_desc or "")).lower()
    matched_basin = next((b for b in _SGMA_CRITICAL_BASINS if b in blob_l), None)
    if matched_basin and _SGMA_CONTEXT.search(blob) and (groundwater or not local_surface):
        level = "high"
        notes.append(f"groundwater supply in/near a critically-overdrafted SGMA basin "
                     f"('{matched_basin}') — mandated pumping reductions under GSP glide path")
    elif _SGMA_CONTEXT.search(blob) and not local_surface:
        level = max(level, "moderate", key=_risk_rank)
        notes.append("SGMA / overdraft language present — groundwater supply subject to "
                     "sustainability constraints")
    elif matched_basin and local_surface:
        notes.append(f"OS mentions SGMA/'{matched_basin}' in statewide context; this system's supply is "
                     f"{src} surface water — not groundwater-overdraft-dependent")

    # (c) groundwater-management agencies (OCWD): their whole purpose is basin replenishment.
    if system_type == "groundwater_mgmt" and level == "low":
        level = "moderate"
        notes.append("groundwater-management agency — replenishment supply depends on imported "
                     "water availability")

    if not notes:
        notes.append(f"no Colorado-River or critically-overdrafted-basin dependency detected"
                     + (f" (supply region: {src})" if geo != "UNKNOWN" else " in OS"))
    # the registries couldn't positively place this system — say so (UNVERIFIABLE != clean), point to the
    # per-agency authority (UWMP), and don't let the OS-keyword heuristic assert an unverified HIGH.
    if _auth and _auth.get("escalate_to_uwmp"):
        if level == "high":
            level = "moderate"
            notes.append("OS keywords suggest higher supply risk but NO published registry confirms it — "
                         "capped pending the agency's DWR UWMP (authority-unverified)")
        else:
            notes.append("supply not registry-verified — confirm portfolio via the agency's DWR UWMP")
    return level, "; ".join(notes)


_RISK_ORDER = {"none": 0, "low": 1, "moderate": 2, "high": 3, "unknown": 1}
def _risk_rank(level: str) -> int:
    return _RISK_ORDER.get(level, 1)


# ======================================================================================
# 4. DSCR — regex first, LLM fallback for the mangled multi-column coverage table
# ======================================================================================
def _extract_json(txt: str) -> Optional[dict]:
    """Parse a JSON object out of an LLM reply, tolerating code fences / leading prose."""
    txt = re.sub(r"^```(?:json)?\s*|\s*```$", "", txt.strip(), flags=re.I | re.M)
    try:
        return json.loads(txt)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", txt, re.S)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                return None
    return None


def parse_dscr_regex(text: str) -> tuple[Optional[float], Optional[str]]:
    """Try to pull the most-recent historical coverage from inline 'N.Nx' near a coverage
    heading. Multi-column pdftotext tables usually defeat this — returns None and the caller
    escalates to the model."""
    out = []
    for m in re.finditer(r"(?:debt service coverage|coverage ratio|all-in (?:debt service )?"
                         r"coverage)[^\n]{0,400}", text, re.I):
        for mm in re.finditer(r"(\d\.\d{1,2})\s*x", m.group(0)):
            v = float(mm.group(1))
            if 0.3 <= v <= 10.0:
                out.append(v)
    if out:
        # most-recent column is conventionally the LAST printed value in a left-to-right
        # historical run; take the smallest of the trailing pair as a conservative read
        return out[-1], "regex: inline coverage ratio near coverage heading"
    return None, None


_RATIO_TOKEN = re.compile(r"\b\d\.\d{1,2}\s*x\b")          # "1.85x" / "2.1 x"
# bare coverage numbers (OCWD prints "Senior Debt Service Coverage 3.86 3.70 5.15 ..." with no x)
_BARE_RATIO = re.compile(r"\b(?:1[0-5]|[0-9])\.\d{1,2}\b")
_COVERAGE_LABEL = re.compile(
    r"(?:Senior |Junior |Parity |All[- ]?In )?(?:Debt Service )?Coverage(?: Ratio)?"
    r"(?: Without| After Transfer)?|"
    r"Historic(?:al)? (?:and Projected )?Operating Results", re.I)
# a coverage ROW (label immediately followed on the same line by numeric columns) — strongest
_COVERAGE_ROW = re.compile(
    r"(?:Senior|Junior|Parity|All[- ]?In|Total)?\s*(?:Debt Service )?Coverage(?: Ratio)?"
    r"[^\n]{0,60}?((?:\s+\d{1,2}\.\d{1,2}\s*x?){2,})", re.I)


def _anchor_coverage_table(src: str) -> int:
    """Return the char offset of the coverage occurrence whose neighborhood carries the most
    numeric ratio values — i.e. the actual historical table, not a table-of-contents caption.

    Scores each coverage-label occurrence by how many ratio tokens (with or without an 'x'
    suffix) sit within ±2.5k chars. A direct coverage-ROW match (label + inline numeric
    columns on one line, e.g. OCWD's 'Senior Debt Service Coverage 3.86 3.70 ...') wins
    outright. -1 if no coverage label is present at all."""
    row = _COVERAGE_ROW.search(src)
    if row:
        return row.start()
    best_i, best_n = -1, 0
    for m in _COVERAGE_LABEL.finditer(src):
        i = m.start()
        nbhd = src[max(0, i - 2500): i + 2500]
        n = len(_RATIO_TOKEN.findall(nbhd)) + len(_BARE_RATIO.findall(nbhd))
        if n > best_n:
            best_n, best_i = n, i
    if best_i != -1 and best_n >= 3:
        return best_i
    m = _COVERAGE_LABEL.search(src)
    return m.start() if m else -1


def parse_dscr_llm(text: str, issuer_hint: str = "", layout_text: str = "") -> tuple[Optional[float], Optional[str]]:
    """Read the historical debt-service-coverage table with claude-opus-4-8. The historical
    DSCR rows are laid out as untabbed numeric columns that defeat regex; the model reads the
    column layout. Returns the MOST-RECENT fiscal year's coverage. Degrades to (None, reason)
    on any failure — never fabricates a number."""
    key_path = Path(os.path.expanduser("~/.anthropic_api_key"))
    if not key_path.exists():
        return None, "no API key — DSCR table not parsed"
    try:
        import anthropic
    except ImportError:
        return None, "anthropic SDK unavailable"

    # Read from the LAYOUT extraction (column alignment preserved) — the historical DSCR rows
    # only stay attached to their numbers in -layout mode. Fall back to flow text if absent.
    src = layout_text or text
    # Anchor on a coverage-RATIO label whose neighborhood actually contains numeric ratio
    # values (N.NNx). Most "Debt Service Coverage" hits are table-of-contents / section
    # captions with no numbers; the real historical table is the one surrounded by ratios. In
    # -layout tables the values can sit a few lines ABOVE their wrapped row label.
    idx = _anchor_coverage_table(src)
    # Window generously on BOTH sides: in wrapped -layout tables the value row can precede its
    # label by several lines (Kern's 0.79x organic row sits ~5k chars above the 'Without
    # Transfer' label the anchor lands on), and the multi-year columns extend after it.
    window = src[max(0, idx - 7000): idx + 9000] if idx != -1 else src[:16000]

    client = anthropic.Anthropic(api_key=key_path.read_text().strip())
    prompt = (
        "You are reading the historical debt-service-coverage section of a municipal water "
        "revenue bond Official Statement. The table is laid out as numeric columns (one per "
        "fiscal year) that may have lost their alignment in text extraction.\n\n"
        f"Issuer: {issuer_hint}\n\n"
        "Find the HISTORICAL (actual, not projected) debt-service coverage ratio for the "
        "MOST RECENT fiscal year shown. Rules for which number to report in most_recent_dscr:\n"
        "  - If both senior-lien and all-in coverage are given, use the ALL-IN (total).\n"
        "  - IMPORTANT: if the table shows coverage BOTH 'without transfer from/to a Rate "
        "Stabilization Fund' AND 'after transfer', report the WITHOUT-TRANSFER (organic) "
        "coverage — that is the system's true net-revenue coverage; the after-transfer figure "
        "is engineered to meet the covenant. Set rsf_engineered=true in that case and put the "
        "after-transfer figure in basis.\n"
        "Report most_recent_dscr as a number of times (x), e.g. 0.79. If you cannot find a "
        "historical coverage ratio, set found=false and most_recent_dscr=null. Never guess.\n\n"
        "Reply with ONLY a JSON object, no prose, no code fence, of exactly this shape:\n"
        '{"most_recent_dscr": <number or null>, "fiscal_year": <string or null>, '
        '"basis": <string: senior/all-in + RSF note>, "rsf_engineered": <true|false>, '
        '"found": <true|false>}\n\n'
        "=== OS COVERAGE SECTION ===\n" + window
    )
    try:
        resp = client.messages.create(
            model=_MODEL,
            max_tokens=1500,
            thinking={"type": "adaptive"},
            messages=[{"role": "user", "content": prompt}],
        )
        txt = next(b.text for b in resp.content if b.type == "text")
        d = _extract_json(txt)
        if d is None:
            return None, "model response not parseable as JSON"
        if d.get("found") and isinstance(d.get("most_recent_dscr"), (int, float)):
            v = float(d["most_recent_dscr"])
            basis = f"{d.get('fiscal_year') or '?'} {d.get('basis') or ''}".strip()
            tag = " [RSF-ENGINEERED: organic coverage; after-transfer meets covenant]" \
                if d.get("rsf_engineered") else ""
            return v, f"OS coverage table (model-read): {basis}{tag}"
        return None, "model read OS coverage section but found no historical DSCR"
    except Exception as ex:  # noqa: BLE001
        return None, f"DSCR model-read failed: {type(ex).__name__}"


# ======================================================================================
# 5. Verdict
# ======================================================================================
def _verdict(dscr, rate_covenant, supply_risk, conc, supply_note=None) -> tuple[str, list[str]]:
    flags = []
    sev = "PASS"

    def bump(level):
        nonlocal sev
        order = {"PASS": 0, "REVIEW": 1, "FLAG": 2, "UNVERIFIABLE": 3}
        if order[level] > order[sev]:
            sev = level

    # coverage
    if dscr is None and rate_covenant is None:
        bump("UNVERIFIABLE")
        flags.append("coverage UNVERIFIABLE: neither historical DSCR nor rate covenant read "
                     "from OS — NOT assumed clean")
    else:
        if dscr is not None:
            if dscr < FLAG_DSCR:
                bump("FLAG"); flags.append(f"DSCR {dscr:.2f}x < {FLAG_DSCR:.2f}x (thin net revenue)")
            elif dscr < REVIEW_DSCR:
                bump("REVIEW"); flags.append(f"DSCR {dscr:.2f}x in covenant-tight band "
                                             f"[{FLAG_DSCR:.2f}-{REVIEW_DSCR:.2f}x)")
        else:
            # covenant known but no historical DSCR — soft caution, not clean
            bump("REVIEW")
            flags.append(f"rate covenant {rate_covenant:.2f}x present but historical DSCR not "
                         f"read — coverage performance UNVERIFIED")

    # supply tail — use the actual (geographically-anchored) supply note, not a hardcoded label
    if supply_risk == "high":
        bump("FLAG"); flags.append("supply_risk HIGH — " + (supply_note or
             "Colorado River / critically-overdrafted SGMA basin").split(";")[0][:90])
    elif supply_risk == "moderate":
        bump("REVIEW"); flags.append("supply_risk MODERATE — " +
             ((supply_note or "imported/groundwater constraint").split(";")[0][:90]))

    # customer concentration
    if conc is not None:
        if conc >= FLAG_CONC:
            bump("FLAG"); flags.append(f"customer_top_share {conc:.1f}% >= {FLAG_CONC:.0f}% "
                                       f"(single-customer revenue dependency)")
        elif conc >= REVIEW_CONC:
            bump("REVIEW"); flags.append(f"customer_top_share {conc:.1f}% in "
                                         f"[{REVIEW_CONC:.0f}-{FLAG_CONC:.0f}%)")

    if not flags:
        flags.append("adequate disclosed coverage, diffuse customer base, no acute supply tail")
    return sev, flags


# ======================================================================================
# 6. Public entry point
# ======================================================================================
def _load_cache() -> dict:
    if CACHE_PATH.exists():
        try:
            return json.loads(CACHE_PATH.read_text())
        except json.JSONDecodeError:
            return {}
    return {}


def _save_cache(cache: dict) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(cache, indent=1, default=str))


def underwrite_water(cusip: str, os_pdf_path_or_text: Optional[str] = None,
                     session=None, use_cache: bool = True, with_current: bool = False) -> dict:
    """Underwrite one essential-service water/wastewater REVENUE bond.

    Args:
        cusip: 9-char CUSIP.
        os_pdf_path_or_text: optional override — a path to an OS .pdf/.txt or the OS text
            itself. If omitted, the OS is fetched from EMMA by CUSIP.
        session: optional requests.Session (reuse across CUSIPs to amortize EMMA cookies).
        use_cache: read/write data/water_revenue_cache.json keyed by CUSIP.
        with_current: also pull the CURRENT debt-service coverage from the issuer's continuing-disclosure
            annual report (cdd_financials). The OS DSCR is issuance-vintage; the CDD carries the latest
            reported coverage. When the OS DSCR is unreadable, the current CDD coverage fills the gap so
            the verdict isn't a bare UNVERIFIABLE. Per-name DD path only (not the nightly universe drain).

    Returns a dict matching the FIELD CONTRACT in the module docstring. Degrades to
    verdict='UNVERIFIABLE' (never PASS) when the OS can't be fetched or coverage can't be read.
    """
    cache = _load_cache() if use_cache else {}
    if use_cache and cusip in cache and not with_current:
        return cache[cusip]

    # text  = reflowed prose (covenant/concentration/supply regexes)
    # layout = column-aligned (historical DSCR table)
    text, layout_text, os_url, sec_desc = None, None, None, None
    # explicit override
    if os_pdf_path_or_text:
        p = Path(os_pdf_path_or_text)
        if p.exists() and p.suffix.lower() == ".pdf":
            OS_CACHE.mkdir(parents=True, exist_ok=True)
            flow_p = OS_CACHE / f"{cusip}.txt"
            lay_p = OS_CACHE / f"{cusip}.layout.txt"
            _pdftotext(p, flow_p, layout=False)
            _pdftotext(p, lay_p, layout=True)
            text = flow_p.read_text(errors="replace") if flow_p.exists() else None
            layout_text = lay_p.read_text(errors="replace") if lay_p.exists() else None
        elif p.exists():
            text = p.read_text(errors="replace")
            layout_text = text
        else:
            text = os_pdf_path_or_text  # treat as raw OS text
            layout_text = text
    else:
        text, layout_text, os_url, sec_desc = fetch_os_text(cusip, session)

    rec = {"cusip": cusip, "issuer": None, "system_type": None, "dscr": None,
           "dscr_basis": None, "rate_covenant": None, "prop218_note": "",
           "customer_top_share": None, "customer_basis": None, "supply_risk": "unknown",
           "supply_note": "", "verdict": "UNVERIFIABLE", "flags": [],
           "os_source": os_url, "asof": ASOF}

    if not text or len(text) < 1000:
        rec["flags"] = ["OS could not be fetched/parsed from EMMA — coverage NOT assumed; "
                        "UNVERIFIABLE != clean"]
        rec["supply_note"] = "OS unavailable"
        if use_cache:
            cache[cusip] = rec
            _save_cache(cache)
        return rec

    # issuer / security description
    if not sec_desc:
        m = re.search(r"^\s*\$[\d,]+\s*\n+\s*(.{5,80})", text)
        sec_desc = m.group(1).strip() if m else None
    rec["issuer"] = _guess_issuer(text, sec_desc) or _issuer_from_stores(cusip)

    # system type
    rec["system_type"], st_note = classify_system_type(text, sec_desc)

    # rate covenant
    rec["rate_covenant"], cov_note = parse_rate_covenant(text)

    # DSCR: read the historical coverage table from the LAYOUT text via the model (the rows
    # only stay attached to their numbers in -layout mode). The flow-text inline regex
    # over-fires on stray "N.Nx" tokens, so it is used only as a last resort when there is no
    # layout text at all.
    dscr, basis = parse_dscr_llm(text, issuer_hint=rec["issuer"] or sec_desc or cusip,
                                 layout_text=layout_text or "")
    if dscr is None and not layout_text:
        dscr, basis = parse_dscr_regex(text)
    rec["dscr"], rec["dscr_basis"] = dscr, basis

    # Prop 218 note
    rec["prop218_note"] = _prop218_note(text, rec["system_type"])

    # customer concentration
    conc, conc_basis = parse_customer_concentration(text)
    rec["customer_top_share"], rec["customer_basis"] = conc, conc_basis

    # supply risk
    rec["supply_risk"], rec["supply_note"] = assess_supply_risk(
        text, rec["system_type"], sec_desc, issuer=rec.get("issuer"))
    if st_note and rec["supply_note"]:
        rec["supply_note"] = f"[{rec['system_type']}] " + rec["supply_note"]

    # CURRENT coverage from the continuing-disclosure annual report (OS DSCR is issuance-vintage).
    if with_current:
        cur = _current_dscr_from_cd(cusip)
        if cur.get("current_dscr") is not None:
            rec.update(cur)
            if dscr is None:        # OS coverage unreadable -> fill the gap with the current figure
                dscr, rec["dscr"] = cur["current_dscr"], cur["current_dscr"]
                rec["dscr_basis"] = f"CDD annual (current, {cur.get('current_dscr_basis')})"

    # verdict
    rec["verdict"], rec["flags"] = _verdict(dscr, rec["rate_covenant"], rec["supply_risk"], conc,
                                            supply_note=rec.get("supply_note"))
    if rec.get("current_dscr_unaudited") and rec.get("current_dscr") is not None \
            and rec["current_dscr"] < 1.0:
        rec["flags"] = list(rec["flags"]) + [
            f"current CDD coverage {rec['current_dscr']:.2f}x is UNAUDITED / one-time-driven"
            + (f": {rec['current_dscr_note']}" if rec.get("current_dscr_note") else "")
            + " — surface, don't treat as structural"]

    if use_cache:
        cache[cusip] = rec
        _save_cache(cache)
    return rec


def _current_dscr_from_cd(cusip: str) -> dict:
    """CURRENT debt-service coverage from the issuer's latest CDD annual report (shared cdd_financials —
    the same parser refresh_current_state uses). Prefers an already-downloaded annual PDF; else fetches
    serial/throttled. Returns {} on miss (never assumes coverage)."""
    try:
        import cdd_financials as CF
        from pathlib import Path
    except Exception:
        return {}
    pdf = Path(__file__).resolve().parent / "outputs" / "diligence_reports" / cusip / "raw" / "cdd_annual_latest.pdf"
    try:
        st = CF.current_state(cusip, ann_text=CF._text(pdf)) if pdf.exists() else CF.current_state(cusip)
    except Exception:
        return {}
    if st.get("dscr_current") is None:
        return {}
    return {"current_dscr": st["dscr_current"], "current_dscr_basis": st.get("dscr_basis"),
            "current_dscr_series": st.get("dscr_series"), "current_dscr_unaudited": st.get("dscr_unaudited"),
            "current_dscr_note": st.get("dscr_note")}


def _issuer_from_stores(cusip: str) -> Optional[str]:
    """Fallback issuer name from the want-list / master when OS extraction fails — needed so the supply
    authority can resolve the agency (a missing issuer silently degrades verification to UNVERIFIED)."""
    import os as _os, json as _json
    here = _os.path.dirname(_os.path.abspath(__file__))
    for rel in ("outputs/SCANNER_STANDING_WANTLIST.json", "outputs/DILIGENCE_MASTER.json"):
        try:
            for r in _json.load(open(_os.path.join(here, rel))):
                if r.get("cusip") == cusip and (r.get("issuer") or r.get("district")):
                    return r.get("issuer") or r.get("district")
        except Exception:
            pass
    return None


def _guess_issuer(text: str, sec_desc: Optional[str]) -> Optional[str]:
    """Best-effort issuer name from the OS cover / security description."""
    if sec_desc:
        nm = re.split(r"\b(?:CALIF|WATER &|WTR &|REV|REVENUE|REFUNDING|SERIES|\d{4})",
                      sec_desc, 1)[0].strip()
        if len(nm) > 5:
            return nm.title()
    for pat in [r"(Kern County Water Agency)", r"(Orange County Water District)",
                r"(Eastern Municipal Water District)",
                r"([A-Z][\w.]+(?:\s+[A-Z][\w.]+){1,5}\s+(?:Water|Municipal|Utility)\s+"
                r"(?:District|Agency|Authority))"]:
        m = re.search(pat, text[:8000])
        if m:
            return m.group(1)
    return None


def _prop218_note(text: str, system_type: Optional[str]) -> str:
    """California Prop 218 governs water/sewer rate increases (majority-protest). Note whether
    the issuer has an ADOPTED MULTI-YEAR rate schedule (mitigant) vs needs new rate action."""
    t = text
    has_218 = bool(re.search(r"Proposition\s*218|Article\s*XIII\s*D|majority protest", t, re.I))
    adopted = re.search(
        r"(adopted|approved)[^.]{0,80}?(multi[- ]year|five[- ]year|\d[- ]year)[^.]{0,40}?"
        r"(rate (?:increase|schedule|adjustment)s?)|"
        r"(rate (?:increase|adjustment)s?)[^.]{0,60}?(through|until)\s+(?:Fiscal Year\s+)?20\d\d",
        t, re.I)
    pending = re.search(r"(?:will|must|intends to|plans to|expects to)\s+(?:seek|adopt|"
                        r"implement|consider)[^.]{0,60}?rate (?:increase|adjustment)", t, re.I)
    parts = []
    if has_218:
        parts.append("CA Prop 218 majority-protest process governs rate increases")
    if adopted:
        parts.append("MITIGANT: adopted multi-year rate schedule in place")
    elif pending:
        parts.append("CAUTION: future rate action needed (not yet adopted)")
    if system_type == "groundwater_mgmt":
        parts.append("note: replenishment assessments set under district's own Act, not retail "
                     "Prop 218 process (Prop 26 may apply)")
    return "; ".join(parts) if parts else "Prop 218 rate-raising constraint not characterized in OS"


# ======================================================================================
# __main__ — validate on the three water CUSIPs surfaced this week
# ======================================================================================
if __name__ == "__main__":
    cusips = sys.argv[1:] or ["27677SCN1", "49228YAX6", "68442CBH8"]
    sess = E._session()
    rows = []
    for cu in cusips:
        print(f"... underwriting {cu}", file=sys.stderr, flush=True)
        rows.append(underwrite_water(cu, session=sess, use_cache=True))
        time.sleep(1.0)

    def fmt(v, suf="", n=2):
        if v is None:
            return "—"
        if isinstance(v, float):
            return f"{v:.{n}f}{suf}"
        return str(v)

    print(f"\n{'cusip':10} {'system_type':16} {'dscr':>7} {'cov':>6} {'top%':>6} "
          f"{'supply':9} {'verdict':12} issuer")
    print("-" * 110)
    for r in rows:
        print(f"{r['cusip']:10} {(r['system_type'] or '—'):16} "
              f"{fmt(r['dscr'], 'x'):>7} {fmt(r['rate_covenant'], 'x'):>6} "
              f"{fmt(r['customer_top_share'], '%', 1):>6} {r['supply_risk']:9} "
              f"{r['verdict']:12} {(r['issuer'] or '—')[:34]}")
    print()
    for r in rows:
        print(f"== {r['cusip']} ({r['issuer'] or '—'}) :: {r['verdict']} ==")
        print(f"   DSCR basis : {r['dscr_basis'] or '—'}")
        print(f"   covenant   : {r['rate_covenant']}  | {r['prop218_note']}")
        print(f"   concentr.  : {r['customer_basis'] or '—'}")
        print(f"   supply     : {r['supply_note']}")
        for f in r["flags"]:
            print(f"     - {f}")
        print()
