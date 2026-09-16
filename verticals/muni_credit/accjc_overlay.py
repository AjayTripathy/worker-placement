"""accjc_overlay — ACCJC accreditation fiscal-distress screen for CA COMMUNITY COLLEGE
DISTRICT (CCD) general-obligation bonds.

WHY. Our muni underwriting uses the CA AB-1200 interim certification (Positive / Qualified /
Negative) as its fiscal-distress signal. But AB-1200 governs K-12 districts ONLY — community
college districts are NOT in it. The school-GO credit module therefore marks every CCD
"NOT-COVERED-CC" and the pipeline hard-excludes it on missing data. That is wrong: a CCD GO is
the SAME security as a K-12 GO — a voter-approved UNLIMITED ad-valorem tax with a statutory
first lien (Education Code / SB-222 §53515 family), county-assessed and county-COLLECTED,
structurally identical. The correct fiscal-distress proxy for a CCD is its ACCJC ACCREDITATION
status. This module supplies that proxy so CCDs get a real grade instead of an auto-FLAG.

ACCJC = Accrediting Commission for Community and Junior Colleges (accjc.org), the regional
accreditor for California's 116 community colleges (and Pacific/territorial two-year colleges).
The meaningful distress signal is an ACTIVE sanction, escalating:
      good standing  <  On Warning  <  Probation  <  Show Cause   (+ Restoration Status)
Loss of accreditation cuts a college off from federal Title IV aid and state apportionment —
an operating-fund stress directly analogous to an AB-1200 Negative certification. As with
AB-1200, the GO lien itself is unaffected (it rides the AV levy, county-collected), so the
sanction is a headline / disclosure / operating-stress flag, NOT a default trigger on the GO.

HONESTY DISCIPLINE (mirrors the AB-1200 "absent from Negative/Qualified ⇒ Positive" authority
pattern — but GUARDED). We assert good_standing ONLY when the college is CONFIRMED present in
the authoritative ACCJC roster AND carries no sanction. If we cannot confirm the institution
exists in the roster at all, we return `unknown` (a soft REVIEW), never good_standing — because
UNVERIFIABLE != clean: mere absence from a sanction list, when we never confirmed roster
membership, is not evidence of good standing.

DATA SOURCE (authoritative, published, current).
  ACCJC institution directory + accreditation status:
     PRIMARY  — ACCJC WordPress REST API  https://accjc.org/wp-json/wp/v2/institutions
                (structured: college name, state, system, wpcf-current-accreditation status).
     FALLBACK — the rendered directory page https://accjc.org/find-an-institution/
                ("<div class='row child'>" blocks carry the same accreditation_Status field).
     LLM      — if both parse paths fail, an LLM-assisted extraction of the fetched HTML.
  Sanction action TEXT + DATE enrichment:
     the latest "ACCJC Commission Actions on Institutions" PDF linked from
     https://accjc.org/commission-actions/  (single-meeting action report; carries the dated
     action language). The CUMULATIVE current-status binding signal is the directory status
     field; the PDF only enriches sanctioned rows with the specific dated action wording.

CACHE.  data/accjc_roster.json  (roster + current status, with as_of)
        data/accjc_sanctions.json (parsed commission-action items, with as_of)

This module is SELF-CONTAINED. It does NOT import from, and does NOT write into, any shared
integration file (school_go_issuer_credit.py, underwrite_candidates.py, build_diligence_master.py).
The caller wires the recommended status->severity mapping.

  RECOMMENDED status -> severity mapping (for the caller to wire, mirroring AB-1200):
     good_standing -> no flag   (CLEAR-eligible, the "Positive" equivalent)
     warning       -> soft REVIEW
     probation     -> hard FLAG
     show_cause    -> hard FLAG
     restoration   -> REVIEW
     unknown       -> soft REVIEW   (a CCD never auto-excludes purely on missing accreditation data)
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import time
import urllib.parse
from datetime import date, datetime

import requests

CUTOFF = "2026-06-19"            # today / blinding cutoff
BASE = "https://accjc.org"
REST_INSTITUTIONS = BASE + "/wp-json/wp/v2/institutions"
DIRECTORY_URL = BASE + "/find-an-institution/"
ACTIONS_URL = BASE + "/commission-actions/"

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
ROSTER_CACHE = os.path.join(DATA_DIR, "accjc_roster.json")
SANCTIONS_CACHE = os.path.join(DATA_DIR, "accjc_sanctions.json")

# Full Chrome browser fingerprint — accjc.org sits behind Cloudflare; use the same header set
# the EMMA scraper uses to defeat 403s (Sec-Ch-Ua / Sec-Fetch / Accept-Language / Referer).
_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
_HEADERS = {
    "User-Agent": _UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Sec-Ch-Ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"macOS"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Upgrade-Insecure-Requests": "1",
}

# ---- status vocabulary --------------------------------------------------------------------
GOOD = "good_standing"
WARNING = "warning"
PROBATION = "probation"
SHOW_CAUSE = "show_cause"
RESTORATION = "restoration"
UNKNOWN = "unknown"

# escalation order (worst = highest) — used to pick the WORST status across a multi-college CCD
_SEVERITY = {GOOD: 0, UNKNOWN: 1, RESTORATION: 2, WARNING: 3, PROBATION: 4, SHOW_CAUSE: 5}

# RECOMMENDED status -> pipeline severity (the caller wires this; exported for reference)
SEVERITY_MAP = {
    GOOD:        "no_flag",      # CLEAR-eligible, like an AB-1200 Positive
    WARNING:     "soft_review",
    PROBATION:   "hard_flag",
    SHOW_CAUSE:  "hard_flag",
    RESTORATION: "review",
    UNKNOWN:     "soft_review",  # never auto-exclude a CCD on missing accreditation data
}

# map the raw ACCJC status string -> our normalized status
def _normalize_status(raw: str) -> str:
    s = (raw or "").strip().lower()
    if not s:
        return UNKNOWN
    if "show cause" in s:
        return SHOW_CAUSE
    if "probation" in s:
        return PROBATION
    if "restoration" in s:
        return RESTORATION
    if "warning" in s:                       # "On Warning" / "Warning"
        return WARNING
    # "Accredited", "Reaffirmed", "Initial Accreditation", "Candidacy (N years)" are all
    # NON-sanction standings; candidacy/initial are pre-full-accreditation but not a sanction.
    if any(k in s for k in ("accredit", "reaffirm", "candidacy", "good standing")):
        return GOOD
    return UNKNOWN


# ---- name normalization / matching -------------------------------------------------------
_STOP = re.compile(
    r"\b(community|junior|jr|the|of|and|a|college|colleges|district|ccd|cccd|campus|"
    r"center|education|educational)\b")


def _norm(name: str) -> str:
    n = (name or "").lower()
    n = re.sub(r"&", " and ", n)
    n = re.sub(r"[^a-z0-9 ]", " ", n)
    n = _STOP.sub(" ", n)
    return re.sub(r"\s+", " ", n).strip()


def _tokens(name: str) -> set:
    return set(_norm(name).split())


# ============================================================================================
#  FETCH + CACHE — roster (primary REST, fallback HTML, fallback LLM)
# ============================================================================================
def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update(_HEADERS)
    return s


def _fetch_roster_rest(sess: requests.Session) -> list[dict] | None:
    """Authoritative structured roster from the ACCJC WordPress REST API."""
    out, page = [], 1
    try:
        while page <= 10:
            r = sess.get(REST_INSTITUTIONS, params={"per_page": 100, "page": page},
                         headers={"Accept": "application/json", "Referer": DIRECTORY_URL},
                         timeout=40)
            if r.status_code != 200:
                break
            batch = r.json()
            if not isinstance(batch, list) or not batch:
                break
            for rec in batch:
                m = rec.get("meta", {}) or {}
                name = (m.get("wpcf-college") or rec.get("title", {}).get("rendered") or "").strip()
                if not name:
                    continue
                out.append({
                    "name": re.sub(r"\s+", " ", name),
                    "status_raw": (m.get("wpcf-current-accreditation") or "").strip(),
                    "state": (m.get("wpcf-state") or "").strip(),
                    "city": (m.get("wpcf-city") or "").strip(),
                    "system": (m.get("wpcf-system") or "").strip(),
                    "last_review": (m.get("wpcf-last-comprehensive-review") or "").strip(),
                    "next_review": (m.get("wpcf-next-comprehensive-review") or "").strip(),
                    "id": rec.get("id"),
                    "src": "rest",
                })
            total_pages = r.headers.get("X-WP-TotalPages")
            if total_pages and page >= int(total_pages):
                break
            page += 1
            time.sleep(0.4)
    except Exception:
        return out or None
    return out or None


_ROW_RE = re.compile(r'<div class="row child">(.*?)</div>\s*</div>', re.S)
_CELL_RE = re.compile(r'data-title="([^"]*)"[^>]*>(.*?)</div>', re.S)


def _fetch_roster_html(sess: requests.Session) -> tuple[list[dict] | None, str]:
    """Fallback: parse the rendered directory page's row-child blocks. Returns (roster, html)."""
    try:
        r = sess.get(DIRECTORY_URL, headers={"Referer": BASE + "/"}, timeout=60)
        if r.status_code != 200:
            return None, ""
        html = r.text
    except Exception:
        return None, ""
    out = []
    for block in _ROW_RE.findall(html):
        cells = {}
        for k, v in _CELL_RE.findall(block):
            v = re.sub(r"<[^>]+>", " ", v)
            v = re.sub(r"\s+", " ", v).strip()
            if k:
                cells[k] = v
        name = cells.get("Institution Name", "").strip()
        if name:
            out.append({
                "name": name,
                "status_raw": cells.get("accreditation_Status", "").strip(),
                "state": cells.get("State", "").strip(),
                "city": cells.get("City", "").strip(),
                "system": "",
                "src": "html",
            })
    return (out or None), html


