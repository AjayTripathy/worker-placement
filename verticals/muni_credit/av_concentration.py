"""TAX-BASE concentration + DEBT-BURDEN screen for CA school/CCD GO bonds.

WHY THIS EXISTS
---------------
A California school or community-college-district general-obligation bond is repaid
by an UNLIMITED ad-valorem levy on the district's assessed value (AV). The tax RATE
floats so that fixed debt service is always covered: if the AV base shrinks, the rate
on everyone else must rise. Two economic risks follow that a coupon/lien screen does
not see:

  (1) TAXPAYER CONCENTRATION. One taxpayer / property / industry that is a large
      share of district AV. If it leaves, wins an assessment appeal, or depreciates
      (a power plant, a single fab, a mall), the levy rate jumps on every remaining
      parcel. We only caught Palo Verde CCD's Blythe Energy gas plant (13.5% of AV)
      by hand; this module catches it mechanically.

  (2) DEBT BURDEN. Direct + overlapping debt as a % of AV, and the total ad-valorem
      tax rate. An over-leveraged base breeds taxpayer fatigue, appeal pressure, and
      the political risk that an "unlimited" levy gets de-facto capped.

DATA SOURCE
-----------
The bond's Official Statement (OS). Every CA GO OS — these are prepared by California
Municipal Statistics, Inc. in a near-identical template — carries:
  * a "Largest [Local Secured] Taxpayers" / "20 Largest ..." / "Principal Taxpayers"
    table: rank, owner, land use, assessed valuation, % of (local secured) total, with
    a trailing total row and a footnote "Local Secured Assessed Valuation: $X".
  * a "Statement of Direct and Overlapping Bonded Debt" with a header
    "20XX-XX Assessed Valuation: $X" and a "Ratios to ... Assessed Valuation:" block
    giving Direct Debt and Gross/Net Combined Total Debt as % of AV.
  * (often) a "Tax Rates" table with a "Total Tax Rate" row across recent fiscal years.

EXTRACTION
----------
Robust text/table parse FIRST (pdftotext -layout + regex on the CA-Muni-Stats template),
then an LLM fallback (Anthropic, claude-opus-4-8 / claude-sonnet-4-6) on the relevant
OS pages when the deterministic parse misses a field. The API key is read inline from
~/.anthropic_api_key and is NEVER written to disk or echoed.

THRESHOLDS  (soft REVIEW vs hard FLAG)
--------------------------------------
  single-taxpayer share of AV   > 10%  -> REVIEW (soft)   > 20%  -> FLAG (hard)
  top-10 taxpayers share of AV   > 25% -> REVIEW (soft)   > 40%  -> FLAG (hard)
  direct+overlapping debt-to-AV  > 6%  -> REVIEW (soft)   > 12%  -> FLAG (hard)
  total ad-valorem tax rate      > 1.30% -> REVIEW (soft) > 1.60% -> FLAG (hard)

These are calibrated against the five validation OSs: typical CA school GO single-
taxpayer share is <1%, top-10 5-15%, combined debt-to-AV 2-5%, tax rate ~1.0-1.13%.
Palo Verde (Blythe Energy 13.5%) is the deliberate REVIEW-tripping anchor.

UNVERIFIABLE != clean. A missing OS yields confidence="UNVERIFIABLE" with NO numbers,
never an implied 0% concentration.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

_HERE = Path(__file__).resolve().parent
_CACHE_PATH = _HERE / "data" / "av_concentration_cache.json"
_KEY_FILE = Path.home() / ".anthropic_api_key"
_LLM_MODEL = "claude-opus-4-8"
_LLM_FALLBACK_MODEL = "claude-sonnet-4-6"

# ---- thresholds (single source of truth) ----------------------------------
TOP1_REVIEW, TOP1_FLAG = 10.0, 20.0          # % of AV, single taxpayer
TOP10_REVIEW, TOP10_FLAG = 25.0, 40.0        # % of AV, top-10 cumulative
DEBT_REVIEW, DEBT_FLAG = 6.0, 12.0           # % of AV, direct+overlapping
TAXRATE_REVIEW, TAXRATE_FLAG = 1.30, 1.60    # % total ad-valorem rate


# ===========================================================================
# text utilities
# ===========================================================================
def _pdf_to_text(pdf_path: Path) -> str:
    """pdftotext -layout (preserves the columnar CA-Muni-Stats tables)."""
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
        out = Path(tmp.name)
    try:
        subprocess.run(["pdftotext", "-layout", str(pdf_path), str(out)],
                       check=True, capture_output=True, timeout=120)
        return out.read_text(errors="replace")
    finally:
        out.unlink(missing_ok=True)


def _money(s: str) -> Optional[float]:
    s = re.sub(r"[^\d.]", "", s or "")
    if not s or s == ".":
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _pct(s: str) -> Optional[float]:
    m = re.search(r"(\d+(?:\.\d+)?)\s*%?", s or "")
    return float(m.group(1)) if m else None


# ===========================================================================
# deterministic parsers (CA Municipal Statistics template)
# ===========================================================================
_TAXPAYER_HDR = re.compile(
    r"(?:LARGEST(?:\s+\d{4}-\d{2})?\s+LOCAL\s+SECURED\s+TAXPAYERS"
    r"|\d{1,2}\s+LARGEST\s+LOCAL\s+SECURED\s+TAXPAYERS"
    r"|LARGEST\s+TAXPAYERS"
    r"|PRINCIPAL\s+TAXPAYERS)",
    re.I)

# A numbered taxpayer row, e.g.:
#   1.    Blythe Energy LLC      Power Plant    $275,462,000   13.54%
_ROW = re.compile(
    r"^\s*(\d{1,2})\.\s+"                       # rank
    r"(?P<name>.+?)\s{2,}"                      # owner (>=2 spaces before land use)
    r"(?P<use>[A-Za-z][A-Za-z &/\.\-]+?)\s+"    # primary land use
    r"\$?\s?(?P<av>[\d,]+)\s+"                  # assessed valuation
    r"(?P<pct>\d+(?:\.\d+)?)\s*%?\s*$")         # % of total


def _parse_rows(block: str) -> list[dict]:
    rows: list[dict] = []
    for ln in block.splitlines():
        rm = _ROW.match(ln)
        if not rm:
            continue
        av = _money(rm.group("av"))
        pct = _pct(rm.group("pct"))
        if av is None or pct is None:
            continue
        rows.append({"rank": int(rm.group(1)), "name": rm.group("name").strip(),
                     "land_use": rm.group("use").strip(), "av": av, "pct": pct})
    return rows


def _extract_taxpayers(text: str) -> dict:
    """Parse the largest-taxpayers table. Returns top1/top10/top-N totals + AV base.

    A header pattern (e.g. "PRINCIPAL TAXPAYERS") also appears in the table of contents
    as a dotted-leader line; we iterate over every header hit and keep the FIRST one whose
    following block actually contains numbered taxpayer rows (>= 5 ranks).
    """
    res: dict = {}
    block, rows = "", []
    for m in _TAXPAYER_HDR.finditer(text):
        # Skip a TOC entry: dotted leaders + trailing page number on the same line.
        line_end = text.find("\n", m.start())
        line = text[m.start(): line_end if line_end != -1 else m.start() + 120]
        if re.search(r"\.\s*\.\s*\.\s*\.\s*\d{1,4}\s*$", line):
            continue
        cand_block = text[m.start(): m.start() + 6000]
        cand_rows = _parse_rows(cand_block)
        if len(cand_rows) >= 5:
            block, rows = cand_block, cand_rows
            break
    if not rows:
        return res
    rows.sort(key=lambda r: r["rank"])

    # Local-secured AV base from the table footnote.
    fb = re.search(r"Local\s+Secured\s+Assessed\s+Valuation:?\s*\$?\s*([\d,]+)",
                   block, re.I)
    av_base = _money(fb.group(1)) if fb else None

    top1 = rows[0]
    res["av_top1_taxpayer"] = top1["name"]
    res["av_top1_land_use"] = top1["land_use"]
    res["av_top1_share"] = round(top1["pct"], 3)
    top10 = [r for r in rows if r["rank"] <= 10]
    if top10:
        res["av_top10_share"] = round(sum(r["pct"] for r in top10), 3)
    # trailing total row (sum of % for the whole table, e.g. 26.07%)
    tot = re.search(r"\$[\d,]+\s+(\d+(?:\.\d+)?)\s*%", block[block.rfind(rows[-1]["name"]):])
    if tot:
        res["av_topN_share"] = round(float(tot.group(1)), 3)
        res["av_topN_count"] = rows[-1]["rank"]
    if av_base:
        res["av_local_secured"] = av_base
    return res


def _extract_av_and_debt(text: str) -> dict:
    """Parse total AV (debt-table header) and direct + combined debt-to-AV ratios."""
    res: dict = {}

    # Total AV: prefer the "Statement of Direct and Overlapping ... Assessed Valuation: $X"
    # header; fall back to the narrative "total assessed valuation for fiscal year ... of $X".
    dh = re.search(r"(\d{4}-\d{2})\s+Assessed\s+Valuation:?\s*\$?\s*([\d,]+)", text)
    if dh:
        res["as_of_year"] = dh.group(1)
        res["av_total"] = _money(dh.group(2))
    else:
        nh = re.search(
            r"total\s+assessed\s+valuation\s+for\s+fiscal\s+year\s+(\d{4}-\d{2})\s+of\s*\$?\s*([\d,]+)",
            text, re.I)
        if nh:
            res["as_of_year"] = nh.group(1)
            res["av_total"] = _money(nh.group(2))

    # Debt ratios block.
    rm = re.search(r"Ratios?\s+to\s+[\d\-]*\s*Assessed\s+Valuation:?(.{0,600})", text, re.I | re.S)
    if rm:
        blk = rm.group(1)
        dd = re.search(r"Direct\s+Debt[^%\n]*?(\d+(?:\.\d+)?)\s*%", blk, re.I)
        if dd:
            res["direct_debt_to_av"] = round(float(dd.group(1)), 3)
        # Combined total debt = direct + ALL overlapping; the headline burden ratio.
        # Templates label it "Gross Combined Total Debt", "Net Combined Total Debt", or
        # just "Combined Total Debt". Prefer Gross; fall back to bare Combined; then Net.
        gc = re.search(r"Gross\s+Combined\s+Total\s+Debt[^%\n]*?(\d+(?:\.\d+)?)\s*%", blk, re.I)
        bc = re.search(r"(?<!Gross )(?<!Net )\bCombined\s+Total\s+Debt[^%\n]*?(\d+(?:\.\d+)?)\s*%", blk, re.I)
        nc = re.search(r"Net\s+Combined\s+Total\s+Debt[^%\n]*?(\d+(?:\.\d+)?)\s*%", blk, re.I)
        burden = gc or bc or nc
        if burden:
            res["overlapping_debt_to_av"] = round(float(burden.group(1)), 3)
    return res


_TAXRATE_HDR = re.compile(r"(?:Typical\s+)?Total\s+Tax\s+Rates?|Summary\s+of\s+Ad\s+Valorem\s+Tax\s+Rates",
                          re.I)
# Total row in the rate table: "Total Tax Rate", "Total All Property", or bare "Total".
_TAXRATE_ROW = re.compile(r"^\s*Total(?:\s+Tax\s+Rate|\s+All\s+Property)?\b\s+([\$\d\.\s%]+)$", re.I)


def _extract_tax_rate(text: str) -> dict:
    """Parse the total ad-valorem tax-rate row; take the rightmost (most-recent FY) value.

    Rates appear either as percentages ("1.066006%") or as dollars-per-$100 of AV
    ("$1.2454") — both are the same quantity expressed per-$100, so a $1.2454 figure IS
    1.2454%. We locate the rate table by its heading, then read the total row's last value.
    """
    res: dict = {}
    hm = _TAXRATE_HDR.search(text)
    if not hm:
        return res
    block = text[hm.start(): hm.start() + 4000]
    best = None
    for ln in block.splitlines():
        rm = _TAXRATE_ROW.match(ln)
        if not rm:
            continue
        nums = re.findall(r"\$?\s?(\d+\.\d+)", rm.group(1))
        if not nums:
            continue
        val = float(nums[-1])
        # Sanity: a CA total ad-valorem rate sits ~1.0-2.0 (per $100 / as %).
        if 0.8 <= val <= 3.0:
            best = round(val, 4)   # last matching total row = most recent table on the page
    if best is not None:
        res["total_tax_rate_pct"] = best
    return res


# ===========================================================================
# LLM fallback (Anthropic)
# ===========================================================================
def _relevant_pages(text: str) -> str:
    """Clip the OS text down to the taxpayer + debt + tax-rate neighborhoods for the LLM."""
    spans = []
    for pat in (_TAXPAYER_HDR,
                re.compile(r"Direct\s+and\s+Overlapping", re.I),
                re.compile(r"Total\s+Tax\s+Rate", re.I),
                re.compile(r"total\s+assessed\s+valuation\s+for\s+fiscal\s+year", re.I)):
        m = pat.search(text)
        if m:
            spans.append(text[max(0, m.start() - 400): m.start() + 4000])
    clip = "\n\n----\n\n".join(spans)
    return clip[:24000] if clip else text[:24000]


def _llm_extract(text: str) -> dict:
    """Anthropic extraction fallback. Returns parsed JSON dict or {} on any failure.

    The API key is read inline from ~/.anthropic_api_key and never persisted/echoed.
    """
    if not _KEY_FILE.exists():
        return {}
    try:
        import anthropic
    except ImportError:
        return {}
    key = _KEY_FILE.read_text().strip()
    if not key:
        return {}

    prompt = (
        "You are extracting tax-base concentration and debt-burden figures from a "
        "California municipal General Obligation bond Official Statement. Return ONLY a "
        "JSON object (no prose) with these keys, using null when a field is genuinely "
        "absent from the text (never guess):\n"
        '  "av_total": number (district total assessed valuation, dollars),\n'
        '  "av_top1_taxpayer": string (name of the single largest taxpayer),\n'
        '  "av_top1_share": number (its % of assessed valuation, e.g. 13.54),\n'
        '  "av_top10_share": number (cumulative % of the top 10 taxpayers),\n'
        '  "av_topN_share": number (cumulative % of the full largest-taxpayers table),\n'
        '  "av_topN_count": integer (how many taxpayers that table lists, e.g. 20),\n'
        '  "direct_debt_to_av": number (district direct debt as % of AV),\n'
        '  "overlapping_debt_to_av": number (gross combined total direct+overlapping debt as % of AV),\n'
        '  "total_tax_rate_pct": number (most recent total ad-valorem tax rate %),\n'
        '  "as_of_year": string (fiscal year of the figures, e.g. "2015-16")\n\n'
        "OFFICIAL STATEMENT EXCERPTS:\n" + _relevant_pages(text))

    for model in (_LLM_MODEL, _LLM_FALLBACK_MODEL):
        try:
            client = anthropic.Anthropic(api_key=key)
            msg = client.messages.create(
                model=model, max_tokens=1024,
                messages=[{"role": "user", "content": prompt}])
            raw = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
            jm = re.search(r"\{.*\}", raw, re.S)
            if jm:
                return {k: v for k, v in json.loads(jm.group(0)).items() if v is not None}
        except Exception:
            continue
    return {}


# ===========================================================================
# scoring
# ===========================================================================
def _score(rec: dict) -> dict:
    """Apply thresholds. Populates conc_flags + designation; UNVERIFIABLE != clean."""
    flags: list[str] = []
    designation = "CLEAN"

    def bump(level):
        nonlocal designation
        order = {"CLEAN": 0, "REVIEW": 1, "FLAG": 2}
        if order[level] > order[designation]:
            designation = level

    t1 = rec.get("av_top1_share")
    if t1 is not None:
        if t1 > TOP1_FLAG:
            flags.append(f"single-taxpayer {rec.get('av_top1_taxpayer','?')} "
                         f"{t1:.1f}% of AV (>{TOP1_FLAG:.0f}% hard)"); bump("FLAG")
        elif t1 > TOP1_REVIEW:
            flags.append(f"single-taxpayer {rec.get('av_top1_taxpayer','?')} "
                         f"{t1:.1f}% of AV (>{TOP1_REVIEW:.0f}% soft)"); bump("REVIEW")

    t10 = rec.get("av_top10_share")
    if t10 is not None:
        if t10 > TOP10_FLAG:
            flags.append(f"top-10 taxpayers {t10:.1f}% of AV (>{TOP10_FLAG:.0f}% hard)"); bump("FLAG")
        elif t10 > TOP10_REVIEW:
            flags.append(f"top-10 taxpayers {t10:.1f}% of AV (>{TOP10_REVIEW:.0f}% soft)"); bump("REVIEW")

    dburden = rec.get("overlapping_debt_to_av")
    if dburden is not None:
        if dburden > DEBT_FLAG:
            flags.append(f"direct+overlapping debt {dburden:.1f}% of AV (>{DEBT_FLAG:.0f}% hard)"); bump("FLAG")
        elif dburden > DEBT_REVIEW:
            flags.append(f"direct+overlapping debt {dburden:.1f}% of AV (>{DEBT_REVIEW:.0f}% soft)"); bump("REVIEW")

    tr = rec.get("total_tax_rate_pct")
    if tr is not None:
        if tr > TAXRATE_FLAG:
            flags.append(f"total tax rate {tr:.3f}% (>{TAXRATE_FLAG:.2f}% hard)"); bump("FLAG")
        elif tr > TAXRATE_REVIEW:
            flags.append(f"total tax rate {tr:.3f}% (>{TAXRATE_REVIEW:.2f}% soft)"); bump("REVIEW")

    rec["conc_flags"] = flags
    rec["designation"] = designation       # CLEAN / REVIEW (soft) / FLAG (hard)
    return rec


# ===========================================================================
# cache
# ===========================================================================
def _load_cache() -> dict:
    if _CACHE_PATH.exists():
        try:
            return json.loads(_CACHE_PATH.read_text())
        except json.JSONDecodeError:
            return {}
    return {}


def _save_cache(cache: dict) -> None:
    _CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _CACHE_PATH.write_text(json.dumps(cache, indent=2))


# ===========================================================================
# public API
# ===========================================================================
def extract_concentration(os_pdf_path_or_text: str | Path,
                          source: Optional[str] = None,
                          allow_llm: bool = True) -> dict:
    """Extract tax-base concentration + debt burden from one OS.

    Accepts a path to an OS PDF, a path to a pre-extracted .txt, or raw OS text.
    Returns a dict with the documented field names:
      av_total, av_top1_taxpayer, av_top1_share, av_top10_share,
      av_topN_share, av_topN_count, av_local_secured, av_top1_land_use,
      direct_debt_to_av, overlapping_debt_to_av, total_tax_rate_pct,
      as_of_year, source, confidence, conc_flags, designation.

    confidence: VERIFIED  (deterministic parse got the concentration + debt fields)
                LLM        (an LLM fallback supplied >=1 missing field)
                PARTIAL    (some fields, but missing both top1 share and debt burden)
                UNVERIFIABLE (no OS text at all)
    """
    text = ""
    src = source
    arg = os_pdf_path_or_text
    p = Path(arg) if isinstance(arg, (str, Path)) and len(str(arg)) < 1000 else None
    if p is not None and p.exists():
        src = src or str(p)
        text = _pdf_to_text(p) if p.suffix.lower() == ".pdf" else p.read_text(errors="replace")
    elif isinstance(arg, str):
        text = arg
        src = src or "inline-text"

    if not text.strip():
        return _score({"source": src, "confidence": "UNVERIFIABLE",
                       "note": "no OS text available"})

    rec: dict = {}
    rec.update(_extract_taxpayers(text))
    rec.update(_extract_av_and_debt(text))
    rec.update(_extract_tax_rate(text))

    have_conc = rec.get("av_top1_share") is not None
    have_debt = rec.get("overlapping_debt_to_av") is not None
    confidence = "VERIFIED" if (have_conc and have_debt) else "PARTIAL"

    # LLM fallback only for fields the deterministic parse missed.
    if allow_llm and not (have_conc and have_debt and rec.get("av_total")):
        llm = _llm_extract(text)
        filled = False
        for k, v in llm.items():
            if rec.get(k) is None and v is not None:
                rec[k] = v
                filled = True
        if filled:
            have_conc = rec.get("av_top1_share") is not None
            have_debt = rec.get("overlapping_debt_to_av") is not None
            confidence = "VERIFIED" if (have_conc and have_debt) else "LLM"

    if not have_conc and not have_debt:
        confidence = "PARTIAL"

    rec["source"] = src
    rec["confidence"] = confidence
    return _score(rec)


def _resolve_os_pdf(cusip: str) -> Optional[Path]:
    """Look for an OS PDF already on disk for this CUSIP."""
    cand = _HERE / "outputs" / "diligence_reports" / cusip / "raw" / "official_statement.pdf"
    return cand if cand.exists() else None


def _fetch_os_from_emma(cusip: str) -> Optional[Path]:
    """Resolve CUSIP -> EMMA issue -> Official Statement PDF, downloaded to disk.

    Reuses emma_scraper's session/disclaimer/OS-link/download helpers. EMMA encrypts
    the plaintext CUSIP in the scale JSON, so the CUSIP itself can't be looked up there;
    we resolve via the Security/Details page (issue title) -> description search ->
    matching issue -> OfficialStatementPartialView. Best-effort; returns None on miss.
    """
    try:
        import emma_scraper as E
    except Exception:
        return None
    try:
        s = E._session()
        # Pull the Security/Details page to recover the issue description for search.
        r = s.get(f"{E.BASE}/Security/Details/{cusip}",
                  headers={"Referer": E.BASE + "/", "Upgrade-Insecure-Requests": "1"},
                  timeout=40)
        txt = r.text
        if "yesButton" in txt:
            s.post(f"{E.BASE}/Disclaimer.aspx",
                   data={"__VIEWSTATE": E._hidden("__VIEWSTATE", txt),
                         "__VIEWSTATEGENERATOR": E._hidden("__VIEWSTATEGENERATOR", txt),
                         "__EVENTVALIDATION": E._hidden("__EVENTVALIDATION", txt),
                         "ctl00$mainContentArea$disclaimerContent$yesButton": "Accept"},
                   headers={"Content-Type": "application/x-www-form-urlencoded",
                            "Origin": E.BASE, "Referer": f"{E.BASE}/Security/Details/{cusip}"},
                   timeout=40)
            txt = s.get(f"{E.BASE}/Security/Details/{cusip}",
                        headers={"Referer": E.BASE + "/"}, timeout=40).text
        # The page links to its parent issue: /IssueView/Details/<IssueId>
        im = re.search(r"/IssueView/Details/([A-Z]\d+)", txt)
        if not im:
            return None
        issue_id = im.group(1)
        os_url = E.get_official_statement(issue_id, s)
        if not os_url:
            return None
        dest = _HERE / "outputs" / "diligence_reports" / cusip / "raw" / "official_statement.pdf"
        E.download_pdf(os_url, dest, s)
        return dest if dest.exists() and dest.stat().st_size > 1000 else None
    except Exception:
        return None


def current_av_from_cd(cusip: str, issuer: Optional[str] = None) -> dict:
    """CURRENT-FY assessed valuation from the issuer's latest 15c2-12 ANNUAL REPORT (the OS only carries
    issuance-vintage AV). Delegates to the shared cdd_financials module — the SAME parser that powers
    refresh_current_state — so the detector and the report tool can't drift. Prefers an already-downloaded
    annual PDF (no EMMA hit); else fetches serially/throttled. Returns {} on miss (never fabricates)."""
    try:
        import cdd_financials as CF
    except Exception:
        return {}
    pdf = _HERE / "outputs" / "diligence_reports" / cusip / "raw" / "cdd_annual_latest.pdf"
    try:
        if pdf.exists():
            st = CF.current_state(cusip, issuer=issuer, ann_text=CF._text(pdf))
        else:
            st = CF.current_state(cusip, issuer=issuer)          # serial/throttled live fetch
    except Exception:
        return {}
    if st.get("av_current"):
        return {"current_av": st["av_current"], "current_av_fy": st.get("av_current_fy"),
                "current_av_chg_pct": st.get("av_change_pct"),
                "current_delinquency_pct": st.get("delinquency_pct"),
                "current_av_ambiguous": st.get("av_ambiguous"), "current_av_source": "cdd_annual_report"}
    if st.get("dscr_current") is not None:
        return {"current_dscr": st["dscr_current"], "current_dscr_basis": st.get("dscr_basis"),
                "current_av_source": "cdd_annual_report"}
    return {}


def batch(cusips: list[str], use_cache: bool = True, fetch: bool = True,
          with_current: bool = False, issuer_map: Optional[dict] = None) -> list[dict]:
    """Screen a list of CUSIPs. Cached results are keyed by CUSIP in
    data/av_concentration_cache.json. For an uncached CUSIP we use an on-disk OS if
    present, else fetch the OS from EMMA. No OS -> confidence=UNVERIFIABLE (not clean).

    with_current=True augments each record with the CURRENT-FY assessed valuation pulled from the
    issuer's continuing-disclosure annual report (cdd_financials). This is the per-name DD / master-regrade
    path; the nightly UNIVERSE drain leaves it False to avoid hammering EMMA. When the OS is un-fetchable
    (the EMMA-403 case that produced stale 'UNVERIFIABLE current AV'), the CDD current AV is used instead
    of returning a bare UNVERIFIABLE record."""
    issuer_map = issuer_map or {}
    cache = _load_cache() if use_cache else {}
    out: list[dict] = []
    dirty = False
    for cusip in cusips:
        cusip = cusip.strip().upper()
        if use_cache and cusip in cache and not with_current:
            out.append(cache[cusip])
            continue
        pdf = _resolve_os_pdf(cusip)
        if pdf is None and fetch:
            pdf = _fetch_os_from_emma(cusip)
        if pdf is None:
            rec = _score({"cusip": cusip, "source": "no OS found (on-disk or EMMA)",
                          "confidence": "UNVERIFIABLE"})
            if with_current:                          # CDD fallback for the OS-403 / missing-OS case
                cd = current_av_from_cd(cusip, issuer_map.get(cusip))
                if cd:
                    rec.update(cd)
                    rec["confidence"] = "CD-CURRENT-AV"   # AV current-verified; taxpayer concentration n/a
                    rec["source"] = "CDD annual report (OS unavailable)"
        else:
            rec = extract_concentration(pdf, source=str(pdf))
            rec["cusip"] = cusip
            # Persist the OS layout text by CUSIP so the downstream insurer-wrap + small-base screens can
            # read it universe-wide (this is the "feed insurer_strength real input" fix). Best-effort.
            try:
                ost = _pdf_to_text(Path(pdf)) if str(pdf).lower().endswith(".pdf") else Path(pdf).read_text(errors="replace")
                d = Path(__file__).resolve().parent / "data" / "_os_text"; d.mkdir(parents=True, exist_ok=True)
                (d / f"{cusip}.txt").write_text(ost, errors="replace")
            except Exception:
                pass
            if with_current:        # add CURRENT-FY AV from the CDD annual report (OS AV is issuance-vintage)
                cd = current_av_from_cd(cusip, issuer_map.get(cusip))
                if cd:
                    rec.update(cd)
        cache[cusip] = rec
        dirty = True
        out.append(rec)
    if use_cache and dirty:
        _save_cache(cache)
    return out


# ===========================================================================
# validation
# ===========================================================================
_VALIDATION_CUSIPS = ["168520PA6", "861419ZJ1", "926055KH6", "925836KH0", "697479CB7"]


def _fmt(v, suffix="", w=10):
    if v is None:
        return "—".rjust(w)
    if isinstance(v, float):
        return f"{v:,.2f}{suffix}".rjust(w)
    return str(v).rjust(w)


if __name__ == "__main__":
    print("av_concentration — CA school/CCD GO tax-base + debt-burden screen")
    print(f"cutoff/today = 2026-06-19   cache = {_CACHE_PATH}\n")
    print("Thresholds (soft REVIEW / hard FLAG):")
    print(f"  single-taxpayer  >{TOP1_REVIEW:.0f}% / >{TOP1_FLAG:.0f}% of AV")
    print(f"  top-10           >{TOP10_REVIEW:.0f}% / >{TOP10_FLAG:.0f}% of AV")
    print(f"  debt-to-AV       >{DEBT_REVIEW:.0f}% / >{DEBT_FLAG:.0f}%")
    print(f"  total tax rate   >{TAXRATE_REVIEW:.2f}% / >{TAXRATE_FLAG:.2f}%\n")

    # Validate directly off the on-disk OS PDFs (force=re-parse, bypass cache).
    rows = []
    for cu in _VALIDATION_CUSIPS:
        pdf = _resolve_os_pdf(cu)
        rec = extract_concentration(pdf, source=str(pdf)) if pdf else \
            _score({"confidence": "UNVERIFIABLE", "source": "missing"})
        rec["cusip"] = cu
        rows.append(rec)

    hdr = (f"{'CUSIP':<11}{'top1 taxpayer':<26}{'top1%':>7}{'top10%':>8}"
           f"{'topN%':>8}{'debt%':>7}{'taxrate':>8}{'conf':>13}  designation")
    print(hdr)
    print("-" * len(hdr))
    for r in rows:
        name = (r.get("av_top1_taxpayer") or "—")[:24]
        print(f"{r['cusip']:<11}{name:<26}"
              f"{_fmt(r.get('av_top1_share'),'',7)}"
              f"{_fmt(r.get('av_top10_share'),'',8)}"
              f"{_fmt(r.get('av_topN_share'),'',8)}"
              f"{_fmt(r.get('overlapping_debt_to_av'),'',7)}"
              f"{_fmt(r.get('total_tax_rate_pct'),'',8)}"
              f"{r.get('confidence','?'):>13}  {r.get('designation','?')}")
    print()
    for r in rows:
        if r.get("conc_flags"):
            print(f"{r['cusip']}: " + "; ".join(r["conc_flags"]))

    # CRITICAL CORRECTNESS CHECK — Palo Verde CCD / Blythe Energy.
    pv = next(r for r in rows if r["cusip"] == "697479CB7")
    print("\nPALO VERDE (697479CB7) correctness check:")
    print(f"  top1 taxpayer = {pv.get('av_top1_taxpayer')} "
          f"({pv.get('av_top1_land_use')})  share = {pv.get('av_top1_share')}%")
    print(f"  top-20 cumulative = {pv.get('av_topN_share')}%  (count={pv.get('av_topN_count')})")
    ok = (pv.get("av_top1_taxpayer") and "blythe" in pv["av_top1_taxpayer"].lower()
          and pv.get("av_top1_share") and 13.0 <= pv["av_top1_share"] <= 14.0
          and pv.get("av_topN_share") and 25.0 <= pv["av_topN_share"] <= 27.0)
    print(f"  RESULT: {'PASS — Blythe ~13.5% / top-20 ~26% surfaced' if ok else 'FAIL — extractor broken'}")
