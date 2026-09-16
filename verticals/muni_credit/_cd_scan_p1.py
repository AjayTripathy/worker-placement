"""Continuing-disclosure / material-event scan for 10 Phase-1 muni CUSIPs.

Pulls EMMA /Security/ContinuingDisclosurePartialView per CUSIP (plaintext CUSIP,
Disclaimer6 cookie required), parses filing rows (group category + posted dates),
and classifies each bond per 15c2-12 event taxonomy.
"""
import emma_scraper as E
import re, json, time, datetime, sys
from pathlib import Path

CUSIPS = ["91412G2F1","926055KH6","91412HJC8","050002AW4","817409H32",
          "900211CP6","171314LB1","012104QQ1","291119KP9","796472AS7"]

TODAY = datetime.date(2026, 6, 11)

# 15c2-12 material-event keywords -> normalized type
EVENT_PATTERNS = [
    ("redemption",   r"\b(advance refund|advance-refund|defeas|optional redemption|notice of redemption|"
                     r"full redemption|partial redemption|mandatory redemption|call notice|redeem)\b"),
    ("rating_change",r"\b(rating change|rating (?:up|down)grade|downgrade|upgrade|rating action|"
                     r"placed on (?:negative|positive) (?:watch|outlook)|outlook (?:revised|change))\b"),
    ("payment_default", r"\b(payment default|principal[/ ]?interest delinquen|payment delinquen|"
                     r"nonpayment|failure to pay|missed payment)\b"),
    ("reserve_draw", r"\b(reserve (?:fund )?(?:draw|deficien|tap)|draw on (?:the )?reserve|"
                     r"debt service reserve)\b"),
    ("financial_difficulty", r"\b(unscheduled draw|credit enhancement|liquidity (?:facility|provider)|"
                     r"bankruptcy|insolvency|receiver|financial difficult|going concern)\b"),
    ("tax_event",    r"\b(adverse tax|taxabilit|determination of taxab|loss of tax)\b"),
    ("late_filing",  r"\b(failure to (?:file|provide)|late filing|notice of failure|"
                     r"failure to submit|non-?compliance)\b"),
    ("financial_obligation", r"\b(financial obligation|incurrence|material (?:terms|modification)|"
                     r"bank loan|direct placement)\b"),
]

ANNUAL_GROUPS = ("Annual Financial Information", "Audited Financial Statements", "ACFR",
                 "Financial/Operating")

def classify_doc(group, desc):
    blob = (group + " || " + desc).lower()
    hits = []
    for typ, pat in EVENT_PATTERNS:
        if re.search(pat, blob):
            hits.append(typ)
    return hits

def parse_cd_html(cd):
    """Return list of dicts: {section, group, desc, period_date, posted_date}."""
    rows = []
    cur_section = None
    cur_group = None
    # walk the table top-to-bottom by splitting on <tr ...>
    parts = re.split(r"(<tr[^>]*>)", cd)
    # reconstruct: pair tag with following block
    i = 0
    blocks = []
    for idx in range(1, len(parts), 2):
        tag = parts[idx]
        body = parts[idx+1] if idx+1 < len(parts) else ""
        blocks.append((tag, body))
    for tag, body in blocks:
        # NEW SECTION header (<th colspan="4">...</th>) -> reset group so an
        # event-section group ("Rating Change") can't leak onto financial rows.
        sec_m = re.search(r'<th colspan="4"[^>]*>(.*?)</th>', body, re.S)
        if sec_m:
            cur_section = E._strip_tags(sec_m.group(1)).strip()
            cur_group = None
            continue
        if 'class="groupRow"' in tag:
            m = re.search(r"<th>(.*?)</th>", body, re.S)
            if m:
                cur_group = E._strip_tags(m.group(1)).strip()
            continue
        # data row?
        dm = re.search(r'data-doctype="[^"]*"[^>]*>(.*?)</a>', body, re.S)
        if not dm:
            continue
        desc = E._strip_tags(dm.group(1)).strip()
        # date cells: <td class="text-center">MM/DD/YYYY</td> (period then posted)
        dates = re.findall(r'<td class="text-center">\s*([01]?\d/[0-3]?\d/\d{4})\s*</td>', body)
        period_date = dates[0] if len(dates) >= 1 else None
        posted_date = dates[1] if len(dates) >= 2 else (dates[0] if dates else None)
        # "Most Recent" sub-block rows carry no date cells; recover from the
        # description text ("Posted MM/DD/YYYY" or "dated MM/DD/YYYY").
        if posted_date is None:
            dm2 = re.search(r'(?:Posted|dated)\s+([01]?\d/[0-3]?\d/\d{4})', desc)
            if dm2:
                posted_date = dm2.group(1)
        # In the Financial/Operating section the group never carries an event
        # type; null it so classify_doc keys purely off the description there.
        grp = cur_group
        if cur_section and "financial/operating" in cur_section.lower():
            grp = cur_group  # financial groups (Annual/Audited/ACFR) are not event types
        rows.append({"section": cur_section, "group": grp, "desc": desc,
                     "period_date": period_date, "posted_date": posted_date})
    # section tagging: find which section each group falls under
    # split html by the two section headers and tag groups by offset
    sec_iter = list(re.finditer(r'<th colspan="4"[^>]*>(.*?)</th>', cd, re.S))
    return rows, [E._strip_tags(s.group(1)).strip() for s in sec_iter]

