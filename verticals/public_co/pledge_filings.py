"""Dense insider-pledge timeline from SEC Form 4 footnotes and Schedule 13D/13G.

WHY THIS EXISTS
---------------
`pledge_margin_call.triangulate()` anchors a margin-call band to the share price
at pledge INCEPTION. With only the two proxy snapshots (the S-1/424B4 at IPO and
the next DEF 14A) the inception window can span ~9 months, so the price anchor —
and therefore the whole call band — is uselessly wide. This module mines the
filings that sit BETWEEN those two proxies to shrink the window:

  * Form 4 footnotes. A pledge is not itself a reportable §16 transaction, but
    every Form 4 the insider files for ANY other reason (grant, code-S sale,
    code-F tax withholding, code-P buy) re-states current holdings, and the
    beneficial-ownership footnotes routinely carry "<N> shares pledged as
    collateral" as of that filing's date. Stringing these together turns one
    9-month gap into a ladder of dated snapshots, so each top-up tranche is
    bracketed to the window between two consecutive Form 4s — often days, not
    months. A footnote that mentions a pledge WITHOUT a parseable count is still
    a hard lower bound on the inception date (the lien already existed by then).

  * Schedule 13D/13G Item 6. A >5% holder must disclose pledge / collateral
    arrangements in Item 6, and amendments are due within 2 business days of a
    material change (post-2024 rules). A 13D/A that first carries pledge language
    brackets the arrangement to ~2 days. The share count is rarely in the prose,
    but the amendment FILING DATE is a hard bound.

Both feed straight into `pledge_margin_call.triangulate()` as extra, tighter
pledge_observations. This library only READS public EDGAR — no paid access.
"""
from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from typing import Any, Optional

from .edgar import fetch_filing_clean, fetch_form4_xml, list_filings

# --- pledge language ---------------------------------------------------------
# A footnote describes ACTUAL holdings, so we don't need the heavy anti-policy
# machinery the proxy classifier needs — but we still guard against negation
# ("has not pledged", "none ... pledged") so a denial isn't read as a pledge.
_PLEDGE = re.compile(r"pledg", re.I)
_NEG = re.compile(
    r"\bno(?:ne)?\b[^.]{0,40}?pledg|ha(?:s|ve)\s+not\s+pledg|"
    r"not\s+(?:been\s+)?pledged|did\s+not\s+pledg|no\s+shares?\s+(?:are\s+)?pledg",
    re.I,
)
# Share-count extractors around a pledge mention (tolerant of "of such"/"common"/
# "Class A" filler on either side of the number).
_SHARES_BEFORE = re.compile(
    r"([\d,]{3,})\s+(?:of\s+(?:such|these|his|her|the)\s+)?"
    r"(?:outstanding\s+|common\s+|class\s+[a-z]\s+|shares?\s+of\s+)*shares?"
    r"[^.]{0,70}?pledg",
    re.I,
)
_SHARES_AFTER = re.compile(
    r"pledg[^.]{0,80}?([\d,]{3,})\s+(?:of\s+(?:such|these|the)\s+)?(?:common\s+|class\s+[a-z]\s+)*shares?",
    re.I,
)
_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")
_NBSP = re.compile(r"&#160;|&nbsp;|&#xa0;", re.I)


def _localname(tag: str) -> str:
    return tag.split("}")[-1]


def _strip_html(html: str) -> str:
    t = _NBSP.sub(" ", html)
    t = _TAG.sub(" ", t)
    return _WS.sub(" ", t)


def _pledged_count(text: str) -> Optional[int]:
    """First parseable share count adjacent to a pledge mention, else None."""
    for rx in (_SHARES_BEFORE, _SHARES_AFTER):
        m = rx.search(text)
        if m:
            try:
                return int(m.group(1).replace(",", ""))
            except ValueError:
                continue
    return None


def _parse_form4(xml_text: str) -> dict[str, Any]:
    """Extract owner name, period-of-report date, and footnote texts from a
    Form 4 XML. Namespace-agnostic (Form 4 XML is usually un-namespaced, but we
    match on local tag names to be safe)."""
    root = ET.fromstring(xml_text)
    owner = period = ""
    footnotes: list[str] = []
    for el in root.iter():
        ln = _localname(el.tag)
        if ln == "rptOwnerName" and not owner:
            owner = (el.text or "").strip()
        elif ln == "periodOfReport" and not period:
            period = (el.text or "").strip()
        elif ln == "footnote":
            footnotes.append(_WS.sub(" ", "".join(el.itertext())).strip())
    return {"owner": owner, "period": period, "footnotes": footnotes}


