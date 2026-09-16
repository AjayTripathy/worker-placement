"""Resolve CSFA charter CUSIPs -> obligor via EMMA Security/Details (browser path).
Writes outputs/csfa_gauntlet_resolve.json. NEVER trades."""
import json, re, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
OUT = HERE / "outputs" / "csfa_gauntlet_resolve.json"

CUSIPS = ["13058TMK3","13058TQL7","13058TVH0","13058TTQ3","13058TRV4","13058TKV1",
"13058TMA5","13058TPU8","13058TSZ4","13058TRB8","13058TPN4","13058TUJ7","13058TMY3",
"13058TQA1","13058TTK6","13058TVQ0","13058TQE3","13058TLY4","13058TLZ1","13058TVD9"]

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

def accept_disclaimer(pg):
    for sel in ("#ctl00_mainContentArea_disclaimerContent_yesButton","#acceptId",
                "input[value=Accept]","button:has-text('I Agree')","#ctl00_mainContentArea_btnAccept"):
        try:
            if pg.locator(sel).count():
                pg.locator(sel).first.click(timeout=4000)
                pg.wait_for_load_state("networkidle", timeout=20000)
                return True
        except Exception:
            pass
    return False

def main():
    results = {}
    with sync_playwright() as p:
        b = p.chromium.launch(channel="chrome", headless=True)
        ctx = b.new_context(user_agent=UA)
        pg = ctx.new_page()
        # prime disclaimer once
        pg.goto("https://emma.msrb.org/Security/Details/13058TMK3", wait_until="domcontentloaded", timeout=60000)
        pg.wait_for_timeout(2500)
        accept_disclaimer(pg)
        pg.wait_for_timeout(1500)
        for c in CUSIPS:
            rec = {"cusip": c}
            try:
                pg.goto(f"https://emma.msrb.org/Security/Details/{c}", wait_until="domcontentloaded", timeout=45000)
                pg.wait_for_timeout(1800)
                accept_disclaimer(pg)
                pg.wait_for_timeout(800)
                body = pg.inner_text("body")
                rec["raw_len"] = len(body)
                # Issuer / description usually near top
                # Pull key labeled fields
                def grab(label):
                    m = re.search(re.escape(label)+r"\s*[:\n]\s*(.+)", body)
                    return m.group(1).strip()[:160] if m else None
                rec["issuer"] = grab("Issuer")
                rec["issue_desc"] = grab("Issue Description") or grab("Official Statement")
                rec["dated"] = grab("Dated Date")
                rec["maturity"] = grab("Maturity Date")
                rec["coupon"] = grab("Coupon")
                rec["tax_status"] = grab("Tax Status") or ("FEDERALLY TAXABLE" if "FEDERALLY TAXABLE" in body.upper() else None)
                rec["rating_block"] = None
                # capture a window around 'charter' to find obligor school
                low = body.lower()
                snips = []
                for kw in ["charter","academy","public schools","kipp","aspire","alliance","green dot",
                           "bright star","camino","da vinci","magnolia","caliber","gateway","ednovate",
                           "rocketship","equitas","vista","scholarship","fenton","extera","new designs",
                           "ice","environmental charter","granada","lifeline","celerity","partnerships to uplift"]:
                    idx = low.find(kw)
                    if idx >= 0:
                        snips.append(body[max(0,idx-60):idx+80].replace("\n"," "))
                rec["obligor_snips"] = list(dict.fromkeys(snips))[:6]
                # title of page
                rec["title"] = pg.title()
            except Exception as e:
                rec["error"] = f"{type(e).__name__}: {str(e)[:120]}"
            results[c] = rec
            print(f"{c}  issuer={rec.get('issuer')}  err={rec.get('error')}", file=sys.stderr)
            time.sleep(0.8)
        b.close()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(results, indent=1))
    print(f"WROTE {OUT}")

if __name__ == "__main__":
    main()
