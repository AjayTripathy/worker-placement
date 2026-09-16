"""cdd_financials — shared CURRENT-state extraction from EMMA continuing-disclosure ANNUAL REPORTS.

The OS (official statement) carries ISSUANCE-VINTAGE assessed valuation / coverage; the issuer's latest
15c2-12 ANNUAL REPORT carries the CURRENT-FY figures. This module fetches that annual report (serial +
throttled — the EMMA 403s that produced "UNVERIFIABLE current AV" were a concurrency artifact, not a real
gap) and parses:
  - parse_cdd_av(text, issuer)  -> current-FY total assessed valuation (California Municipal Statistics
    table format), multi-year series, YoY change. Handles multi-district CDDs (Modesto ELEMENTARY vs HIGH
    -> issuer-title disambiguation), single-year layouts (FY header + separate $ row), keyword-free tables
    (Antioch/Turlock), and a narrative footnote fallback. Future-FY rows (SACS budget schedules) excluded.
  - parse_cdd_dscr(text)        -> current debt-service coverage for REVENUE/water bonds, COMPUTED as
    Net Revenues / Total Debt Service (grabbing a 'coverage'-labelled row misparses badly), with an
    'unaudited / one-time cause' footnote so a transient sub-1.0x reading isn't framed as distress.
  - parse_delinquency / parse_audit_fy.

EXTRACTED from refresh_current_state.py (2026-06-20) so the DETECTORS use it, not just an ad-hoc tool:
av_concentration.py augments its OS-based AV with the current-FY CDD AV (and uses it as a 403-fallback
instead of returning UNVERIFIABLE), and water_revenue_underwrite.py adds current CDD coverage.
Consumers: refresh_current_state.py, av_concentration.py, water_revenue_underwrite.py.
"""
import re, time, subprocess
from pathlib import Path

import emma_scraper as E
import emma_continuing_disclosure as CD

HERE = Path(__file__).resolve().parent
THROTTLE = 4.0

# Annual-report doc descriptions (preference order). These carry the AV / coverage tables.
ANNUAL_DESC = ("annual financial disclosure", "continuing disclosure annual report",
               "annual report", "annual financial information")
AUDITED_DESC = ("audited financial statement", "acfr", "comprehensive annual financial")


# --------------------------------------------------------------------------- CD doc selection
def _anchors(cd_html):
    """[(text, href, posted_date), ...] for every CD document row, newest as listed."""
    out = []
    for a in re.findall(r"(<a[^>]*data-doctype[^>]*>.*?</a>)", cd_html, re.S):
        href_m = re.search(r'href="([^"]+)"', a)
        if not href_m:
            continue
        txt = E._strip_tags(a).strip()
        dm = re.search(r"(?:Posted|dated|as of)\s+([01]?\d/[0-3]?\d/\d{4})", txt)
        out.append((txt, href_m.group(1), dm.group(1) if dm else None))
    return out


def _pick(anchors, kinds):
    """Most-recent doc whose text matches one of `kinds` (sort by parsed posted date desc)."""
    cand = [(t, h, d) for (t, h, d) in anchors if any(k in t.lower() for k in kinds)]
    import datetime
    cand.sort(key=lambda x: CD.to_date(x[2]) or datetime.date(1900, 1, 1), reverse=True)
    return cand[0] if cand else None


# --------------------------------------------------------------------------- AV parsing
_FY = re.compile(r"\b(20[12]\d)\s*[-/]\s*(\d{2,4})\b")        # 2025-26 and 2025-2026
_DOLLAR = re.compile(r"\$?\s?([\d]{1,3}(?:,\d{3})+|\d{7,})")
_AV_FLOOR = 30_000_000        # no real CA district AV is below ~$30M; kills debt-schedule rows
_FY_MAX_START = 2026          # reject future-FY rows (debt-service schedules run out to 2050+)
_AV_HDR = re.compile(r"^\s*(?:[IVXL]+\.|\d+\.)?\s*assessed valuations?\b", re.I)
_DISTRICT_TITLE = re.compile(r"^[A-Z][A-Z0-9 ,.&'\-/]{6,70}"
                             r"(?:DISTRICT|COLLEGE|CITY|COUNTY|AUTHORITY|AGENCY)\b")
_STOP = {"THE", "OF", "AND", "CALIFORNIA", "CA", "SCHOOL", "DISTRICT", "DISTRICTS", "GENERAL",
         "OBLIGATION", "BONDS", "BOND", "COUNTY", "COMMUNITY", "JOINT", "PUBLIC", "FINANCING",
         "AUTHORITY", "NO", "INC", "MUNICIPAL", "STATISTICS"}
