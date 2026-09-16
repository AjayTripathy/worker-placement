"""Tier 1 open-web discovery connector.

The DD framework's other connectors (Austin permits, FMCSA, USPTO, EDGAR, etc.)
are Tier 2/3 — they verify a specific fact you already know to query. This
connector is Tier 1: given an entity name, it asks the open web what facts
are publicly disclosed *about* that entity (addresses, partners, customers,
prior names, news, real estate listings) so downstream verifiers have
something concrete to test.

Lesson driving this: on the AHC deal we queried Tier 2/3 registries by entity
name and got false negatives — because the deck didn't include the factory's
specific street address and tenants don't appear in permit databases. A simple
search for `"AHC factory" Austin` would have surfaced LoopNet's listing for
4422 Supply Ct (the actual factory address). With the address in hand, Tier 2/3
queries become productive (address-keyed permit search returns 12 permits).

Sources queried in priority order:
  1. Brave Search HTML (primary — DDG is now bot-blocking aggressively)
  2. DuckDuckGo HTML (fallback)

Operational reality: both DDG and Brave will rate-limit aggressive automation
(HTTP 429 / 202 interstitial). For production deployments, plug in:
  - Brave Search API ($5 / 1k queries, key-gated, no rate limits)
  - SerpAPI / Apify / similar wrappers (~$50-100/mo for moderate volume)
  - Or rotate through residential proxies
The connector's _brave_search and _ddg_search functions are pure HTML parsers
and will work against any equivalent HTML response from those sources.

Output: ConnectorObservations of the form:
  - attribute = "discovery_address" / "discovery_related_entity" /
                "discovery_url:<category>" / "discovery_meta"
  - value = the surfaced fact
  - source_url = the open-web result URL where it was found
"""

from __future__ import annotations

# Knowledge-graph dispatch contract (see knowledge_graph/dispatch.py) — added 2026-07-29 gap-close.
APPLIES_TO = {
    "kind": 'helper',
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": [],
    "asset_classes": ['corporate_ipo_dd'],
    "applies_universally": False,
    "summary": 'Tier-1 open-web discovery plumbing used by verifier agents.',
}

import json
import os
import re
import urllib.parse
from functools import lru_cache
from pathlib import Path
from typing import Iterable

from .base import (
    BaseConnector,
    ConnectorRequest,
    ConnectorResult,
    ConnectorObservation,
    ErrorKind,
    safe_get,
)


DDG_HTML = "https://html.duckduckgo.com/html/"
BRAVE_HTML = "https://search.brave.com/search"
FIRECRAWL_SEARCH = "https://api.firecrawl.dev/v2/search"


@lru_cache(maxsize=1)
def _firecrawl_api_key() -> str | None:
    """Key-gated, Google-grade search backend. Read from env first, then a
    0600 home-dir file (mirrors the ~/.anthropic_api_key pattern) so the key is
    never committed to the repo. Absent key -> connector silently falls back to
    the HTML-scraping engines below."""
    key = os.environ.get("FIRECRAWL_API_KEY")
    if key:
        return key.strip()
    keyfile = Path.home() / ".firecrawl_api_key"
    if keyfile.exists():
        return keyfile.read_text().strip() or None
    return None


