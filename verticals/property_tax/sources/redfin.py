"""
Redfin sale history source — national scope, property_tax vertical.

Primary: HTTP via stingray internal API (fast).
Fallback: Playwright — establishes Cloudflare session then calls stingray in-browser.

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

REDFIN_BASE = "https://www.redfin.com"
AUTOCOMPLETE_URL = f"{REDFIN_BASE}/stingray/do/location-autocomplete"
PROPERTY_HISTORY_URL = f"{REDFIN_BASE}/stingray/api/home/details/propertyHistory"
_RF_PREFIX = re.compile(r"^[^\[{]*")

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json,text/html,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}
_DELAY_SECS = 1.0


def _strip_prefix(text: str) -> str:
    return _RF_PREFIX.sub("", text, count=1)


def _safe_date(raw: str) -> date | None:
    try:
        return date.fromisoformat(str(raw)[:10])
    except (ValueError, TypeError):
        return None


def _resolve_property_id(client: httpx.Client, address: str) -> str | None:
    params = {"location": address, "v": "2", "market": "detroit", "al": "1"}
    try:
        resp = client.get(AUTOCOMPLETE_URL, params=params, timeout=20)
        resp.raise_for_status()
    except Exception:
        return None

    try:
        data = json.loads(_strip_prefix(resp.text))
    except json.JSONDecodeError:
        return None

    payload = data.get("payload", {})
    completion = payload.get("exactMatch") or (
        payload.get("sections", [{}])[0].get("rows", [{}])[0]
        if payload.get("sections") else {}
    )
    if not isinstance(completion, dict):
        return None

    url_path = completion.get("url", "")
    m = re.search(r"/(\d+)_zpid", url_path) or re.search(r"propertyId=(\d+)", url_path)
    if m:
        return m.group(1)
    prop_id = completion.get("id")
    return str(prop_id) if prop_id else None


def _fetch_property_history(client: httpx.Client, property_id: str) -> list[dict]:
    try:
        resp = client.get(
            PROPERTY_HISTORY_URL,
            params={"propertyId": property_id, "accessLevel": "3"},
            timeout=20,
        )
        resp.raise_for_status()
    except Exception:
        return []

    try:
        data = json.loads(_strip_prefix(resp.text))
    except json.JSONDecodeError:
        return []

    events = (
        data.get("payload", {}).get("propertyHistoryInfo", {}).get("events", [])
        or data.get("payload", {}).get("events", [])
    )
    sales = []
    for ev in events:
        et = str(ev.get("eventType", "")).lower()
        desc = str(ev.get("description", "")).lower()
        if "sold" in et or "sold" in desc or ev.get("eventType") == 3:
            price = ev.get("price") or ev.get("listedPrice")
            d = ev.get("eventDate") or ev.get("date")
            if price and d:
                try:
                    sales.append({
                        "sale_date": str(d)[:10],
                        "sale_price": float(price),
                    })
                except (ValueError, TypeError):
                    pass
    return sales


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
            search_url = (
                f"{REDFIN_BASE}/city/Detroit/MI/homes-for-sale"
                f"?searchParam={urllib.parse.quote(address)}"
            )
            await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(2000)

            ac_url = (
                f"{REDFIN_BASE}/stingray/do/location-autocomplete"
                f"?location={urllib.parse.quote(address)}&v=2&market=detroit&al=1"
            )
            ac_text = await page.evaluate(f"""async () => {{
                const r = await fetch('{ac_url}', {{credentials:'include'}});
                return await r.text();
            }}""")

            data = json.loads(_strip_prefix(ac_text))
            payload = data.get("payload", {})
            completion = payload.get("exactMatch") or (
                payload.get("sections", [{}])[0].get("rows", [{}])[0]
                if payload.get("sections") else None
            )
            if not completion:
                return []

            url_path = completion.get("url", "")
            m = re.search(r"/(\d+)_zpid", url_path) or re.search(r"propertyId=(\d+)", url_path)
            prop_id = m.group(1) if m else str(completion.get("id", ""))
            if not prop_id:
                return []

            hist_url = (
                f"{REDFIN_BASE}/stingray/api/home/details/propertyHistory"
                f"?propertyId={prop_id}&accessLevel=3"
            )
            hist_text = await page.evaluate(f"""async () => {{
                const r = await fetch('{hist_url}', {{credentials:'include'}});
                return await r.text();
            }}""")
            hist_data = json.loads(_strip_prefix(hist_text))
            events = (
                hist_data.get("payload", {}).get("propertyHistoryInfo", {}).get("events", [])
                or hist_data.get("payload", {}).get("events", [])
            )
            sales = []
            for ev in events:
                et = str(ev.get("eventType", "")).lower()
                desc = str(ev.get("description", "")).lower()
                if "sold" in et or "sold" in desc or ev.get("eventType") == 3:
                    price = ev.get("price") or ev.get("listedPrice")
                    d = ev.get("eventDate") or ev.get("date")
                    if price and d:
                        try:
                            sales.append({"sale_date": str(d)[:10], "sale_price": float(price)})
                        except (ValueError, TypeError):
                            pass
            return sales
        except Exception:
            return []
        finally:
            await browser.close()


def _get_sale_history(address: str) -> list[dict]:
    try:
        with httpx.Client(headers=_HEADERS, follow_redirects=True, timeout=20) as client:
            property_id = _resolve_property_id(client, address)
            time.sleep(_DELAY_SECS)
            if property_id:
                sales = _fetch_property_history(client, property_id)
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


class RedfinSaleSource:
    source_id = "redfin"
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
