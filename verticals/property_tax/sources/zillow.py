"""
Zillow sale history source — national scope, property_tax vertical.

Primary: HTTP (fast, but PerimeterX may block).
Fallback: Playwright headless Chromium (slower, bypasses bot detection).

Requires entity.metadata["address"] to be set (injected from assessor seed record).
"""
from __future__ import annotations

import asyncio
import json
import re
import time
import urllib.parse
from datetime import date, datetime
from decimal import Decimal

import httpx

try:
    from playwright.async_api import async_playwright
    _PLAYWRIGHT = True
except ImportError:
    _PLAYWRIGHT = False

from core.models import Entity, Record

ZILLOW_BASE = "https://www.zillow.com"
_NEXT_DATA_RE = re.compile(
    r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', re.DOTALL
)
_PRICE_HISTORY_RE = re.compile(r'"priceHistory"\s*:\s*(\[.*?\])', re.DOTALL)

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}
_DELAY_SECS = 1.0


def _safe_date(raw: str) -> date | None:
    try:
        return date.fromisoformat(raw[:10])
    except (ValueError, TypeError):
        return None


def _search_zpid(client: httpx.Client, address: str) -> str | None:
    url = f"{ZILLOW_BASE}/homes/{urllib.parse.quote(address)}_rb/"
    try:
        resp = client.get(url, timeout=20)
        resp.raise_for_status()
    except Exception:
        return None

    m = _NEXT_DATA_RE.search(resp.text)
    if m:
        try:
            data = json.loads(m.group(1))
            props = data.get("props", {}).get("pageProps", {})
            zpid = props.get("zpid") or props.get("initialReduxState", {}).get("gdpClientCache", {})
            if isinstance(zpid, dict):
                first_key = next(iter(zpid), None)
                if first_key:
                    return str(first_key).split("-")[0]
        except (json.JSONDecodeError, KeyError, StopIteration):
            pass

    m = re.search(r'"zpid"\s*:\s*(\d+)', resp.text)
    return m.group(1) if m else None


def _parse_price_history(html: str) -> list[dict]:
    m = _NEXT_DATA_RE.search(html)
    if m:
        try:
            data = json.loads(m.group(1))
            ph_match = _PRICE_HISTORY_RE.search(json.dumps(data))
            if ph_match:
                history = json.loads(ph_match.group(1))
                sales = []
                for event in history:
                    if event.get("event", "").lower() in ("sold", "sale"):
                        price = event.get("price") or event.get("priceRaw")
                        d = event.get("date") or event.get("dateStr")
                        if price and d:
                            try:
                                sales.append({
                                    "sale_date": str(d),
                                    "sale_price": float(str(price).replace(",", "").replace("$", "")),
                                })
                            except (ValueError, TypeError):
                                pass
                return sales
        except (json.JSONDecodeError, ValueError):
            pass
    return []


async def _playwright_fetch_async(address: str) -> list[dict]:
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
        )
        ctx = await browser.new_context(
            user_agent=_HEADERS["User-Agent"],
            viewport={"width": 1280, "height": 800},
            locale="en-US",
        )
        page = await ctx.new_page()
        await page.add_init_script(
            "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"
        )
        try:
            url = f"{ZILLOW_BASE}/homes/{urllib.parse.quote(address)}_rb/"
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(3000)
            return _parse_price_history(await page.content())
        except Exception:
            return []
        finally:
            await browser.close()


def _get_sale_history(address: str) -> list[dict]:
    try:
        with httpx.Client(headers=_HEADERS, follow_redirects=True, timeout=20) as client:
            zpid = _search_zpid(client, address)
            time.sleep(_DELAY_SECS)
            url = (
                f"{ZILLOW_BASE}/homedetails/{zpid}_zpid/"
                if zpid
                else f"{ZILLOW_BASE}/homes/{urllib.parse.quote(address)}_rb/"
            )
            resp = client.get(url, timeout=20)
            resp.raise_for_status()
            sales = _parse_price_history(resp.text)
            if sales:
                return sorted(sales, key=lambda s: s["sale_date"], reverse=True)
    except Exception:
        pass

    if not _PLAYWRIGHT:
        return []
    try:
        sales = asyncio.run(_playwright_fetch_async(address))
        return sorted(sales, key=lambda s: s["sale_date"], reverse=True)
    except Exception:
        return []


class ZillowSaleSource:
    source_id = "zillow"
    record_type = "sale"
    cache_ttl_days = 30

    def fetch(self, entity: Entity) -> list[Record]:
        address = entity.metadata.get("address", "")
        if not address:
            return []

        raw_sales = _get_sale_history(address)
        now = datetime.utcnow()
        records = []
        for s in raw_sales:
            parsed_date = _safe_date(s.get("sale_date", ""))
            if parsed_date is None:
                continue
            try:
                records.append(Record(
                    entity_id=entity.id,
                    record_type=self.record_type,
                    source=self.source_id,
                    data={
                        "parcel_id": entity.id,
                        "sale_date": parsed_date.isoformat(),
                        "sale_price": float(s["sale_price"]),
                        "source": self.source_id,
                        "is_arms_length": None,
                    },
                    fetched_at=now,
                ))
            except Exception:
                pass
        return records