def _firecrawl_search(query: str, limit: int = 8) -> tuple[list[dict], str | None, str | None]:
    """Primary search engine. Unlike Brave/DDG/Mojeek (IP-rate-limited HTML
    scrapers), Firecrawl is an authenticated API with deep index coverage — it
    surfaces small/early-stage entities the HTML engines miss (e.g. a startup's
    factory address in the TX TDLR registry). Returns the engine's standard
    (results, error_kind, error_detail) triple with {url,title,snippet} dicts."""
    key = _firecrawl_api_key()
    if not key:
        return [], ErrorKind.UNSUPPORTED, "no FIRECRAWL_API_KEY"
    payload = json.dumps({"query": query, "limit": limit}).encode()
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    try:
        try:
            from curl_cffi import requests as _creq
            r = _creq.post(FIRECRAWL_SEARCH, headers=headers, data=payload, timeout=40.0)
        except ImportError:
            import requests as _req
            r = _req.post(FIRECRAWL_SEARCH, headers=headers, data=payload, timeout=40.0)
    except Exception as e:  # noqa: BLE001 — normalize any transport error
        return [], ErrorKind.NETWORK, f"firecrawl: {e}"
    if r.status_code in (401, 403):
        return [], ErrorKind.AUTH, f"firecrawl http {r.status_code}"
    if r.status_code == 429:
        return [], ErrorKind.RATE_LIMIT, "firecrawl http 429"
    if r.status_code >= 400:
        return [], ErrorKind.UNKNOWN, f"firecrawl http {r.status_code}: {r.text[:120]}"
    try:
        body = r.json()
    except Exception as e:  # noqa: BLE001
        return [], ErrorKind.UNKNOWN, f"firecrawl bad json: {e}"
    data = body.get("data") if isinstance(body, dict) else None
    # /search may return data as a flat list or {"web": [...], "news": [...]}.
    items = data if isinstance(data, list) else (data or {}).get("web", []) if isinstance(data, dict) else []
    results = []
    for it in items:
        u = it.get("url")
        if not u:
            continue
        results.append({
            "url": u,
            "title": (it.get("title") or "").strip(),
            "snippet": (it.get("description") or it.get("snippet") or "").strip(),
        })
    if not results:
        return [], ErrorKind.NOT_FOUND, "firecrawl returned no results"
    return results, None, None


# ─── Browser fingerprint ────────────────────────────────────────────────────
# Cloudflare / Brave / most gov + enterprise WAFs gate on the FULL client-hint +
# fetch-metadata header set, not just User-Agent. A bare UA earns a 429 / 202
# bot-challenge — which then arrives brotli-encoded and trips
# "content-encoding: br, but failed to decode it". A complete, INTERNALLY
# CONSISTENT desktop-Chrome fingerprint clears the challenge. Two hard
# constraints: (1) the Sec-Ch-Ua brand versions must match the UA's Chrome
# major; (2) advertise only gzip/deflate, NOT br — the runtime has no
# guaranteed brotli decoder, so accepting br re-creates the decode failure.
_CHROME_MAJOR = "131"
_CHROME_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    f"Chrome/{_CHROME_MAJOR}.0.0.0 Safari/537.36"
)