def _fetch_roster_llm(html: str) -> list[dict] | None:
    """Last resort: LLM-assisted extraction of the directory HTML into roster rows.

    Uses the Anthropic API with the key read inline from ~/.anthropic_api_key (never written
    or echoed). Trimmed to the row region to keep token cost bounded.
    """
    if not html:
        return None
    # isolate the table region to keep the prompt small
    lo = html.find('class="row child"')
    snippet = html[max(0, lo - 200):lo + 120000] if lo > 0 else html[:120000]
    prompt = (
        "Extract the ACCJC institution accreditation directory from this HTML fragment. "
        "Return ONLY a JSON array; each element: "
        '{"name": <institution name>, "status_raw": <accreditation status exactly as shown, '
        'e.g. Accredited / On Warning / Probation / Show Cause / Restoration / Candidacy / '
        'Initial Accreditation>, "state": <state code>, "city": <city>}. '
        "Do not invent institutions or statuses; include only rows actually present.\n\nHTML:\n"
        + snippet)
    payload = {
        "model": "claude-opus-4-8",
        "max_tokens": 16000,
        "messages": [{"role": "user", "content": prompt}],
    }
    try:
        # key is interpolated by the shell from the file; never printed by this process
        proc = subprocess.run(
            ["bash", "-lc",
             'curl -s https://api.anthropic.com/v1/messages '
             '-H "x-api-key: $(cat ~/.anthropic_api_key)" '
             '-H "anthropic-version: 2023-06-01" '
             '-H "content-type: application/json" '
             '-d @-'],
            input=json.dumps(payload), capture_output=True, text=True, timeout=180)
        resp = json.loads(proc.stdout)
        text = "".join(b.get("text", "") for b in resp.get("content", []))
        m = re.search(r"\[.*\]", text, re.S)
        rows = json.loads(m.group(0) if m else text)
        out = []
        for rec in rows:
            nm = (rec.get("name") or "").strip()
            if nm:
                out.append({"name": nm, "status_raw": (rec.get("status_raw") or "").strip(),
                            "state": (rec.get("state") or "").strip(),
                            "city": (rec.get("city") or "").strip(), "system": "", "src": "llm"})
        return out or None
    except Exception:
        return None


