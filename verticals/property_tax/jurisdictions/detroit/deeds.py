"""Wayne County Parcelmaster deed source — returns Record(record_type="deed")."""
from __future__ import annotations

import asyncio
from datetime import datetime

from core.exceptions import SourceError
from core.models import Entity, Record

source_id = "wayne_county_parcelmaster"
record_type = "deed"

_MONTH_MAP = {
    "JAN": "01", "FEB": "02", "MAR": "03", "APR": "04",
    "MAY": "05", "JUN": "06", "JUL": "07", "AUG": "08",
    "SEP": "09", "OCT": "10", "NOV": "11", "DEC": "12",
}

PARCELMASTER_URL = (
    "https://gdffa833c5bf651-apexprod.adb.us-chicago-1.oraclecloudapps.com"
    "/ords/r/apexprod/wc-parcelmaster/parcel-search"
)


def _normalize_date(raw: str) -> str:
    parts = raw.strip().upper().split("-")
    if len(parts) == 3 and parts[1] in _MONTH_MAP:
        return f"{parts[2]}-{_MONTH_MAP[parts[1]]}-{parts[0].zfill(2)}"
    return raw


def _parse_table(html: str) -> list[dict]:
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "lxml")
    results = []
    for table in soup.find_all("table"):
        headers = [th.get_text(strip=True).lower() for th in table.find_all("th")]
        if not ("sale date" in headers or "grantor" in headers):
            continue
        for row in table.find_all("tr")[1:]:
            cells = [td.get_text(strip=True) for td in row.find_all(["td", "th"])]
            if len(cells) < 4 or not cells[0]:
                continue
            try:
                price_raw = cells[1].replace("$", "").replace(",", "").strip()
                price = float(price_raw) if price_raw else None
            except ValueError:
                price = None

            instr = cells[3].strip().upper() if len(cells) > 3 else ""
            results.append({
                "sale_date":           _normalize_date(cells[0]),
                "sale_price":          price,
                "terms":               cells[2].strip() if len(cells) > 2 else "",
                "instrument_type":     instr,
                "grantor":             cells[4].strip() if len(cells) > 4 else "",
                "grantee":             cells[5].strip() if len(cells) > 5 else "",
                "liber_page":          cells[6].strip() if len(cells) > 6 else "",
                "is_quit_claim":       instr in ("QC", "QUITCLAIM"),
                "is_zero_consideration": price == 0 or price is None,
                "consideration":       price or 0,
            })
    return results


async def _scrape_async(parcel_id: str) -> list[dict]:
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        raise SourceError(
            "playwright required for Wayne County: pip install playwright && "
            "python -m playwright install chromium"
        )

    clean = parcel_id.strip().rstrip(".")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto(PARCELMASTER_URL, wait_until="networkidle", timeout=30000)
            await page.evaluate("""() => {
                const r = document.getElementById('R37412632579059242');
                if (r) r.style.display = 'block';
                try { apex.region('R37412632579059242').refresh(); } catch(e) {}
            }""")
            await page.evaluate("""(pid) => {
                const f = document.getElementById('R37412632579059242_search_field');
                const b = document.getElementById('R37412632579059242_search_button');
                if (f && b) {
                    f.value = pid;
                    f.dispatchEvent(new Event('input', {bubbles: true}));
                    b.click();
                }
            }""", clean)
            await page.wait_for_timeout(4000)
            clicked = await page.evaluate("""(pid) => {
                for (const row of document.querySelectorAll('tr')) {
                    const t = row.textContent;
                    if (t.includes(pid) && t.includes('DETROIT')) {
                        const a = row.querySelector('a');
                        if (a) { a.click(); return true; }
                    }
                }
                for (const a of document.querySelectorAll('a[href*="parcel-details"]')) {
                    if (a.href.includes(pid)) { a.click(); return true; }
                }
                return false;
            }""", clean)
            if not clicked:
                return []
            await page.wait_for_load_state("networkidle", timeout=20000)
            await page.wait_for_timeout(2000)
            return _parse_table(await page.content())
        finally:
            await browser.close()


class WayneCountyDeedSource:
    source_id = "wayne_county_parcelmaster"
    record_type = "deed"
    cache_ttl_days = 90  # deed recordings are rare; Playwright scrape is ~15s, cache aggressively

    def fetch(self, entity: Entity) -> list[Record]:
        return fetch(entity.id)


def fetch(entity_id: str) -> list[Record]:
    """Fetch Wayne County deed history for a parcel."""
    try:
        raw_deeds = asyncio.run(_scrape_async(entity_id))
    except Exception as e:
        raise SourceError(f"Wayne County scrape failed for {entity_id}: {e}") from e

    now = datetime.utcnow()
    records = []
    for d in raw_deeds:
        d["parcel_id"] = entity_id.strip().rstrip(".")
        records.append(Record(
            entity_id=entity_id,
            record_type=record_type,
            source=source_id,
            data=d,
            fetched_at=now,
        ))
    return records