def form4_pledge_observations(
    cik: str,
    insider_name: Optional[str] = None,
    since: Optional[str] = None,
    until: Optional[str] = None,
    verbose: bool = False,
) -> list[dict[str, Any]]:
    """Dated pledged-share snapshots mined from an issuer's Form 4 footnotes.

    Args:
      cik: issuer CIK (Form 4s are filed under the issuer too).
      insider_name: substring filter on the reporting owner (e.g. "Halbert").
                    None = every insider.
      since: YYYY-MM-DD lower bound on filing_date.
      until: YYYY-MM-DD upper bound on filing_date — the point-in-time cutoff that
             keeps post-cutoff Form 4s out of a backtest.

    Returns ascending-by-date list of:
      {"date":            "YYYY-MM-DD",   # period-of-report (transaction date)
       "filing_date":     "YYYY-MM-DD",
       "pledged_shares":  int | None,     # cumulative pledged count if parseable
       "pledge_mentioned": bool,          # footnote referenced a pledge at all
       "owner":           "<name>",
       "source":          "Form 4 footnote (<owner>)",
       "evidence":        "<footnote excerpt>"}
    Rows with neither a count nor a mention are dropped.
    """
    _, rows = list_filings(cik)
    f4 = [r for r in rows if r["form"] in ("4", "4/A")]
    if since:
        f4 = [r for r in f4 if r["filing_date"] >= since]
    if until:
        f4 = [r for r in f4 if r["filing_date"] <= until]
    f4.sort(key=lambda r: r["filing_date"])
    out: list[dict[str, Any]] = []
    for r in f4:
        xml = fetch_form4_xml(cik, r["accession"], r["primary_document"])
        if not xml:
            continue
        try:
            p = _parse_form4(xml)
        except ET.ParseError:
            continue
        if insider_name and insider_name.lower() not in p["owner"].lower():
            continue
        pledge_fns = [fn for fn in p["footnotes"]
                      if _PLEDGE.search(fn) and not _NEG.search(fn)]
        if not pledge_fns:
            continue
        evidence = max(pledge_fns, key=len)
        count = None
        for fn in pledge_fns:
            count = _pledged_count(fn)
            if count is not None:
                evidence = fn
                break
        d = p["period"] or r["filing_date"]
        out.append({
            "date": d,
            "filing_date": r["filing_date"],
            "pledged_shares": count,
            "pledge_mentioned": True,
            "owner": p["owner"],
            "source": f"Form 4 footnote ({p['owner']})",
            "evidence": evidence[:240],
        })
        if verbose:
            cs = f"{count:,}" if count else "MENTION (no count)"
            print(f"  F4 {d}  {p['owner']:28.28}  pledged={cs}", file=sys.stderr)
    out.sort(key=lambda o: o["date"])
    return out


def schedule_13_pledge_check(
    cik: str,
    insider_name: Optional[str] = None,
    since: Optional[str] = None,
    until: Optional[str] = None,
    verbose: bool = False,
) -> list[dict[str, Any]]:
    """Scan an issuer's Schedule 13D/13G (and amendments) for Item 6 pledge
    language. Each hit's FILING DATE is a hard date bound on the arrangement.
    `until` is the point-in-time cutoff (no post-cutoff amendments).

    Returns ascending-by-date list of:
      {"filing_date", "form", "has_pledge_language": bool,
       "pledged_shares": int | None, "evidence": "<excerpt>"}
    Only rows whose body mentions a pledge are returned.
    """
    _, rows = list_filings(cik)
    sc = [r for r in rows
          if "13D" in r["form"].upper() or "13G" in r["form"].upper()]
    if since:
        sc = [r for r in sc if r["filing_date"] >= since]
    if until:
        sc = [r for r in sc if r["filing_date"] <= until]
    sc.sort(key=lambda r: r["filing_date"])
    out: list[dict[str, Any]] = []
    for r in sc:
        html = fetch_filing_clean(cik, r["accession"], r["primary_document"])
        if not html:
            continue
        text = _strip_html(html)
        low = text.lower()
        if insider_name and insider_name.lower() not in low:
            continue
        hit = None
        for m in re.finditer(r"pledg", low):
            a, b = max(0, m.start() - 200), min(len(low), m.end() + 200)
            win = low[a:b]
            if _NEG.search(win):
                continue
            hit = text[a:b]
            break
        if not hit:
            continue
        out.append({
            "filing_date": r["filing_date"],
            "form": r["form"],
            "has_pledge_language": True,
            "pledged_shares": _pledged_count(hit),
            "evidence": _WS.sub(" ", hit).strip()[:240],
        })
        if verbose:
            print(f"  {r['form']:14} {r['filing_date']}  PLEDGE in Item 6",
                  file=sys.stderr)
    return out