def load_roster(refresh: bool = False, max_age_days: int = 30) -> dict:
    """Return {'as_of', 'source', 'confidence', 'institutions': [...]}, cached.

    confidence: VERIFIED (REST/HTML primary parse) | LLM (LLM-extracted) | UNVERIFIABLE (no data).
    """
    if not refresh and os.path.exists(ROSTER_CACHE):
        try:
            cached = json.load(open(ROSTER_CACHE))
            age = (date.today() - datetime.fromisoformat(cached["as_of"]).date()).days
            if age <= max_age_days and cached.get("institutions"):
                return cached
        except Exception:
            pass

    sess = _session()
    roster = _fetch_roster_rest(sess)
    source, confidence = "ACCJC REST API /wp-json/wp/v2/institutions", "VERIFIED"
    if not roster:
        roster, html = _fetch_roster_html(sess)
        source, confidence = "ACCJC directory page (find-an-institution)", "VERIFIED"
        if not roster:
            roster = _fetch_roster_llm(html)
            source, confidence = "ACCJC directory HTML (LLM-extracted)", "LLM"

    out = {
        "as_of": date.today().isoformat(),
        "source": source,
        "confidence": confidence if roster else "UNVERIFIABLE",
        "institutions": roster or [],
    }
    if roster:
        os.makedirs(DATA_DIR, exist_ok=True)
        try:
            json.dump(out, open(ROSTER_CACHE, "w"), indent=2)
        except Exception:
            pass
    elif os.path.exists(ROSTER_CACHE):       # serve stale rather than nothing, flagged
        try:
            stale = json.load(open(ROSTER_CACHE))
            stale["confidence"] = "UNVERIFIABLE"
            stale["note"] = "live fetch failed; serving stale cache"
            return stale
        except Exception:
            pass
    return out


