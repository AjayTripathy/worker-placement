"""Programmatic EMMA (emma.msrb.org) scraper for muni issue data.

WHY THIS EXISTS
---------------
EMMA has no public API and its UI is the only free access path. The site is an
ASP.NET-MVC app behind an AWS ALB; the security/CUSIP tables sit behind a CGS/ABA
CUSIP-license click-through (an ASP.NET WebForms postback to Disclaimer.aspx that
sets a `Disclaimer6` cookie). This module reproduces a browser session end-to-end:

    obligor name
      -> SearchAhead/SearchDesc          (name -> issues; conduit obligors live in
                                           the issue DESCRIPTION, not the issuer name,
                                           so we use the description search)
      -> IssueView/Details/<IssueId>     (renders the disclaimer)
      -> Disclaimer.aspx  (POST accept)  (sets the Disclaimer6 cookie)
      -> GetFinalScaleData/<IssueId>     (maturity scale JSON: principal, coupon,
                                           maturity date, offering price/yield)
      -> OfficialStatementPartialView    (OS PDF link)
      -> ContinuingDisclosurePartialView (audit / financial PDFs)

CUSIP CAVEAT
------------
The scale JSON returns the plaintext CUSIP only as an ENCRYPTED token (`Cusip9Enc`)
— EMMA obfuscates it for CGS licensing. Everything else (par, coupon, maturity date,
initial offering price/yield) is plaintext. For plaintext 9-char CUSIPs, parse the
Official Statement PDF (which is also where the security/lien covenant language lives,
the stuff no structured database carries). See `download_pdf` + use pdftotext.

POLITENESS
----------
Full Chrome fingerprint (per scraping-fingerprint playbook), one session reused across
requests, THROTTLE_S spacing between hits. EMMA data is public municipal disclosure;
this is research use. Respect the site — do not parallelize aggressively.
"""
from __future__ import annotations

import html
import json
import re
import time
import warnings
from pathlib import Path
from typing import Optional

warnings.filterwarnings("ignore")
import requests

BASE = "https://emma.msrb.org"
THROTTLE_S = 0.5
_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
_HEADERS = {
    "User-Agent": _UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Sec-Ch-Ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"macOS"',
    "Upgrade-Insecure-Requests": "1",
}
_CACHE = Path(__file__).parent / "data" / "_emma_cache"


def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update(_HEADERS)
    s.get(BASE + "/", timeout=40)   # seed AWS ALB cookies
    return s


