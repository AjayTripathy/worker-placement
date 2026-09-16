"""Resolve obligor + sector for a list of CUSIPs via EMMA Security/Details.

Pulls the Security/Details/<cusip> page (accepting the CGS disclaimer once per session)
and extracts: issuer, issue description (where conduit OBLIGOR lives), state, dated/
maturity/coupon, tax status, and the Official Statement link. Writes JSON for grading.
"""
import json, re, sys, time, html as _html
from pathlib import Path
import emma_continuing_disclosure as ECD
import emma_scraper as E

HERE = Path(__file__).resolve().parent
OUT = HERE / "outputs" / "gauntlet_resolution.json"

CUSIPS = [
    "036680BZ8","940204EB2","940204GR5",
    "130923BH7","13069AAT5","13069ABC1",
    "87972DBL5",
    "89356CBL9","89356CBM7","79770GET9","79770GES1","79770GCB0","79770GER3",
    "786129DD5","67232TBQ7","13063DZB7","13078RHE3","655505BT1","76913AKY8",
    "13032UMG0","13032UPV4","13032UNW4","03255LHR3","568061CW3",
]

def _strip(s): return _html.unescape(re.sub(r"<[^>]+>"," ",s or "")).strip()

def detail_html(s, cusip, retries=2):
    det = E.BASE + "/Security/Details/" + cusip
    for attempt in range(retries+1):
        try:
            h = s.get(det, headers={"Referer": E.BASE+"/","Upgrade-Insecure-Requests":"1"}, timeout=45).text
            if "yesButton" in h:
                data = {"__VIEWSTATE": E._hidden("__VIEWSTATE", h),
                        "__VIEWSTATEGENERATOR": E._hidden("__VIEWSTATEGENERATOR", h),
                        "__EVENTVALIDATION": E._hidden("__EVENTVALIDATION", h),
                        "ctl00$mainContentArea$disclaimerContent$yesButton":"Accept"}
                s.post(E.BASE+"/Disclaimer.aspx", data=data,
                       headers={"Content-Type":"application/x-www-form-urlencoded","Origin":E.BASE,"Referer":det}, timeout=45)
                h = s.get(det, headers={"Referer":E.BASE+"/"}, timeout=45).text
            if "yesButton" in h:
                time.sleep(1.5); continue
            return h, None
        except Exception as ex:
            if attempt < retries: time.sleep(1.5); continue
            return None, f"{type(ex).__name__}:{ex}"
    return None, "disclaimer"

def extract(cusip, h):
    out = {"cusip": cusip}
    # The details page has labeled fields. Grab common ones via regex around known labels.
    def field(label):
        # match <span/td>label</...>...<...>value
        m = re.search(label + r"\s*</[^>]+>\s*(?:<[^>]+>\s*)*([^<]{1,160})", h, re.I)
        return _strip(m.group(1)) if m else None
    # Issuer & description often in page title / header
    title = re.search(r"<title>(.*?)</title>", h, re.I|re.S)
    out["title"] = _strip(title.group(1)) if title else None
    for lab,key in [("Issuer","issuer"),("State","state"),("Dated Date","dated"),
                    ("Maturity Date","maturity"),("Interest Rate","coupon"),
                    ("Coupon","coupon2"),("Tax Status","tax_status"),
                    ("Federally Taxable","fed_taxable"),("Issue Description","issue_desc"),
                    ("Security Description","sec_desc"),("Source of Repayment","repay"),
                    ("Use of Proceeds","use")]:
        v = field(lab)
        if v: out[key] = v
    # broad text dump (collapsed) for keyword sector inference
    body = _strip(h)
    out["_text_excerpt"] = body[:4000]
    return out

def main():
    s = ECD.E._session() if hasattr(ECD.E,"_session") else E._session()
    results = {}
    for c in CUSIPS:
        h, err = detail_html(s, c)
        if h is None:
            results[c] = {"cusip": c, "status":"UNREADABLE","err":err}
            print(f"{c}: UNREADABLE ({err})", file=sys.stderr)
            time.sleep(1.0); continue
        rec = extract(c, h)
        rec["status"]="OK"
        results[c]=rec
        print(f"{c}: {rec.get('issuer','?')} | {rec.get('issue_desc') or rec.get('sec_desc') or rec.get('title','')[:80]}")
        time.sleep(1.2)
    OUT.write_text(json.dumps(results, indent=2))
    print(f"\nwrote {OUT}")

if __name__=="__main__":
    main()