def to_date(mdy):
    if not mdy:
        return None
    try:
        m, d, y = mdy.split("/")
        return datetime.date(int(y), int(m), int(d))
    except Exception:
        return None

def fetch_cd(s, cusip, retries=1):
    det = E.BASE + "/Security/Details/" + cusip
    for attempt in range(retries + 1):
        try:
            html = s.get(det, headers={"Referer": E.BASE + "/",
                         "Upgrade-Insecure-Requests": "1"}, timeout=45).text
            if "yesButton" in html:  # accept disclaimer for this obligor
                data = {"__VIEWSTATE": E._hidden("__VIEWSTATE", html),
                        "__VIEWSTATEGENERATOR": E._hidden("__VIEWSTATEGENERATOR", html),
                        "__EVENTVALIDATION": E._hidden("__EVENTVALIDATION", html),
                        "ctl00$mainContentArea$disclaimerContent$yesButton": "Accept"}
                s.post(E.BASE + "/Disclaimer.aspx", data=data,
                       headers={"Content-Type": "application/x-www-form-urlencoded",
                                "Origin": E.BASE, "Referer": det}, timeout=45)
                html = s.get(det, headers={"Referer": E.BASE + "/"}, timeout=45).text
            if "yesButton" in html:
                # disclaimer still not accepted
                if attempt < retries:
                    time.sleep(1); continue
                return None, "disclaimer_not_accepted"
            cd = s.post(E.BASE + "/Security/ContinuingDisclosurePartialView",
                        data={"SecurityId": cusip, "SelectedPredefinedDateRange": "All"},
                        headers={"Referer": det, "X-Requested-With": "XMLHttpRequest",
                                 "Origin": E.BASE}, timeout=45).text
            if "continuingDisclosureContainer" not in cd:
                if attempt < retries:
                    time.sleep(1); continue
                return None, "no_cd_container"
            return cd, None
        except Exception as ex:
            if attempt < retries:
                time.sleep(1); continue
            return None, f"exception:{type(ex).__name__}:{ex}"
    return None, "unknown"