def _strip_tags(s: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", s or "")).strip()


def search_issues(term: str, session: Optional[requests.Session] = None) -> list[dict]:
    """Resolve an obligor/issuer name to EMMA issues via the description search.

    Returns dicts: {issuer, issue_desc, issue_id, issue_url}. Conduit obligors
    (e.g. 'Aldersly' issued through CMFA) only match on issue description, which is
    what `cat=desc` searches — issuer-name search alone would miss them.
    """
    s = session or _session()
    time.sleep(THROTTLE_S)
    r = s.get(f"{BASE}/QuickSearch/Results",
              params={"quickSearchText": term, "cat": "desc"},
              headers={"Referer": BASE + "/"}, timeout=40)
    # Results are embedded inline as a JSON array of issue records.
    recs = re.findall(
        r'"IssuerName":"(?P<issuer>[^"]*)"[^{]*?'
        r'"IssueDesc":"(?P<desc>[^"]*)","IssueId":"(?P<id>[^"]*)",'
        r'"IssueUrl":"(?P<url>[^"]*)"', r.text)
    out = []
    for issuer, desc, iid, url in recs:
        out.append({"issuer": _strip_tags(issuer), "issue_desc": _strip_tags(desc),
                    "issue_id": iid, "issue_url": html.unescape(url)})
    # de-dupe on issue_id, preserve order
    seen, uniq = set(), []
    for r_ in out:
        if r_["issue_id"] not in seen:
            seen.add(r_["issue_id"]); uniq.append(r_)
    return uniq


def _hidden(name: str, html_txt: str) -> str:
    m = re.search(r'id="%s"[^>]*value="([^"]*)"' % re.escape(name), html_txt)
    return m.group(1) if m else ""


def accept_disclaimer(session: requests.Session, issue_id: str) -> bool:
    """Render the issue detail page and POST the CUSIP-license acceptance so the
    securities endpoints return data. Sets the Disclaimer6 cookie on the session."""
    detail = f"{BASE}/IssueView/Details/{issue_id}"
    time.sleep(THROTTLE_S)
    html_txt = session.get(detail, timeout=40).text
    if "yesButton" not in html_txt:        # already accepted this session
        return True
    session.post(f"{BASE}/Disclaimer.aspx",
                 data={"__VIEWSTATE": _hidden("__VIEWSTATE", html_txt),
                       "__VIEWSTATEGENERATOR": _hidden("__VIEWSTATEGENERATOR", html_txt),
                       "__EVENTVALIDATION": _hidden("__EVENTVALIDATION", html_txt),
                       "ctl00$mainContentArea$disclaimerContent$yesButton": "Accept"},
                 headers={"Content-Type": "application/x-www-form-urlencoded",
                          "Origin": BASE, "Referer": detail}, timeout=40)
    return any(c.name == "Disclaimer6" for c in session.cookies)


def _ajax_headers(issue_id: str) -> dict:
    return {"X-Requested-With": "XMLHttpRequest", "Accept": "text/html, */*; q=0.01",
            "Referer": f"{BASE}/IssueView/Details/{issue_id}"}


def get_scale(issue_id: str, session: requests.Session) -> list[dict]:
    """Maturity scale for an issue: par / coupon / maturity date / offering
    price+yield per maturity. CUSIP is the encrypted token only (see module docstring)."""
    time.sleep(THROTTLE_S)
    r = session.get(f"{BASE}/IssueView/GetFinalScaleData/{issue_id}",
                    headers=_ajax_headers(issue_id), timeout=40)
    try:
        rows = json.loads(r.text)
    except json.JSONDecodeError:
        return []
    out = []
    for d in rows:
        out.append({
            "security_desc": d.get("SecurityDescription"),
            "principal": d.get("MatPrinTxt"),
            "coupon": d.get("IntRateTxt"),
            "maturity_date": d.get("MatDtTxt"),
            "offering_price": d.get("IOPTxt"),
            "offering_yield": d.get("NiidsIOYTxt"),
            "cusip9_enc": d.get("Cusip9Enc"),   # encrypted; resolve via OS PDF
        })
    return out


def _partial_pdf_links(issue_id: str, partial: str, session: requests.Session) -> list[str]:
    time.sleep(THROTTLE_S)
    r = session.get(f"{BASE}/IssueView/{partial}", params={"issueId": issue_id},
                    headers=_ajax_headers(issue_id), timeout=40)
    # EMMA document filenames are prefixed by the issue's letter code (P, EP, ER, ES, SS, ...),
    # not always "P" — match any 1-2 letter prefix per segment.
    links = re.findall(r'href="(/[A-Z]{1,2}\d+-[A-Z]{1,2}\d+-[A-Z]{1,2}\d+\.pdf)"', r.text)
    return [BASE + l for l in dict.fromkeys(links)]


def get_official_statement(issue_id: str, session: requests.Session) -> Optional[str]:
    links = _partial_pdf_links(issue_id, "OfficialStatementPartialView", session)
    return links[0] if links else None


def get_continuing_disclosures(issue_id: str, session: requests.Session) -> list[str]:
    return _partial_pdf_links(issue_id, "ContinuingDisclosurePartialView", session)


# RTRS trade-type codes (MSRB Real-time Transaction Reporting System).
_TRADE_TYPE = {"P": "purchase_from_customer", "S": "sale_to_customer",
               "D": "inter_dealer"}


def get_trades(cusip: str, session: requests.Session) -> list[dict]:
    """Per-CUSIP RTRS trade history. Plaintext (NOT the encrypted scale token).

    The /Security/Details/<cusip> page embeds the full reported trade tape
    server-side as `var tradeData = {...}` — it does NOT come from the scale JSON
    and only renders once the Disclaimer6 cookie is set (call accept_disclaimer
    on any issue of the obligor first). Fields: TD trade date, PX dollar price,
    YX yield %, TA par traded, TT trade type (P/S/D). Rows are newest-first.
    """
    time.sleep(THROTTLE_S)
    r = session.get(f"{BASE}/Security/Details/{cusip}",
                    headers={"Referer": BASE + "/", "Upgrade-Insecure-Requests": "1"},
                    timeout=40)
    m = re.search(r"var tradeData = (\{.*?\});", r.text, re.S)
    if not m:
        return []
    try:
        rows = json.loads(m.group(1)).get("data", [])
    except json.JSONDecodeError:
        return []
    out = []
    for d in rows:
        out.append({
            "trade_date": (d.get("TD") or "")[:10],
            "price": d.get("PX"),
            "yield_pct": d.get("YX"),
            "par_traded": d.get("TA"),
            "trade_type": _TRADE_TYPE.get(d.get("TT"), d.get("TT")),
            "settlement": (d.get("STL") or "")[:10],
        })
    return out


def download_pdf(url: str, dest: Path, session: requests.Session) -> Path:
    time.sleep(THROTTLE_S)
    r = session.get(url, headers={"Referer": f"{BASE}/"}, timeout=90)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(r.content)
    return dest


def collect_issue(issue_id: str, session: requests.Session,
                  with_os: bool = True, with_cd: bool = False) -> dict:
    """Full pull for one issue: scale + OS link (+ optional continuing-disclosure links)."""
    accept_disclaimer(session, issue_id)
    rec = {"issue_id": issue_id, "scale": get_scale(issue_id, session)}
    if with_os:
        rec["official_statement_pdf"] = get_official_statement(issue_id, session)
    if with_cd:
        rec["continuing_disclosure_pdfs"] = get_continuing_disclosures(issue_id, session)
    return rec


def collect_obligor(term: str, desc_filter: Optional[str] = None,
                    save: bool = True) -> dict:
    """Search an obligor name, pull scale + OS for every matching issue.

    `desc_filter` (case-insensitive substring) narrows the description matches to the
    intended obligor — important because a description search can pull near-name hits.
    """
    s = _session()
    issues = search_issues(term, s)
    if desc_filter:
        issues = [i for i in issues if desc_filter.lower() in i["issue_desc"].lower()]
    for i in issues:
        i.update(collect_issue(i["issue_id"], s))
    result = {"term": term, "desc_filter": desc_filter, "n_issues": len(issues),
              "issues": issues}
    if save:
        _CACHE.mkdir(parents=True, exist_ok=True)
        safe = re.sub(r"[^A-Za-z0-9]+", "_", term).strip("_").lower()
        (_CACHE / f"{safe}.json").write_text(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    import sys
    term = sys.argv[1] if len(sys.argv) > 1 else "Aldersly"
    filt = sys.argv[2] if len(sys.argv) > 2 else None
    res = collect_obligor(term, filt)
    print(json.dumps({"term": res["term"], "n_issues": res["n_issues"],
                      "issues": [{"desc": i["issue_desc"], "id": i["issue_id"],
                                  "n_maturities": len(i.get("scale", [])),
                                  "os_pdf": i.get("official_statement_pdf")}
                                 for i in res["issues"]]}, indent=2))
