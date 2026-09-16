"""Re-scrape the 403-throttled CUSIPs from the gauntlet. Slow, polite, persistent.
Merges into outputs/gauntlet_resolution.json. NEVER trades."""
import json, re, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
OUT = HERE / "outputs" / "gauntlet_resolution.json"

NEED = ['79770GET9','79770GES1','79770GCB0','79770GER3','786129DD5','67232TBQ7',
        '13063DZB7','13078RHE3','655505BT1','76913AKY8','13032UMG0','13032UPV4',
        '13032UNW4','03255LHR3','568061CW3']

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

def accept(pg):
    for sel in ("#ctl00_mainContentArea_disclaimerContent_yesButton","#acceptId",
                "input[value=Accept]","button:has-text('I Agree')",
                "button:has-text('Accept')","#ctl00_mainContentArea_btnAccept"):
        try:
            if pg.locator(sel).count():
                pg.locator(sel).first.click(timeout=4000)
                pg.wait_for_load_state("networkidle", timeout=20000)
                return True
        except Exception: pass
    return False

def parse(c, txt):
    rec={"cusip":c,"status":"OK"}
    m=re.search(r'Security Details CUSIP:\s*(.+?)\s+Coupon:', txt)
    rec["desc"]=m.group(1).strip()[:240] if m else None
    for lab,key in [("Coupon","coupon"),("Maturity Date","maturity"),("Dated Date","dated"),
                    ("Initial Offering Price/Yield","offer"),("Principal Amount at Issuance","par_issued"),
                    ("Fiscal Year End Date","fye")]:
        mm=re.search(re.escape(lab)+r":\s*([^\n]{1,80}?)(?:\s{2,}|$|\sMaturity|\sDated|\sInitial|\sPrincipal|\sTime|\sClosing|\sFiscal)", txt)
        rec[key]=mm.group(1).strip() if mm else None
    rec["_excerpt"]=re.sub(r"\s+"," ",txt[:4500])
    return rec

def main():
    results=json.loads(OUT.read_text()) if OUT.exists() else {}
    with sync_playwright() as p:
        b=p.chromium.launch(channel="chrome", headless=True)
        ctx=b.new_context(user_agent=UA, viewport={"width":1280,"height":900})
        pg=ctx.new_page()
        pg.goto("https://emma.msrb.org/Security/Details/036680BZ8", wait_until="domcontentloaded", timeout=60000)
        pg.wait_for_timeout(3000); accept(pg); pg.wait_for_timeout(2000)
        todo=list(NEED)
        attempt=0
        while todo and attempt<4:
            attempt+=1
            still=[]
            for c in todo:
                ok=False
                for retry in range(2):
                    try:
                        pg.goto(f"https://emma.msrb.org/Security/Details/{c}", wait_until="domcontentloaded", timeout=60000)
                        pg.wait_for_timeout(4000)
                        accept(pg)
                        pg.wait_for_timeout(2500)
                        txt=pg.inner_text("body")
                        if "Security Details CUSIP:" in txt and "Coupon:" in txt:
                            results[c]=parse(c,txt)
                            print(f"OK  {c}: {results[c]['desc'][:90] if results[c]['desc'] else '??'}", flush=True)
                            ok=True; break
                        else:
                            print(f"403 {c} (attempt {attempt}.{retry}) backing off", flush=True)
                            time.sleep(25)
                    except Exception as e:
                        print(f"ERR {c}: {str(e)[:80]}", flush=True); time.sleep(15)
                if not ok: still.append(c)
                OUT.write_text(json.dumps(results,indent=2))
                time.sleep(8)
            todo=still
            if todo:
                print(f"--- {len(todo)} still throttled, long backoff before pass {attempt+1} ---", flush=True)
                time.sleep(60)
        b.close()
    print("REMAINING UNRESOLVED:", todo)
    OUT.write_text(json.dumps(results,indent=2))

if __name__=="__main__":
    main()