def _chrome_headers(referer: str | None = None) -> dict:
    """A coherent desktop-Chrome request fingerprint. Pass `referer` when the
    fetch should look like a search-form submission (Sec-Fetch-Site=same-origin);
    omit it for a directly-typed navigation (Sec-Fetch-Site=none)."""
    h = {
        "User-Agent": _CHROME_UA,
        "Accept": (
            "text/html,application/xhtml+xml,application/xml;q=0.9,"
            "image/avif,image/webp,image/apng,*/*;q=0.8,"
            "application/signed-exchange;v=b3;q=0.7"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate",
        "Sec-Ch-Ua": (
            f'"Google Chrome";v="{_CHROME_MAJOR}", '
            f'"Chromium";v="{_CHROME_MAJOR}", '
            '"Not_A Brand";v="24"'
        ),
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"macOS"',
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "max-age=0",
    }
    if referer:
        h["Referer"] = referer
        h["Sec-Fetch-Site"] = "same-origin"
    else:
        h["Sec-Fetch-Site"] = "none"
    return h


# ─── Regex patterns for fact extraction ─────────────────────────────────────
# US street address pattern. Conservative: requires street number + street name
# + a street type word, then optional ", City, ST 12345".
ADDRESS_RE = re.compile(
    r"\b(\d{1,6}\s+[A-Z][\w\.\' ]{2,60}?\s+(?:Rd|Road|St|Street|Ave|Avenue|Blvd|Boulevard|Dr|Drive|Way|Ln|Lane|Ct|Court|Pl|Place|Pkwy|Parkway|Hwy|Highway|Ste|Suite|Unit)\b\.?(?:\s*(?:#|Ste\.?|Suite|Unit)\s*\w+)?(?:\s*,?\s*[A-Z][\w\s\.]{2,30}?)?(?:\s*,?\s*[A-Z]{2}\s+\d{5}(?:-\d{4})?)?)",
    re.IGNORECASE,
)
# US zip code (TX-friendly but works anywhere)
ZIP_RE = re.compile(r"\b(\d{5})(?:-\d{4})?\b")
# DOLLAR amounts
USD_RE = re.compile(r"\$\s?(\d{1,3}(?:,\d{3})*(?:\.\d+)?(?:\s*[MmBbKk])?)")
# Common business naming patterns surfaced as partners/customers
ENTITY_RE = re.compile(r"\b([A-Z][A-Za-z0-9&\.,\- ]{3,60}?(?:LLC|Inc\.?|Corp\.?|LP|LLP|Ltd\.?|Group|Holdings|Partners|Capital|Co\.?))\b")


MOJEEK_HTML = "https://www.mojeek.com/search"


def _http_get(url: str, headers: dict, timeout: float = 20.0):
    """Fetch with a real Chrome fingerprint at the TRANSPORT layer.

    `requests` has a fixed TLS/JA3 + HTTP-2 frame fingerprint that Cloudflare /
    Brave / DDG detect and challenge regardless of how perfect the HTTP headers
    are. curl_cffi's `impersonate` replays an actual Chrome TLS ClientHello +
    HTTP-2 SETTINGS, which is what those WAFs actually fingerprint. We prefer it
    and fall back to plain requests only if it is not installed.

    Returns (response_like, error_kind, error_detail) — response has `.text` and
    `.status_code`, matching safe_get's contract.
    """
    try:
        from curl_cffi import requests as _creq
        try:
            r = _creq.get(url, headers=headers, impersonate="chrome131", timeout=timeout)
        except Exception as e:  # noqa: BLE001 — normalize any transport error
            return None, ErrorKind.NETWORK, f"curl_cffi: {e}"
    except ImportError:
        import requests as _req
        try:
            r = _req.get(url, headers=headers, timeout=timeout)
        except Exception as e:  # noqa: BLE001
            return None, ErrorKind.NETWORK, f"requests: {e}"
    sc = r.status_code
    if sc in (401, 403):
        return None, ErrorKind.AUTH, f"http {sc}"
    if sc == 404:
        return None, ErrorKind.NOT_FOUND, "http 404"
    if sc in (202, 429):
        return None, ErrorKind.RATE_LIMIT, f"http {sc} (bot challenge): {r.text[:120]}"
    if sc >= 500:
        return None, ErrorKind.NETWORK, f"http {sc}: server error"
    if sc >= 400:
        return None, ErrorKind.UNKNOWN, f"http {sc}: {r.text[:120]}"
    return r, None, None


def _brave_search(query: str, headers: dict) -> tuple[list[dict], str | None, str | None]:
    """Brave Search HTML — primary source. DDG is now bot-blocking aggressively
    (HTTP 202 with interstitial page); Brave still serves real result HTML."""
    url = f"{BRAVE_HTML}?q={urllib.parse.quote_plus(query)}"
    r, ek, ed = _http_get(url, headers=headers)
    if r is None:
        return [], ek, ed
    text = r.text
    # Permissive URL extract — Brave's SPA shell embeds real result URLs as
    # plain href attributes. Filter out Brave-internal/CDN domains.
    SKIP_DOMAINS = ("search.brave", "brave.com", "brave.app", "cdn.", "imgs.", "tiles.", "hackerone")
    seen = set()
    results = []
    for m in re.finditer(r'href="(https?://[^"]+)"', text):
        u = m.group(1)
        if any(b in u for b in SKIP_DOMAINS):
            continue
        if u in seen:
            continue
        seen.add(u)
        # Try to find a title nearby — look 100 chars after for a >text< pattern
        idx = m.end()
        title_m = re.search(r"^[^<]*>([^<]{3,200})</a>", text[idx:idx+500])
        title = title_m.group(1).strip() if title_m else ""
        # And a snippet shortly after
        snip_m = re.search(r"<(?:p|div|span)[^>]*>([^<]{20,400})</", text[idx:idx+2000])
        snippet = snip_m.group(1).strip() if snip_m else ""
        results.append({"url": u, "title": title, "snippet": snippet})
        if len(results) >= 30:
            break
    return results, None, None


def _ddg_search(query: str, headers: dict) -> tuple[list[dict], str | None, str | None]:
    """DDG HTML — fallback only; DDG aggressively returns HTTP 202 + interstitial
    for non-browser clients. Kept as fallback in case Brave goes down."""
    url = f"{DDG_HTML}?q={urllib.parse.quote_plus(query)}"
    r, ek, ed = _http_get(url, headers=headers)
    if r is None:
        return [], ek, ed
    pattern = re.compile(
        r'<a[^>]*class="result__a"[^>]*href="([^"]+)"[^>]*>([^<]+)</a>'
        r'.*?<a[^>]*class="result__snippet"[^>]*>([^<]*)</a>',
        re.DOTALL,
    )
    results = []
    for m in pattern.finditer(r.text):
        url_raw, title, snippet = m.group(1), m.group(2), m.group(3)
        ud = re.search(r"uddg=([^&]+)", url_raw)
        if ud:
            url_raw = urllib.parse.unquote(ud.group(1))
        results.append({"url": url_raw, "title": title.strip(), "snippet": snippet.strip()})
    return results, None, None


def _mojeek_search(query: str, headers: dict) -> tuple[list[dict], str | None, str | None]:
    """Mojeek HTML — independent crawler, automation-tolerant. Serves real
    result HTML when Brave/DDG IP-rate-limit. Organic results are <a> anchors
    carrying a 'title'-flavored class with a direct (un-redirected) href."""
    url = f"{MOJEEK_HTML}?q={urllib.parse.quote_plus(query)}"
    r, ek, ed = _http_get(url, headers=headers)
    if r is None:
        return [], ek, ed
    text = r.text
    results = []
    seen = set()
    # Direct result anchors: <a ... class="...title..." href="https://...">Title</a>
    for m in re.finditer(
        r'<a[^>]*href="(https?://[^"]+)"[^>]*class="[^"]*title[^"]*"[^>]*>(.*?)</a>'
        r'|<a[^>]*class="[^"]*title[^"]*"[^>]*href="(https?://[^"]+)"[^>]*>(.*?)</a>',
        text, re.DOTALL,
    ):
        u = m.group(1) or m.group(3)
        title = re.sub(r"<[^>]+>", "", (m.group(2) or m.group(4) or "")).strip()
        if not u or "mojeek.com" in u or u in seen:
            continue
        seen.add(u)
        # Snippet: first <p class="s"> shortly after the anchor
        snip_m = re.search(r"<p class=\"s\">(.*?)</p>", text[m.end():m.end() + 1500], re.DOTALL)
        snippet = re.sub(r"<[^>]+>", "", snip_m.group(1)).strip() if snip_m else ""
        results.append({"url": u, "title": title, "snippet": snippet})
    return results, None, None


def _decode_url_for_addresses(url: str) -> list[str]:
    """Some result URLs (Google Maps, etc.) contain URL-encoded addresses in
    query parameters. Decode and look for address patterns."""
    try:
        decoded = urllib.parse.unquote(url)
        # Strip protocol/domain to focus on path + query
        m = re.search(r"\?(.+)$", decoded)
        haystack = m.group(1) if m else decoded
        # Replace + with space (URL encoding)
        haystack = haystack.replace("+", " ")
        return [a.strip() for a in ADDRESS_RE.findall(haystack)]
    except Exception:
        return []


def _extract_facts(results: list[dict], entity_name: str) -> list[ConnectorObservation]:
    """Parse search-result snippets + titles for derivable facts."""
    obs: list[ConnectorObservation] = []
    en_lower = entity_name.lower()

    for r in results:
        text_blob = f"{r.get('title','')} {r.get('snippet','')}"
        url = r.get("url", "")

        # 1a) Addresses in title/snippet (only if entity is mentioned to filter noise)
        entity_in_blob = (
            en_lower in text_blob.lower()
            or any(tok.lower() in text_blob.lower() for tok in entity_name.split() if len(tok) > 3)
        )
        if entity_in_blob:
            for m in ADDRESS_RE.finditer(text_blob):
                addr = m.group(1).strip().rstrip(",.")
                if len(addr) < 10 or len(addr) > 120:
                    continue
                obs.append(ConnectorObservation(
                    attribute="discovery_address",
                    value=addr,
                    source_url=url,
                    extra={"snippet": text_blob[:300]},
                ))

        # 1b) Addresses encoded INSIDE the result URL itself (Google Maps,
        # commercial real-estate listing slugs, etc.). Search engines often
        # return URLs that contain the entity's address in the query string
        # even if no page snippet does.
        for addr in _decode_url_for_addresses(url):
            if len(addr) < 10 or len(addr) > 120:
                continue
            obs.append(ConnectorObservation(
                attribute="discovery_address",
                value=addr,
                source_url=url,
                extra={"source": "url_decoded", "title": r.get("title","")[:200]},
            ))
        # Also: extract street-number + street-name from URL paths like
        # /4422-supply-ct-austin-tx-78744/ which commercial RE listings use
        path_addr = re.findall(
            r"/(\d{2,6}[-_](?:[a-z][a-z\-_]{2,40}[-_])(?:rd|st|ave|blvd|dr|way|ln|ct|pkwy|hwy|pl|trl|cir)[-_a-z\d]+)",
            url.lower(),
        )
        for slug in path_addr:
            normalized = slug.replace("-", " ").replace("_", " ").title()
            obs.append(ConnectorObservation(
                attribute="discovery_address",
                value=normalized,
                source_url=url,
                extra={"source": "url_path_slug"},
            ))
        # 2) Zip codes (only if no address pattern matched in this blob)
        if not any(o.attribute == "discovery_address" and o.source_url == url for o in obs):
            for m in ZIP_RE.finditer(text_blob):
                obs.append(ConnectorObservation(
                    attribute="discovery_zip",
                    value=m.group(1),
                    source_url=url,
                    extra={"snippet": text_blob[:200]},
                ))
        # 3) Surfaced URL itself (real estate listing, business directory, news)
        # Capture domain category hint
        domain = re.sub(r"^(?:https?://)?(?:www\.)?", "", url).split("/")[0] if url else ""
        category = None
        if domain:
            if "loopnet.com" in domain or "showcase.com" in domain:
                category = "commercial_real_estate_listing"
            elif "linkedin.com" in domain:
                category = "linkedin_profile_or_company"
            elif "indeed.com" in domain or "glassdoor.com" in domain or "ziprecruiter.com" in domain:
                category = "job_listing"
            elif "bizapedia.com" in domain or "cortera.com" in domain or "superpages.com" in domain or "chamberofcommerce.com" in domain:
                category = "business_directory"
            elif "uspto.gov" in domain or "trademark" in domain:
                category = "trademark_filing"
            elif "techcrunch.com" in domain or "businesswire.com" in domain or "prnewswire.com" in domain:
                category = "press_release_or_news"
            elif domain.endswith(".gov"):
                category = "gov_record"
        if category:
            obs.append(ConnectorObservation(
                attribute=f"discovery_url:{category}",
                value=url,
                source_url=url,
                extra={"title": r.get("title", "")[:200], "snippet": text_blob[:300]},
            ))
        # 4) Other entity names mentioned (potential partners, GCs, customers)
        for m in ENTITY_RE.finditer(text_blob):
            ent = m.group(1).strip()
            if entity_name.lower() in ent.lower():
                continue
            if any(tok in ent.lower() for tok in ("page not found", "click here", "search results")):
                continue
            obs.append(ConnectorObservation(
                attribute="discovery_related_entity",
                value=ent,
                source_url=url,
                extra={"snippet": text_blob[:200]},
            ))
    # Dedupe by (attribute, value)
    seen = set()
    unique = []
    for o in obs:
        key = (o.attribute, str(o.value)[:200])
        if key in seen:
            continue
        seen.add(key)
        unique.append(o)
    return unique


class WebDiscoveryConnector(BaseConnector):
    """Open-web discovery for an entity. Tier 1.

    Inputs (via ConnectorRequest):
      - entity_name: required
      - extra.claim_keywords: optional list of strings to OR into the query
                              (e.g. ["factory", "address"], ["customers"], ["fleet"])

    Returns observations with attribute prefixes "discovery_*". Downstream
    Tier 2/3 connectors should consume these to derive concrete queries.
    """
    source_id = "web_discovery"
    rate_limit_per_min = 30
    user_agent = _CHROME_UA

    def query(self, request: ConnectorRequest) -> ConnectorResult:
        if not request.entity_name:
            return self._fail(request, ErrorKind.UNSUPPORTED, "entity_name required")

        # Two query modes:
        #  - ENTITY mode (default): exact-phrase the entity name and OR in keywords.
        #    Right when entity_name is a precise proper noun ("Acme Modular LLC").
        #  - VERBATIM mode (extra.verbatim_query): send entity_name as-is, no quote
        #    wrap, no keyword append. The Stage-1.5 resolver composes a full
        #    natural-language query ("American Housing Corp factory Austin TX
        #    address"); quote-wrapping that whole string forces an exact-phrase
        #    match that returns nothing, which starved the AHC factory resolution.
        if (request.extra or {}).get("verbatim_query"):
            query = request.entity_name.strip()
        else:
            keywords: Iterable[str] = (request.extra or {}).get("claim_keywords") or []
            kw_str = " ".join(f'"{k}"' if " " in k else k for k in keywords)
            query = f'"{request.entity_name}"'
            if kw_str:
                query += f" {kw_str}"

        self._throttle()

        # Engine chain, best backend first. Firecrawl is a key-gated API with
        # deep index coverage and no IP rate-limiting — it is the primary source
        # whenever a key is configured. The HTML scrapers below backstop it (and
        # cover the no-key case): curl_cffi's Chrome impersonation supplies the
        # TLS/HTTP-2 fingerprint and _chrome_headers the matching HTTP headers +
        # Referer, but Brave & DDG still IP-rate-limit aggressively, so Mojeek
        # (independent crawler, automation-tolerant) backstops them.
        results: list[dict] = []
        used_source = None
        ek = ed = None

        results, ek, ed = _firecrawl_search(query)
        if results:
            used_source = "firecrawl"
        else:
            engines = [
                ("brave", _brave_search, "https://search.brave.com/"),
                ("duckduckgo", _ddg_search, "https://duckduckgo.com/"),
                ("mojeek", _mojeek_search, "https://www.mojeek.com/"),
            ]
            for name, fn, referer in engines:
                results, ek, ed = fn(query, headers=_chrome_headers(referer))
                if results:
                    used_source = name
                    break

        if not results:
            return self._fail(
                request,
                ek or ErrorKind.NOT_FOUND,
                ed or "no results from Firecrawl, Brave, DDG, or Mojeek",
            )

        observations = _extract_facts(results, request.entity_name)

        # Add a meta observation so downstream knows the search ran and what query was used
        observations.insert(0, ConnectorObservation(
            attribute="discovery_meta",
            value={
                "query": query,
                "n_raw_results": len(results),
                "n_facts_extracted": len(observations),
                "search_source": used_source,
                # Raw hits so an LLM consumer (entity_resolution web_search) can
                # reason over snippets directly, instead of being limited to the
                # regex-extracted facts _extract_facts could pattern-match. Many
                # useful answers (a company's address stated in prose) never trip
                # the address regex but are obvious to a reader.
                "raw_results": results[:10],
            },
            source_url=None,
        ))
        return self._ok(request, observations, raw=str(results)[:2048])
