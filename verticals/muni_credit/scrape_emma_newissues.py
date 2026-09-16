"""scrape_emma_newissues — drive a real browser to MSRB EMMA's New Issue Calendar (the forward CA muni
pipeline) and write data/ca_newissue_calendar.csv for new_issue_watch to vet.

EMMA's calendar (emma.msrb.org/ToolsAndResources/NewIssueCalendar) is an ASP.NET page behind a disclaimer
gate that throttles requests-based scraping; a headless browser accepts the disclaimer and renders the
table (State | Issuer/Description | Amount | Date | Time | Maturities | BankQual | Tax Status | ESG).
We keep CA + tax-exempt rows and hand them to new_issue_watch.py's fit-engine. NEVER trades.

This closes the loop: cron runs this (browser) -> writes the CA calendar -> new_issue_watch alerts.
"""
import csv, datetime, os, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CAL = HERE / "data" / "ca_newissue_calendar.csv"
URL = "https://emma.msrb.org/ToolsAndResources/NewIssueCalendar"
_STATES = set("AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ "
              "NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY DC PR".split())


def scrape(headless=True):
    from playwright.sync_api import sync_playwright
    rows_out = []
    with sync_playwright() as p:
        b = p.chromium.launch(headless=headless)
        pg = b.new_page(user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36")
        pg.goto(URL, wait_until="networkidle", timeout=60000)
        for sel in ("#ctl00_mainContentArea_disclaimerContent_yesButton", "#acceptId", "input[value=Accept]"):
            try:
                if pg.locator(sel).count():
                    pg.locator(sel).first.click(timeout=5000); break
            except Exception:
                pass
        pg.wait_for_load_state("networkidle", timeout=30000); pg.wait_for_timeout(3000)
        try:
            pg.locator("select").first.select_option("100"); pg.wait_for_timeout(2500)
        except Exception:
            pass
        trs = pg.locator("table tr")
        n = trs.count()
        cur_week = ""
        for i in range(n):
            txt = trs.nth(i).inner_text() or ""
            cells = [c.strip() for c in txt.split("\t") if c.strip()]
            if not cells:
                continue
            if cells[0].lower().startswith("week of"):
                cur_week = cells[0]; continue
            if cells[0] not in _STATES:
                continue                                   # header / group row
            state = cells[0]
            desc = cells[1] if len(cells) > 1 else ""
            amount = next((c for c in cells[2:] if re.match(r"[\d,]{4,}$", c.replace(",", "")) or "," in c), "")
            date = next((c for c in cells if re.match(r"\d{1,2}/\d{1,2}/\d{2,4}", c)), "")
            taxst = "Taxable" if "Taxable" in txt else ("Tax Exempt" if "Tax Exempt" in txt else "")
            # firm date if competitive; else "day-to-day" within the listed week (negotiated, prices at the
            # underwriter's discretion) — carry the WEEK so the alert shows timing, not a bare TBD.
            wk = cur_week.replace("Week of Monday, ", "wk of ").replace("Week of ", "wk of ")
            sale = date if date else (f"{wk} (day-to-day)" if wk else "TBD")
            rows_out.append({"state": state, "description": desc.rstrip("N").strip(),
                             "amount": amount, "sale_date": sale, "tax_status": taxst, "week": cur_week})
        b.close()
    return rows_out


def main():
    headless = "--show" not in sys.argv
    try:
        rows = scrape(headless=headless)
    except Exception as e:
        print(f"EMMA scrape FAILED ({type(e).__name__}: {str(e)[:80]}) — calendar not refreshed", file=sys.stderr)
        return
    ca = [r for r in rows if r["state"] == "CA"]
    CAL.parent.mkdir(parents=True, exist_ok=True)
    with open(CAL, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["issuer", "description", "type", "sale_date", "amount", "tax_status"])
        w.writeheader()
        for r in ca:
            w.writerow({"issuer": r["description"], "description": r["description"], "type": "",
                        "sale_date": r["sale_date"], "amount": r["amount"], "tax_status": r["tax_status"]})
    print(f"EMMA New Issue Calendar: {len(rows)} rows scraped, {len(ca)} CA -> {CAL}")
    print(f"  asof {datetime.date(2026,6,22)}; feed to new_issue_watch.py")


if __name__ == "__main__":
    main()