_NON_AV_CTX = ("budget", "revenue", "expenditure", "expense", "fund balance", "enrollment",
               "attendance", " ada", "pension", "opeb", "cash flow", "debt service")


def _fy_label(m):
    a, b = m.group(1), m.group(2)
    return int(a), f"{a}-{b[-2:]}"      # normalize 2025-2026 -> 2025-26


def _av_tables(lines):
    """Each 'Assessed Valuations' table tagged with its district-name title (the ALL-CAPS line just above
    the header). Big CDDs may cover MULTIPLE districts (Modesto City ELEMENTARY vs Modesto HIGH) — the
    title lets the caller pick the table matching the bond's issuer. Returns [(title|None, {fy: total})].
    Stateful parse so a single-year layout (FY in a header row, $ values on a separate row) is captured."""
    n = len(lines)
    tables = []
    for i, ln in enumerate(lines):
        s = ln.strip(); low = s.lower()
        if not (_AV_HDR.match(s) and "...." not in s and "largest" not in low
                and "taxpayer" not in low and len(s) < 80):
            continue
        title = None
        for k in range(i - 1, max(i - 5, -1), -1):
            t = lines[k].strip()
            if _DISTRICT_TITLE.match(t):
                title = t; break
        j = i + 1
        end = min(i + 35, n)
        while j < end and "california municipal statistics" not in lines[j].lower() \
                and not _AV_HDR.match(lines[j].strip()):
            j += 1
        tbl = {}; cur_fy = None
        for line in lines[i + 1:j + 1]:
            fym = _FY.search(line)
            big = [int(d.replace(",", "")) for d in _DOLLAR.findall(line)]
            big = [d for d in big if d >= _AV_FLOOR]
            if fym:
                start, fy = _fy_label(fym)
                if start > _FY_MAX_START or start < 2010:
                    continue
                cur_fy = fy
                if len(big) >= 2:
                    tbl[fy] = max(big)
            elif big and cur_fy and len(big) >= 2:
                tbl[cur_fy] = max(big)
        if tbl:
            tables.append((title, tbl))
    return tables


def _av_tables_kwfree(lines):
    """Keyword-FREE AV-table detector for CDDs whose AV table lacks the 'assessed valuation' header
    (Antioch, Turlock). AV row = FY(<=2026) + >=3 dollar columns (Local Secured + Unsecured + Total) with
    Total >= $200M — the >=3-columns + $200M gate separates AV (billions) from SACS general-fund budget
    tables (millions, <=2 large columns, future FYs). Budget/revenue context lines skipped."""
    d = {}
    for line in lines:
        low = line.lower()
        if any(c in low for c in _NON_AV_CTX):
            continue
        fym = _FY.search(line)
        if not fym:
            continue
        start, fy = _fy_label(fym)
        if start > _FY_MAX_START or start < 2010:
            continue
        big = [int(x.replace(",", "")) for x in _DOLLAR.findall(line)]
        big = [x for x in big if x >= _AV_FLOOR]
        if len(big) < 3:
            continue
        if max(big) < 200_000_000:
            continue
        d[fy] = max(big)
    return [(None, d)] if d else []


def _title_match(title, issuer):
    """Score a table title vs the bond issuer. ELEMENTARY/HIGH/UNIFIED level mismatch is disqualifying."""
    if not title or not issuer:
        return 0
    tt = set(re.findall(r"[A-Z]+", title.upper())) - _STOP
    it = set(re.findall(r"[A-Z]+", issuer.upper())) - _STOP
    for lvl in ("ELEMENTARY", "HIGH", "UNIFIED"):
        if (lvl in tt) != (lvl in it) and ({"ELEMENTARY", "HIGH", "UNIFIED"} & it):
            return -1
    return len(tt & it)