def _num(s: Optional[str]) -> Optional[float]:
    if not s:
        return None
    try:
        return float(s.replace(",", "").replace("$", ""))
    except ValueError:
        return None


def _val(el: ET.Element, name: str) -> Optional[str]:
    """Text of the first descendant whose local tag is `name`, preferring its
    nested <value> child (Form 4 wraps most scalars in <value>)."""
    for d in el.iter():
        if _localname(d.tag) == name:
            for c in d.iter():
                if _localname(c.tag) == "value":
                    return (c.text or "").strip()
            return (d.text or "").strip()
    return None


def form4_transaction_events(
    cik: str,
    insider_name: Optional[str] = None,
    since: Optional[str] = None,
    until: Optional[str] = None,
    codes: tuple[str, ...] = ("S", "F", "P"),
    verbose: bool = False,
) -> list[dict[str, Any]]:
    """Non-derivative Form 4 transactions by code. Code S = open-market / private
    SALE — the behavioral backstop for the margin-call band: forced/voluntary
    insider selling near a band crossing is the trigger confirmation the band only
    bounds. (F = tax withholding, P = open-market buy — kept for context, not
    distress.) `until` is the point-in-time cutoff.

    Returns ascending-by-date list of:
      {"date","code","shares","price","acq_disp","owner","filing_date"}.
    """
    _, rows = list_filings(cik)
    f4 = [r for r in rows if r["form"] in ("4", "4/A")]
    if since:
        f4 = [r for r in f4 if r["filing_date"] >= since]
    if until:
        f4 = [r for r in f4 if r["filing_date"] <= until]
    f4.sort(key=lambda r: r["filing_date"])
    out: list[dict[str, Any]] = []
    for r in f4:
        xml = fetch_form4_xml(cik, r["accession"], r["primary_document"])
        if not xml:
            continue
        try:
            root = ET.fromstring(xml)
        except ET.ParseError:
            continue
        owner = ""
        for el in root.iter():
            if _localname(el.tag) == "rptOwnerName":
                owner = (el.text or "").strip()
                break
        if insider_name and insider_name.lower() not in owner.lower():
            continue
        for el in root.iter():
            if _localname(el.tag) != "nonDerivativeTransaction":
                continue
            code = _val(el, "transactionCode")
            if codes and code not in codes:
                continue
            out.append({
                "date": _val(el, "transactionDate"),
                "code": code,
                "shares": _num(_val(el, "transactionShares")),
                "price": _num(_val(el, "transactionPricePerShare")),
                "acq_disp": _val(el, "transactionAcquiredDisposedCode"),
                "owner": owner,
                "filing_date": r["filing_date"],
            })
            if verbose:
                print(f"  TXN {_val(el,'transactionDate')} code={code} "
                      f"sh={_val(el,'transactionShares')} {owner[:24]}", file=sys.stderr)
    out.sort(key=lambda e: e["date"] or "")
    return out


def gather_pledge_observations(
    cik: str,
    insider_name: Optional[str] = None,
    since: Optional[str] = None,
    until: Optional[str] = None,
    verbose: bool = False,
) -> dict[str, Any]:
    """Convenience bundle: the Form 4 ladder, the 13D/13G bounds, and the
    earliest dated pledge evidence across both. `pledge_margin_call` consumes
    `form4_count_observations` directly as extra tranches. `until` is the
    point-in-time cutoff threaded to both miners."""
    f4 = form4_pledge_observations(cik, insider_name, since, until, verbose)
    sc = schedule_13_pledge_check(cik, insider_name, since, until, verbose)
    count_obs = [
        {"date": o["date"], "pledged_shares": o["pledged_shares"],
         "source": o["source"], "exact_date": False}
        for o in f4 if o["pledged_shares"]
    ]
    dated = [o["date"] for o in f4] + [o["filing_date"] for o in sc]
    return {
        "form4_ladder": f4,
        "form4_count_observations": count_obs,
        "schedule_13_bounds": sc,
        "earliest_pledge_evidence_date": min(dated) if dated else None,
    }


if __name__ == "__main__":
    import json
    cik = sys.argv[1] if len(sys.argv) > 1 else "2019410"      # Caris (CAI)
    name = sys.argv[2] if len(sys.argv) > 2 else "Halbert"
    print(json.dumps(gather_pledge_observations(cik, name, verbose=True),
                     indent=2, default=str))
