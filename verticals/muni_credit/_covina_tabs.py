"""Extract the Pre-Sale Documents / Official Statements tab hrefs from the Covina issuer homepage,
navigate to each, and dump body + document links. Writes outputs/covina_tabs.json."""
import json, re
from pathlib import Path
HERE=Path(__file__).resolve().parent
OUT=HERE/"outputs"/"covina_tabs.json"
HOME="https://emma.msrb.org/IssuerHomePage/Issuer?id=CDB5143F246317936BA4292FFBF3D0E0&type=G"
UA=("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
def accept(pg):
    for sel in ("#ctl00_mainContentArea_disclaimerContent_yesButton","#acceptId","input[value=Accept]"):
        try:
            if pg.locator(sel).count(): pg.locator(sel).first.click(timeout=5000); return
        except Exception: pass
def links(pg):
    out=[]; a=pg.locator("a")
    for i in range(min(a.count(),900)):
        try:
            href=a.nth(i).get_attribute("href") or ""
            t=(a.nth(i).inner_text() or "").strip()
            if href: out.append({"t":t[:140],"h":href})
        except Exception: pass
    return out
def main():
    from playwright.sync_api import sync_playwright
    res={}
    with sync_playwright() as p:
        b=p.chromium.launch(channel="chrome", headless=True)
        ctx=b.new_context(user_agent=UA); pg=ctx.new_page()
        pg.goto(HOME, wait_until="domcontentloaded", timeout=60000)
        accept(pg); pg.wait_for_timeout(4000)
        tab_hrefs={}
        for name in ["Pre-Sale Documents","Official Statements","Issues"]:
            try:
                loc=pg.locator(f"a:has-text('{name}')")
                if loc.count():
                    tab_hrefs[name]=loc.first.get_attribute("href")
            except Exception: pass
        res["tab_hrefs"]=tab_hrefs
        for name,href in tab_hrefs.items():
            if not href: continue
            url = href if href.startswith("http") else ("https://emma.msrb.org"+href)
            try:
                pg.goto(url, wait_until="domcontentloaded", timeout=60000)
                accept(pg); pg.wait_for_timeout(4500)
                try:
                    s=pg.locator("select")
                    for i in range(s.count()):
                        try: s.nth(i).select_option("100"); pg.wait_for_timeout(1200)
                        except Exception: pass
                except Exception: pass
                pg.wait_for_timeout(1500)
                res[name]={"url":url,"body":re.sub(r"\s+"," ",pg.inner_text("body"))[:4000],
                           "links":[l for l in links(pg) if l['h'] and ('.pdf' in l['h'].lower()
                                    or 'IssueView' in l['h'] or 'Document' in l['h'] or 'Disclosure' in l['h'])]}
            except Exception as e:
                res[name]={"url":url,"err":str(e)[:160]}
        b.close()
    OUT.write_text(json.dumps(res,indent=2)); print("wrote",OUT)
if __name__=="__main__": main()