def parse_cdd_av(text, issuer=None):
    """Parse the 'Assessed Valuations' table from a CDD annual report. For multi-district CDDs, select the
    sub-table whose title matches `issuer`. Returns {av_current, av_current_fy, av_prior, av_change_pct,
    av_series, av_table_title, av_ambiguous, av_n_tables} or {}."""
    lines = text.splitlines()
    tables = _av_tables(lines)
    if not tables:
        nar = {}                          # narrative fallback: AV stated only as a footnote
        for ln in lines:
            if "assessed valuation" not in ln.lower():
                continue
            fym = _FY.search(ln)
            dm = re.search(r"assessed valuation[:\s]*\$?\s?(\d{1,3}(?:,\d{3}){2,})", ln, re.I)
            if not (fym and dm):
                continue
            start, fy = _fy_label(fym)
            if start > _FY_MAX_START or start < 2010:
                continue
            val = int(dm.group(1).replace(",", ""))
            if val >= _AV_FLOOR:
                nar[fy] = max(val, nar.get(fy, 0))
        if nar:
            tables = [(None, nar)]
        else:
            tables = _av_tables_kwfree(lines)
            if not tables:
                return {}
    chosen = None; ambiguous = False
    if len(tables) == 1:
        chosen = tables[0]
    else:
        scored = sorted(((_title_match(t, issuer), t, tbl) for t, tbl in tables), key=lambda x: -x[0])
        best = scored[0]
        if best[0] > 0:
            chosen = (best[1], best[2])
        else:
            curs = {max(tbl) and tbl[sorted(tbl)[-1]] for _, tbl in tables}
            if len(curs) == 1:
                chosen = tables[0]
            else:
                chosen = max(tables, key=lambda x: max(x[1]))
                ambiguous = True
    title, tbl = chosen
    series2 = sorted(tbl.items(), key=lambda r: r[0])
    cur_fy, cur_av = series2[-1]
    prior_av = series2[-2][1] if len(series2) >= 2 else None
    chg = round((cur_av / prior_av - 1) * 100, 1) if prior_av else None
    return {"av_current": cur_av, "av_current_fy": cur_fy, "av_prior": prior_av,
            "av_change_pct": chg, "av_series": [[fy, t, None] for fy, t in series2],
            "av_table_title": title, "av_ambiguous": ambiguous, "av_n_tables": len(tables)}


# --------------------------------------------------------------------------- DSCR parsing
def _dscr_footnote(text):
    """'unaudited' qualifier + the explanatory footnote for the latest year, so a sub-1.0x reading driven
    by a transient cause (e.g. a billing-system outage) is framed accurately, not as structural distress."""
    out = {}
    if re.search(r"\bunaudited\b", text, re.I):
        out["dscr_unaudited"] = True
    m = re.search(r"\(\d\)\s*(Unaudited\.?\s*)?(The (?:reduction|decrease|decline|increase)[^.]*\."
                  r"(?:[^.]*\.){0,2})", text, re.I)
    if m:
        out["dscr_note"] = re.sub(r"\s+", " ", m.group(2)).strip()[:320]
    return out


def _last_dollars(line, floor=100_000):
    vals = []
    for t in re.findall(r"\(?\-?\$?\s?\d{1,3}(?:,\d{3})+(?:\.\d{2})?\)?", line):
        neg = "(" in t
        v = float(re.sub(r"[^\d.]", "", t))
        if v >= floor:
            vals.append(-v if neg else v)
    return vals


def parse_cdd_dscr(text):
    """REVENUE/water current coverage. COMPUTE Net Revenues / Total Debt Service (grabbing a 'coverage'-
    labelled row misparses — a healthy 1.48x sewer read 0.68x off a rate line). Prefer an explicit clean
    ratio row only when one exists. Returns {dscr_current, dscr_series, dscr_basis, ...} or {} (honest)."""
    lines = text.splitlines()
    for ln in lines:                       # 1) explicit clean ratio row (no $)
        s = ln.strip(); low = s.lower()
        if low.startswith("debt service coverage") and "total" not in low and "$" not in s:
            vals = []
            for t in re.findall(r"\(?\-?\d{1,3}\.\d{1,2}\)?x?", s):
                neg = "(" in t; num = float(re.sub(r"[^\d.]", "", t))
                vals.append(-num if neg else num)
            vals = [v for v in vals if abs(v) < 100]
            if vals:
                out = {"dscr_current": round(vals[-1], 2), "dscr_series": vals,
                       "dscr_basis": "explicit coverage row"}
                out.update(_dscr_footnote(text))
                return out
    net_line = ds_line = None              # 2) compute Net Revenues / Total Debt Service
    for ln in lines:
        s = ln.strip(); low = s.lower()
        if low.startswith("net revenues") and _last_dollars(ln):
            net_line = ln
        if (low.startswith("total debt service") or low.startswith("subtotal")) and _last_dollars(ln):
            ds_line = ln
    if net_line and ds_line:
        nr = _last_dollars(net_line); ds = _last_dollars(ds_line)
        if nr and ds and ds[-1]:
            dscr = round(nr[-1] / ds[-1], 2)
            ser = [round(n / d, 2) for n, d in zip(nr, ds) if d] if len(nr) == len(ds) else [dscr]
            out = {"dscr_current": dscr, "dscr_series": ser,
                   "dscr_basis": "computed Net Revenues / Total Debt Service"}
            out.update(_dscr_footnote(text))
            return out
    return {}