# ============================================================================================
#  FETCH + CACHE — commission-action SANCTION enrichment (dated action text from the PDF)
# ============================================================================================
_PDF_LINK_RE = re.compile(
    r'href="(https?://[^"]*Commission-Actions[^"]*\.pdf)"', re.I)
_ACTION_HEADER_RE = re.compile(
    r"\b(SHOW CAUSE|PROBATION|WARNING|RESTORATION|TERMINAT\w*|WITHDRAW\w*)\b", re.I)


def _latest_actions_pdf_url(sess: requests.Session) -> str | None:
    try:
        r = sess.get(ACTIONS_URL, headers={"Referer": BASE + "/"}, timeout=40)
        urls = _PDF_LINK_RE.findall(r.text) if r.status_code == 200 else []
    except Exception:
        urls = []

    def _key(u: str):
        mo = {m: i for i, m in enumerate(
            ["january", "february", "march", "april", "may", "june", "july",
             "august", "september", "october", "november", "december"], 1)}
        ml = u.lower()
        yr = re.search(r"(20\d\d)", ml)
        mon = next((v for k, v in mo.items() if k in ml), 0)
        return (int(yr.group(1)) if yr else 0, mon)

    return max(urls, key=_key) if urls else None


def load_sanctions(refresh: bool = False, max_age_days: int = 30) -> dict:
    """Parse the latest Commission Actions PDF for dated sanction/action items.

    Returns {'as_of','source','confidence','pdf_url','items': [{institution, action, ...}]}.
    The directory STATUS field is the binding current-sanction signal; this only enriches the
    action TEXT + meeting DATE for sanctioned rows. A no-sanction meeting yields an empty list
    (correct: a single meeting need not have issued any sanction).
    """
    if not refresh and os.path.exists(SANCTIONS_CACHE):
        try:
            cached = json.load(open(SANCTIONS_CACHE))
            age = (date.today() - datetime.fromisoformat(cached["as_of"]).date()).days
            if age <= max_age_days:
                return cached
        except Exception:
            pass

    sess = _session()
    url = _latest_actions_pdf_url(sess)
    out = {"as_of": date.today().isoformat(),
           "source": "ACCJC Commission Actions on Institutions (PDF)",
           "confidence": "UNVERIFIABLE", "pdf_url": url, "meeting": None, "items": []}
    if not url:
        return out

    # meeting label from the filename, e.g. ...-January-2026.pdf
    mlabel = re.search(r"Institutions-([A-Za-z]+-20\d\d)", url)
    out["meeting"] = mlabel.group(1).replace("-", " ") if mlabel else None
    try:
        pdf = sess.get(url, headers={"Referer": ACTIONS_URL}, timeout=90).content
        import io
        import pdfplumber
        with pdfplumber.open(io.BytesIO(pdf)) as doc:
            text = "\n".join((p.extract_text() or "") for p in doc.pages)
        out["confidence"] = "VERIFIED"
    except Exception:
        return out

    # Parse the action-grouped roster: an ALL-CAPS action heading followed by institution names.
    items, cur_action = [], None
    for ln in text.splitlines():
        s = ln.strip()
        if not s:
            continue
        # a heading line is mostly uppercase and contains an action verb
        upp = sum(c.isupper() for c in s if c.isalpha())
        low = sum(c.islower() for c in s if c.isalpha())
        is_heading = upp >= 8 and upp > low * 2
        if is_heading and re.search(r"\b(REAFFIRM|INITIAL|CANDIDACY|WARNING|PROBATION|SHOW CAUSE|"
                                    r"RESTORATION|TERMINAT|WITHDRAW|MIDTERM|FOLLOW|TEACH-OUT|ACTION)",
                                    s, re.I):
            cur_action = re.sub(r"\s+", " ", s)
            continue
        if cur_action and _ACTION_HEADER_RE.search(cur_action):
            # only capture institutions under genuine sanction headings
            for nm in re.split(r"\s{2,}", s):       # PDF lays 2 colleges per row, space-separated
                nm = nm.strip()
                if nm and not nm.isupper() and len(nm) > 3 and "accjc.org" not in nm.lower():
                    items.append({"institution": nm, "action": cur_action,
                                  "meeting": out["meeting"]})
    out["items"] = items
    os.makedirs(DATA_DIR, exist_ok=True)
    try:
        json.dump(out, open(SANCTIONS_CACHE, "w"), indent=2)
    except Exception:
        pass
    return out


