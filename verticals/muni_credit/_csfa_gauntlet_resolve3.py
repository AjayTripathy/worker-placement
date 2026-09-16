"""Pass 3: remaining 13 CUSIPs, fresh context, slow pacing, retry on block."""
import json, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
OUT = HERE / "outputs" / "csfa_gauntlet_bodies2.json"
CUSIPS = ["13058TPU8","13058TSZ4","13058TRB8","13058TPN4","13058TUJ7","13058TMY3",
"13058TQA1","13058TTK6","13058TVQ0","13058TQE3","13058TLY4","13058TLZ1","13058TVD9"]
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

def accept(pg):
    for sel in ("#ctl00_mainContentArea_disclaimerContent_yesButton","#acceptId","input[value=Accept]"):
        try:
            if pg.locator(sel).count():
                pg.locator(sel).first.click(timeout=4000); pg.wait_for_load_state("networkidle",timeout=20000); return
        except Exception: pass

def fetch_one(c, headless=True):
    with sync_playwright() as p:
        b=p.chromium.launch(channel="chrome",headless=headless)
        ctx=b.new_context(user_agent=UA); pg=ctx.new_page()
        try:
            pg.goto(f"https://emma.msrb.org/Security/Details/{c}",wait_until="domcontentloaded",timeout=60000)
            pg.wait_for_timeout(3000); accept(pg); pg.wait_for_timeout(2000)
            body=pg.inner_text("body")
        except Exception as e:
            body=f"__ERR__ {type(e).__name__}: {e}"
        b.close()
    return body

def main():
    res={}
    for c in CUSIPS:
        body=fetch_one(c)
        tries=0
        while len(body)<100 and tries<2:
            time.sleep(8); body=fetch_one(c); tries+=1
        res[c]=body
        print(c,"len",len(body),"tries",tries,file=sys.stderr)
        time.sleep(5)
    OUT.write_text(json.dumps(res,indent=1)); print("WROTE",OUT)

if __name__=="__main__": main()
