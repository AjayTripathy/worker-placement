"""Pass 2: capture FULL body text per CUSIP from EMMA Security/Details."""
import json, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
OUT = HERE / "outputs" / "csfa_gauntlet_bodies.json"
CUSIPS = ["13058TMK3","13058TQL7","13058TVH0","13058TTQ3","13058TRV4","13058TKV1",
"13058TMA5","13058TPU8","13058TSZ4","13058TRB8","13058TPN4","13058TUJ7","13058TMY3",
"13058TQA1","13058TTK6","13058TVQ0","13058TQE3","13058TLY4","13058TLZ1","13058TVD9"]
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

def accept(pg):
    for sel in ("#ctl00_mainContentArea_disclaimerContent_yesButton","#acceptId","input[value=Accept]"):
        try:
            if pg.locator(sel).count():
                pg.locator(sel).first.click(timeout=4000); pg.wait_for_load_state("networkidle",timeout=20000); return
        except Exception: pass

def main():
    res={}
    with sync_playwright() as p:
        b=p.chromium.launch(channel="chrome",headless=True)
        ctx=b.new_context(user_agent=UA); pg=ctx.new_page()
        pg.goto("https://emma.msrb.org/Security/Details/13058TMK3",wait_until="domcontentloaded",timeout=60000)
        pg.wait_for_timeout(2500); accept(pg); pg.wait_for_timeout(1500)
        for c in CUSIPS:
            try:
                pg.goto(f"https://emma.msrb.org/Security/Details/{c}",wait_until="domcontentloaded",timeout=45000)
                pg.wait_for_timeout(1700); accept(pg); pg.wait_for_timeout(700)
                res[c]=pg.inner_text("body")
            except Exception as e:
                res[c]=f"__ERR__ {type(e).__name__}: {e}"
            print(c, "len", len(res[c]), file=sys.stderr); time.sleep(0.6)
        b.close()
    OUT.write_text(json.dumps(res,indent=1)); print("WROTE",OUT)

if __name__=="__main__": main()