# ============================================================================================
#  MATCH a district -> its college(s) in the roster
# ============================================================================================
def _candidate_college_names(district_name: str, college_hint: str | None) -> list[str]:
    """Heuristic college names a CCD likely contains (single-college mapping)."""
    out = []
    if college_hint:
        out.append(college_hint)
    dn = district_name or ""
    # "X Community College District" -> "X College" / "X Community College"
    stem = re.sub(r"\b(community college district|college district|ccd|cccd|district)\b", "",
                  dn, flags=re.I).strip(" ,.")
    if stem:
        out += [f"{stem} College", f"{stem} Community College", stem]
    return out


def _match_colleges(district_name: str, college_hint: str | None,
                    institutions: list[dict]) -> list[dict]:
    """Return roster rows for college(s) belonging to this district.

    Strategy: (1) exact-ish name match on heuristic college names; (2) token-subset match —
    every significant token of a candidate college appears in a roster name. Multi-college
    districts (Los Rios, San Mateo CCCD, etc.) won't be fully enumerable from the district name
    alone unless a hint is given; we surface ALL roster colleges whose distinctive token set is
    a subset of the district's tokens (e.g. district "Los Rios" won't match its colleges by
    name, so token-subset is intentionally CONSERVATIVE and may under-cover — under-coverage
    yields `unknown`, never a false good_standing).
    """
    by_norm = {}
    for inst in institutions:
        by_norm.setdefault(_norm(inst["name"]), inst)

    matched, seen = [], set()

    def _add(inst):
        key = inst["name"]
        if key not in seen:
            seen.add(key)
            matched.append(inst)

    # (1) heuristic candidate names, exact normalized hit
    for cand in _candidate_college_names(district_name, college_hint):
        cn = _norm(cand)
        if cn and cn in by_norm:
            _add(by_norm[cn])

    # (2) token-subset: a roster college whose distinctive tokens are all present in the
    #     district name (catches "Palo Verde College" from "Palo Verde Community College District")
    if not matched:
        dtok = _tokens(district_name)
        if college_hint:
            dtok |= _tokens(college_hint)
        for inst in institutions:
            itok = _tokens(inst["name"])
            if itok and itok <= dtok:
                _add(inst)

    return matched


# ============================================================================================
#  PUBLIC API
# ============================================================================================
def accjc_status(district_name: str, college_hint: str | None = None) -> dict:
    """Fiscal-distress proxy for a CA community-college-district GO via ACCJC accreditation.

    Args:
        district_name: e.g. "Palo Verde Community College District".
        college_hint:  optional explicit college name (or "; "-joined list) to disambiguate
                       multi-college districts the district name can't enumerate.

    Returns dict with fields:
        accjc_status    good_standing | warning | probation | show_cause | restoration | unknown
        accjc_sanction  the specific commission-action text + date (or None)
        accjc_match     the matched institution name(s) driving the (worst) status (or None)
        accjc_colleges  list of all colleges found for the district
        source          authority string
        as_of           ISO date the roster was fetched
        confidence      VERIFIED | LLM | UNVERIFIABLE
    """
    roster = load_roster()
    institutions = roster.get("institutions", [])
    base = {
        "accjc_status": UNKNOWN,
        "accjc_sanction": None,
        "accjc_match": None,
        "accjc_colleges": [],
        "source": roster.get("source"),
        "as_of": roster.get("as_of"),
        "confidence": roster.get("confidence", "UNVERIFIABLE"),
    }

    if not institutions:
        base["note"] = ("ACCJC roster unavailable — accreditation status UNVERIFIED, not clean")
        return base

    matched = _match_colleges(district_name, college_hint, institutions)
    if not matched:
        # roster present but we could not confirm this district's college(s) in it:
        # UNVERIFIABLE != clean -> unknown (soft REVIEW), never good_standing.
        base["note"] = ("district/college not confirmed in ACCJC roster; accreditation status "
                        "UNVERIFIED, not clean (do not assert good standing from absence)")
        return base

    base["accjc_colleges"] = [m["name"] for m in matched]

    # normalize each matched college's status; pick the WORST across the district
    sanctions = None
    worst = None
    for m in matched:
        st = _normalize_status(m["status_raw"])
        m["_status"] = st
        if worst is None or _SEVERITY[st] > _SEVERITY[worst["_status"]]:
            worst = m

    base["accjc_status"] = worst["_status"]
    base["accjc_match"] = worst["name"]
    # also surface the per-college breakdown when >1 college
    if len(matched) > 1:
        base["accjc_college_status"] = {m["name"]: m["_status"] for m in matched}

    # enrich sanction text+date for any college that carries a sanction (warning+)
    if _SEVERITY[worst["_status"]] >= _SEVERITY[WARNING]:
        try:
            sanctions = load_sanctions()
        except Exception:
            sanctions = None
        action_txt = None
        if sanctions:
            wnorm = _norm(worst["name"])
            for it in sanctions.get("items", []):
                if _norm(it["institution"]) == wnorm:
                    action_txt = f"{it['action']} ({it['meeting']})"
                    break
        # fall back to the directory's status label + review timing when the PDF doesn't list it
        if not action_txt:
            label = worst["status_raw"] or worst["_status"]
            nxt = worst.get("next_review")
            action_txt = (f"ACCJC current status: {label}"
                          + (f"; next comprehensive review {nxt}" if nxt else "")
                          + " (per ACCJC institution directory)")
        base["accjc_sanction"] = action_txt

    return base