def parse_delinquency(text):
    """Secured-tax delinquency rate (the levy-collection cushion)."""
    m = re.search(r"(?is)delinquen\w*.{0,400}?(\d{1,2}\.\d{1,2})\s*%", text)
    if m:
        v = float(m.group(1))
        if 0 <= v <= 25:
            return v
    return None


def parse_audit_fy(annual_text, audited_text=""):
    for t in (audited_text or "", annual_text or ""):
        m = re.search(r"(?i)(?:year ended|fiscal year ended|FYE)\s+(?:June 30,?\s+)?(20\d{2})", t)
        if m:
            return int(m.group(1))
    return None


# --------------------------------------------------------------------------- fetch + orchestrate
def _dl(url, dest, s):
    E.download_pdf(E.BASE + url if url.startswith("/") else url, dest, s)
    return dest


def _text(pdf):
    try:
        out = Path(pdf).with_suffix(".txt")
        subprocess.run(["pdftotext", "-layout", str(pdf), str(out)], check=True,
                       capture_output=True, timeout=120)
        return out.read_text(errors="replace")
    except Exception:
        return ""


def fetch_latest_annual(s, cusip, raw_dir=None, throttle=THROTTLE):
    """Fetch (serial/throttled) the latest CDD annual-report PDF for a CUSIP -> dict with its text + doc
    metadata. {ann_text, annual_doc, annual_posted, audited_doc, audited_posted, n_cd_docs} or {err}."""
    cd, err = CD.fetch_cd(s, cusip)
    if cd is None:
        return {"err": f"fetch_cd: {err}"}
    anchors = _anchors(cd)
    ann = _pick(anchors, ANNUAL_DESC)
    aud = _pick(anchors, AUDITED_DESC)
    out = {"n_cd_docs": len(anchors)}
    if not ann and not aud:
        out["err"] = "no annual/audited doc in CD record"
        return out
    if ann:
        if throttle:
            time.sleep(throttle)
        raw_dir = Path(raw_dir) if raw_dir else (HERE / "outputs" / "diligence_reports" / cusip / "raw")
        raw_dir.mkdir(parents=True, exist_ok=True)
        p = _dl(ann[1], raw_dir / "cdd_annual_latest.pdf", s)
        out.update(ann_text=_text(p), annual_doc=ann[0], annual_posted=ann[2],
                   annual_pdf=str(p))
    if aud:
        out.update(audited_doc=aud[0], audited_posted=aud[2])
    return out


def current_state(cusip, session=None, issuer=None, raw_dir=None, ann_text=None, throttle=THROTTLE):
    """Top-level current-state extractor. Either pass `ann_text` (already-downloaded annual report) or a
    `session` to fetch live. Returns a dict: av_* (school GO) or dscr_* (revenue), delinquency_pct,
    audit_fy, plus doc metadata. status VERIFIED / PARTIAL / STILL-UNVERIFIABLE. Never fabricates."""
    rec = {"cusip": cusip}
    meta = {}
    if ann_text is None:
        if session is None:
            session = E._session()
        meta = fetch_latest_annual(session, cusip, raw_dir=raw_dir, throttle=throttle)
        if meta.get("err"):
            return {"cusip": cusip, "status": "STILL-UNVERIFIABLE", "reason": meta["err"],
                    **{k: v for k, v in meta.items() if k != "err"}}
        ann_text = meta.get("ann_text", "")
    rec.update({k: meta[k] for k in ("annual_doc", "annual_posted", "audited_doc", "audited_posted",
                                     "n_cd_docs") if k in meta})
    av = parse_cdd_av(ann_text, issuer=issuer)
    rec.update(av)
    rec["delinquency_pct"] = parse_delinquency(ann_text)
    rec["audit_fy"] = parse_audit_fy(ann_text)
    if not av.get("av_current"):
        rec.update(parse_cdd_dscr(ann_text))
    rec["status"] = "VERIFIED" if (rec.get("av_current") or rec.get("dscr_current") is not None) \
        else "PARTIAL"
    return rec
