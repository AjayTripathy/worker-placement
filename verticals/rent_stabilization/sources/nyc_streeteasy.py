"""
StreetEasy rental listing source — returns Record(record_type="listing").

Fetches active rental listings for a given NYC building address or BBL.
StreetEasy is the dominant NYC rental listing platform; its data reflects
actual advertised rents, which is the market signal M in the gap function.

Two fetch paths:
  1. HTTP search (fast, works most of the time)
  2. Playwright fallback (if Cloudflare blocks the HTTP request)

The source returns one Record per active listing found.
"""
from __future__ import annotations

import json
import re
from datetime import date, datetime

import httpx

from core.exceptions import SourceError
from core.models import Entity, Record

source_id   = "nyc_streeteasy"
record_type = "listing"

_SEARCH_URL = "https://streeteasy.com/for-rent/nyc"
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

_PRICE_RE = re.compile(r"\$([0-9,]+)/mo", re.IGNORECASE)
_BR_RE    = re.compile(r"(\d+)\s*(?:bed|br)", re.IGNORECASE)


def _parse_price(text: str) -> float | None:
    m = _PRICE_RE.search(text)
    if m:
        return float(m.group(1).replace(",", ""))
    return None


def _parse_bedrooms(text: str) -> int:
    m = _BR_RE.search(text)
    if m:
        return int(m.group(1))
    if "studio" in text.lower():
        return 0
    return 1  # default 1BR if ambiguous


class NYCStreetEasySource:
    source_id      = source_id
    record_type    = record_type
    cache_ttl_days = 3    # listings change frequently

    def fetch(self, entity: Entity) -> list[Record]:
        address = entity.metadata.get("address", "")
        bbl     = entity.id
        if not address:
            return []
        return _fetch_listings(address, bbl)


def _fetch_listings(address: str, bbl: str) -> list[Record]:
    """Attempt HTTP fetch; fall back to Playwright if blocked."""
    try:
        return _http_fetch(address, bbl)
    except SourceError:
        try:
            return _playwright_fetch(address, bbl)
        except Exception as e:
            raise SourceError(f"StreetEasy listing fetch failed for {address}: {e}") from e


def _http_fetch(address: str, bbl: str) -> list[Record]:
    try:
        with httpx.Client(headers=_HEADERS, timeout=20, follow_redirects=True) as client:
            resp = client.get(
                "https://streeteasy.com/for-rent/nyc",
                params={"q": address, "sort_by": "listed_desc"},
            )
            if resp.status_code in (403, 429):
                raise SourceError("StreetEasy blocked — need Playwright fallback")
            resp.raise_for_status()
            return _parse_html_listings(resp.text, bbl, address)
    except httpx.HTTPError as e:
        raise SourceError(f"StreetEasy HTTP error: {e}") from e


def _parse_html_listings(html: str, bbl: str, address: str) -> list[Record]:
    records = []
    today = date.today()

    # Try to extract from __NEXT_DATA__ JSON (StreetEasy is Next.js)
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
    if m:
        try:
            data = json.loads(m.group(1))
            listings_raw = _dig(data, ["props", "pageProps", "listings"]) or []
            if not listings_raw:
                listings_raw = _dig(data, ["props", "pageProps", "searchResults", "listings"]) or []
            for item in listings_raw[:10]:
                price = item.get("price") or item.get("asking_price")
                if not price:
                    continue
                beds = item.get("bedrooms") or item.get("beds") or 1
                unit = item.get("unit") or item.get("apt") or None
                records.append(Record(
                    entity_id=bbl,
                    record_type=record_type,
                    source=source_id,
                    data={
                        "bbl":          bbl,
                        "address":      address,
                        "unit":         str(unit) if unit else None,
                        "listed_rent":  float(price),
                        "bedrooms":     int(beds),
                        "listing_date": str(today),
                        "source":       source_id,
                    },
                    fetched_at=datetime.utcnow(),
                ))
            if records:
                return records
        except (json.JSONDecodeError, KeyError):
            pass

    # Fallback: regex scrape price strings from raw HTML
    prices = _PRICE_RE.findall(html)
    seen: set[float] = set()
    for price_str in prices[:8]:
        price = float(price_str.replace(",", ""))
        if price < 500 or price > 30000 or price in seen:
            continue
        seen.add(price)
        idx = html.find(price_str)
        context = html[max(0, idx - 200):idx + 200]
        beds = _parse_bedrooms(context)
        records.append(Record(
            entity_id=bbl,
            record_type=record_type,
            source=source_id,
            data={
                "bbl":          bbl,
                "address":      address,
                "unit":         None,
                "listed_rent":  price,
                "bedrooms":     beds,
                "listing_date": str(today),
                "source":       source_id,
            },
            fetched_at=datetime.utcnow(),
        ))
    return records


def _playwright_fetch(address: str, bbl: str) -> list[Record]:
    from playwright.sync_api import sync_playwright

    today = date.today()
    records = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            user_agent=_HEADERS["User-Agent"],
            viewport={"width": 1280, "height": 800},
        )
        page = ctx.new_page()
        try:
            page.goto(
                f"https://streeteasy.com/for-rent/nyc?q={address}",
                timeout=30000,
                wait_until="domcontentloaded",
            )
            page.wait_for_timeout(3000)

            prices = page.query_selector_all('[data-testid="listing-price"], .price, .Price')
            beds_els = page.query_selector_all('[data-testid="beds-baths"], .bedroom, .Bedroom')

            seen: set[float] = set()
            for i, el in enumerate(prices[:8]):
                text = el.inner_text()
                price = _parse_price(text)
                if price is None or price in seen:
                    continue
                seen.add(price)
                beds_text = beds_els[i].inner_text() if i < len(beds_els) else ""
                beds = _parse_bedrooms(beds_text)
                records.append(Record(
                    entity_id=bbl,
                    record_type=record_type,
                    source=source_id,
                    data={
                        "bbl":          bbl,
                        "address":      address,
                        "unit":         None,
                        "listed_rent":  price,
                        "bedrooms":     beds,
                        "listing_date": str(today),
                        "source":       source_id,
                    },
                    fetched_at=datetime.utcnow(),
                ))
        finally:
            browser.close()

    return records


def _dig(d: dict, keys: list[str]):
    for k in keys:
        if not isinstance(d, dict):
            return None
        d = d.get(k)
    return d
