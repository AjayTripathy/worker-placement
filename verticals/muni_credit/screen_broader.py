"""Broader EMMA screen: source REAL new CA school-GO + water-revenue CUSIPs from OS maturity
schedules (EMMA encrypts the scale CUSIPs, but the OS lists them in plaintext), then pull CURRENT
stats per CUSIP via the same security-details pipeline as the basket. Target: ~9 more to reach 20.
"""
import sys, re, json, subprocess
from pathlib import Path
sys.path.insert(0, "/Users/ajay/exalted/signalos/verticals/muni_credit")
import emma_scraper as E
import compute_bond_analytics as CBA

SCHOOL = ["Los Angeles Unified School District", "Long Beach Unified School District",
          "Santa Ana Unified School District", "Fresno Unified School District",
          "Elk Grove Unified School District", "San Francisco Unified School District",
          "Sweetwater Union High School District", "Garden Grove Unified School District",
          "Capistrano Unified School District", "Mount Diablo Unified School District"]
WATER = ["East Bay Municipal Utility District", "San Diego County Water Authority",
         "Santa Clara Valley Water District"]


def parse_os_cusips(txt):
    """Return list of (year, coupon, yield, full_cusip) from an OS maturity schedule."""
    base = None
    m = re.search(r'CUSIP.{0,60}?\(?\s*(\d{6})\s*\)?', txt, re.S)
    if m:
        base = m.group(1)
    out = []
    # row: year ... coupon% ... yield% ... 3-char suffix (base+suffix convention)
    for r in re.finditer(r'\b(20[2-5]\d)\b[^\n]{0,90}?([0-9]\.[0-9]{2,3})\s*%[^\n]{0,40}?([0-9]\.[0-9]{2,3})\s*%[^0-9A-Za-z\n]{0,12}([A-Z0-9]{2}[0-9A-Z])\b', txt):
        yr, cpn, yld, suf = r.groups()
        if base and len(suf) == 3:
            out.append((int(yr), float(cpn), float(yld), base + suf))
    # fallback: full 9-char CUSIPs inline
    if not out:
        for r in re.finditer(r'\b(20[2-5]\d)\b[^\n]{0,90}?([0-9]\.[0-9]{2,3})\s*%[^\n]{0,40}?([0-9]\.[0-9]{2,3})\s*%[^\n]{0,12}([0-9]{6}[A-Z0-9]{2}[0-9])\b', txt):
            yr, cpn, yld, cu = r.groups(); out.append((int(yr), float(cpn), float(yld), cu))
    return out


def get_candidate(issuer, s, want_year=(2033, 2042)):
    """Find a recent OS, parse it, return one intermediate-maturity (cusip, coupon, mat, offer_yld)."""
    for i in E.search_issues(issuer, s):
        if i["issue_id"][:2] not in ("ER", "ES", "EP", "MS"):
            continue
        E.accept_disclaimer(s, i["issue_id"])
        os_url = E.get_official_statement(i["issue_id"], s)
        if not os_url:
            continue
        try:
            E.download_pdf(os_url, Path("/tmp/_scr.pdf"), s)
            subprocess.run(["pdftotext", "-layout", "-f", "1", "-l", "5", "/tmp/_scr.pdf", "/tmp/_scr.txt"],
                           timeout=60, capture_output=True)
            rows = parse_os_cusips(open("/tmp/_scr.txt", encoding="utf-8", errors="ignore").read())
        except Exception:
            rows = []
        # prefer an intermediate maturity with a real coupon
        cand = [r for r in rows if want_year[0] <= r[0] <= want_year[1] and r[1] >= 2.0]
        if cand:
            yr, cpn, yld, cu = sorted(cand, key=lambda r: abs(r[0] - 2037))[0]
            return {"issuer": issuer, "issue": i["issue_id"], "cusip": cu,
                    "os_coupon": cpn, "os_year": yr, "os_offer_yield": yld, "os_url": os_url}
    return None


def main():
    s = E._session()
    found = []
    for issuer, sec in [(x, "school_go_sb222") for x in SCHOOL] + [(x, "water") for x in WATER]:
        if len(found) >= 9:
            break
        c = get_candidate(issuer, s)
        if not c:
            print(f"  -- {issuer[:38]:38} no parseable OS schedule"); continue
        c["sector"] = sec
        # current stats via security-details (same as basket)
        try:
            rec = CBA.fetch_security(c["cusip"], s)
            an = CBA.analyze(rec)
        except Exception as ex:
            rec, an = {"error": str(ex)}, None
        c["emma_coupon"] = rec.get("coupon"); c["emma_mat"] = rec.get("maturity")
        c["trade_date"] = rec.get("trade_date"); c["price"] = rec.get("price")
        if an:
            c["ytw"] = round(rec["trade_yield"] / 100, 5) if rec.get("trade_yield") else round(an["my_ytw"], 5)
            c["ytm"] = round(an["ytm"], 5); c["dur_worst"] = round(an["dur_to_worst"], 2)
            c["dur_mat"] = round(an["dur_to_maturity"], 2); c["src"] = "EMMA trade"
        else:  # no current trade -> use OS offering yield, flag
            c["ytw"] = c["ytm"] = round(c["os_offer_yield"] / 100, 5); c["dur_worst"] = c["dur_mat"] = None; c["src"] = "OS offering (at-issuance)"
        found.append(c)
        print(f"  OK {issuer[:34]:34} cusip {c['cusip']} {c.get('emma_coupon') or c['os_coupon']}% "
              f"mat {c.get('emma_mat') or c['os_year']} | YTW {(c['ytw'] or 0)*100:.2f}% YTM {(c['ytm'] or 0)*100:.2f}% [{c['src']}]")
    json.dump(found, open("/Users/ajay/exalted/signalos/verticals/muni_credit/data/broader_screen.json", "w"), indent=1, default=str)
    print(f"\nsourced {len(found)} new real names -> data/broader_screen.json")


if __name__ == "__main__":
    main()