def scan_one(s, cusip):
    cd, err = fetch_cd(s, cusip)
    if cd is None:
        return {"cusip": cusip, "status": "UNREADABLE", "last_annual_filing_date": None,
                "event_notices": [], "basis": f"endpoint failed: {err}"}
    rows, sections = parse_cd_html(cd)
    # CDA contractual due-date note (header)
    cda = re.search(r"annual financial information is contractually due to be submitted on ([^.<]+)", cd)
    cda_due = cda.group(1).strip() if cda else None

    # annual filings: group mentions Annual Financial Information / Audited / ACFR
    annual_dates = []
    event_notices = []
    redemption_hits = []
    for r in rows:
        grp = r["group"] or ""
        posted = to_date(r["posted_date"]) or to_date(r["period_date"])
        is_annual = any(k.lower() in grp.lower() for k in
                        ("Annual Financial Information", "Audited Financial Statements",
                         "ACFR")) or "annual financial" in r["desc"].lower() \
                        or "annual financial report" in r["desc"].lower() \
                        or "annual report" in r["desc"].lower()
        if is_annual and posted:
            annual_dates.append((posted, r["desc"]))
        hits = classify_doc(grp, r["desc"])
        # Drop "financial_obligation" alone from event_notices noise unless material modification;
        # keep it but flag. Drop generic annual/CP-memo from events.
        material = [h for h in hits if h in ("redemption","rating_change","payment_default",
                                             "reserve_draw","financial_difficulty","tax_event","late_filing")]
        for h in material:
            note = r["desc"][:160]
            event_notices.append({"date": r["posted_date"] or r["period_date"],
                                  "type": h, "note": note})
            if h == "redemption":
                redemption_hits.append((posted, r["desc"]))
    annual_dates.sort(reverse=True)
    last_annual = annual_dates[0][0].isoformat() if annual_dates else None
    last_annual_desc = annual_dates[0][1] if annual_dates else None

    # recurring-late-audit tell: >=2 "Failure to Provide/File" notices
    late_filing_events = [e for e in event_notices if e["type"] == "late_filing"]
    chronic_late = len(late_filing_events) >= 2

    # classify
    status = "CLEAN"
    basis_parts = []
    # REDEMPTION-RISK takes precedence
    if redemption_hits:
        status = "REDEMPTION-RISK"
        basis_parts.append("defeasance/redemption/refunding notice present")
    else:
        # event notices in last 3 years?
        recent_events = [e for e in event_notices
                         if to_date(e["date"]) and (TODAY - to_date(e["date"])).days <= 365*3]
        # stale filer?
        stale = False
        if last_annual:
            age_days = (TODAY - annual_dates[0][0]).days
            if age_days > 548:  # 18 months
                stale = True
        else:
            stale = True  # no annual filing found at all
        if stale:
            status = "STALE-FILER"
            if last_annual:
                basis_parts.append(f"last annual filing {last_annual} > 18mo old")
            else:
                basis_parts.append("no annual financial filing found in CD record")
        elif recent_events:
            status = "NOTICE"
            kinds = sorted(set(e["type"] for e in recent_events))
            basis_parts.append("15c2-12 event notice(s) in last 3y: " + ", ".join(kinds))
        else:
            status = "CLEAN"
            basis_parts.append("only routine annual/operating filings; reasonably current")

    if chronic_late:
        ld = sorted([e["date"] for e in late_filing_events if e["date"]])
        basis_parts.append(f"CHRONIC LATE FILER: {len(late_filing_events)} failure-to-file "
                           f"notices ({', '.join(ld)}) — audit currency lags operating-data currency")
    if last_annual:
        basis_parts.append(f"most recent annual: {last_annual} ({last_annual_desc[:60] if last_annual_desc else ''})")
    if cda_due:
        basis_parts.append(f"CDA annual due: {cda_due}")
    basis_parts.append(f"sections={sections}; total_filings={len(rows)}")

    return {"cusip": cusip, "status": status, "last_annual_filing_date": last_annual,
            "event_notices": event_notices, "basis": " | ".join(basis_parts)}


def main():
    s = E._session()
    out = []
    for cusip in CUSIPS:
        time.sleep(1)
        res = scan_one(s, cusip)
        out.append(res)
        print(f"[{cusip}] {res['status']} :: annual={res['last_annual_filing_date']} "
              f":: events={len(res['event_notices'])}", file=sys.stderr)
    p = Path("/Users/ajay/exalted/signalos/verticals/muni_credit/outputs/buylist_dd/cd_scan_p1.json")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, indent=2))
    print("WROTE", p, file=sys.stderr)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