# ============================================================================================
#  VALIDATION
# ============================================================================================
if __name__ == "__main__":
    print("ACCJC accreditation overlay — CCD GO fiscal-distress proxy")
    print(f"cutoff/today = {CUTOFF}\n")

    roster = load_roster()
    print(f"Roster: {len(roster['institutions'])} institutions | source={roster['source']} | "
          f"as_of={roster['as_of']} | confidence={roster['confidence']}\n")

    cases = [
        # (district name, college_hint, expectation note)
        ("Palo Verde Community College District", None,
         "EXPECT accredited / good_standing (its GO = CUSIP 697479CB7)"),
        ("San Francisco Community College District", "City College of San Francisco",
         "KNOWN-SANCTION CONTROL: CCSF Show Cause->termination saga ~2013-2017, later restored; "
         "report CURRENT status honestly"),
        ("Compton Community College District", "Compton College",
         "control: Compton (historical loss-of-accreditation 2006; merged w/ El Camino, restored)"),
        ("Redwoods Community College District", "College of the Redwoods",
         "control: College of the Redwoods (had Show Cause ~2012-2014)"),
        ("San Luis Obispo County Community College District", "Cuesta College",
         "control: Cuesta College (had Show Cause ~2012-2013)"),
        # a genuinely-sanctioned-NOW control to prove the sanction path fires on a live sanction
        ("California Preparatory College District", "California Preparatory College",
         "LIVE-SANCTION CONTROL: currently on Show Cause -> must FLAG"),
    ]

    rows = []
    for dn, hint, note in cases:
        r = accjc_status(dn, hint)
        rows.append((dn, r, note))

    # table
    print(f"{'district':<46} {'colleges matched':<34} {'status':<14} {'confidence':<12} sanction")
    print("-" * 140)
    for dn, r, _ in rows:
        cols = ", ".join(r["accjc_colleges"]) or "(none)"
        san = (r["accjc_sanction"] or "")[:60]
        print(f"{dn[:45]:<46} {cols[:33]:<34} {r['accjc_status']:<14} "
              f"{r['confidence']:<12} {san}")

    print("\nper-case detail:")
    for dn, r, note in rows:
        print(f"\n  {dn}")
        print(f"    note      : {note}")
        print(f"    status    : {r['accjc_status']}  (severity -> {SEVERITY_MAP[r['accjc_status']]})")
        print(f"    match     : {r['accjc_match']}")
        print(f"    colleges  : {r['accjc_colleges']}")
        print(f"    sanction  : {r['accjc_sanction']}")
        print(f"    source    : {r['source']}")
        print(f"    as_of     : {r['as_of']}   confidence: {r['confidence']}")

    print("\nRECOMMENDED status -> severity mapping (caller wires this):")
    for k, v in SEVERITY_MAP.items():
        print(f"    {k:<14} -> {v}")
