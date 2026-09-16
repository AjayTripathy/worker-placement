"""Browser resolver: render EMMA Security/Details/<cusip> (JS-populated header) to extract
obligor/issuer name, issue description, sector cues, coupon/maturity/dated, tax status, ratings.
Writes outputs/gauntlet_resolution.json keyed by CUSIP.
"""
import json, re, sys, time
from pathlib import Path

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

def main():
    from playwright.sync_api import sync_playwright
    results = {}
    if OUT.exists():
        try: results = json.loads(OUT.read_text())
        except Exception: results = {}
    with sync_playwright() as p:
        b = p.chromium.launch(channel="chrome", headless=True)
        ctx = b.new_context(user_agent=("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
              "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"))
        pg = ctx.new_page()
        # accept disclaimer once
        pg.goto("https://emma.msrb.org/Security/Details/036680BZ8", wait_until="domcontentloaded", timeout=60000)
        for sel in ("#ctl00_mainContentArea_disclaimerContent_yesButton","#acceptId","input[value=Accept]"):
            try:
                if pg.locator(sel).count(): pg.locator(sel).first.click(timeout=5000); break
            except Exception: pass
        pg.wait_for_timeout(2500)
        for c in CUSIPS:
            prev=results.get(c,{})
            ex_prev=prev.get("_excerpt","")
            if ex_prev and "403" not in ex_prev[:20] and "Security Details CUSIP" in ex_prev:
                continue  # already resolved cleanly
            try:
                pg.goto(f"https://emma.msrb.org/Security/Details/{c}", wait_until="domcontentloaded", timeout=60000)
                # wait for header to populate
                pg.wait_for_timeout(4500)
                txt = pg.inner_text("body")
                if "403 Forbidden" in txt[:40] or "Security Details CUSIP" not in txt:
                    # rate-limited: back off hard and retry once
                    time.sleep(20)
                    pg.goto(f"https://emma.msrb.org/Security/Details/{c}", wait_until="domcontentloaded", timeout=60000)
                    pg.wait_for_timeout(4500)
                    txt = pg.inner_text("body")
                rec = {"cusip": c, "status":"OK"}
                # header: usually first lines contain issuer + description
                # grab labelled fields from full text
                def fval(label):
                    m = re.search(re.escape(label)+r"\s*:?\s*\n?\s*([^\n]{1,160})", txt)
                    return m.group(1).strip() if m else None
                rec["coupon"]=fval("Coupon")
                rec["maturity"]=fval("Maturity Date")
                rec["dated"]=fval("Dated Date")
                rec["tax_status"]=fval("Tax Status")
                rec["source_of_repayment"]=fval("Source of Repayment")
                rec["state"]=fval("State")
                # header / issuer: try known header selectors
                for sel in ["h1","h2",".security-header",".securityHeader","#securityHeader",".issuer-name"]:
                    try:
                        loc=pg.locator(sel)
                        for i in range(min(loc.count(),5)):
                            t=loc.nth(i).inner_text().strip()
                            if t and t.lower() not in ("security details","") and "emma" not in t.lower() and len(t)>5:
                                rec.setdefault("header_candidates",[]).append(t[:200])
                    except Exception: pass
                # description block: text between top and 'Coupon'
                head = txt[:txt.find("Coupon")] if "Coupon" in txt else txt[:600]
                # keep the meaningful lines
                lines=[l.strip() for l in head.split("\n") if l.strip()]
                rec["top_lines"]=[l for l in lines if len(l)>6][:25]
                rec["_excerpt"]=re.sub(r"\s+"," ",txt[:4500])
                results[c]=rec
                hc = rec.get("header_candidates") or rec.get("top_lines")
                print(f"{c}: {hc[:3] if hc else '??'}")
            except Exception as e:
                results[c]={"cusip":c,"status":"ERR","err":str(e)[:120]}
                print(f"{c}: ERR {e}", file=sys.stderr)
            OUT.write_text(json.dumps(results,indent=2))
            time.sleep(4.0)
        b.close()
    print("done ->",OUT)

if __name__=="__main__":
    main()
