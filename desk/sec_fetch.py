"""Full-fingerprint sec.gov fetcher — the working recipe, wired 2026-08-11.

Every court bench this week reported sec.gov 403s; data.sec.gov accepts a plain UA but
www.sec.gov/Archives requires the complete Chrome client-hint set INCLUDING
Sec-Fetch-Site: cross-site and a Referer (verified live on FVRR 6-K exhibit fetch,
2026-08-11: partial set -> 403, full set -> 200). Memory: gov/enterprise sites check
Sec-Ch-Ua / Sec-Fetch-* / Referer, not just User-Agent.

Usage:  from desk.sec_fetch import fetch
        html = fetch("https://www.sec.gov/Archives/edgar/data/...")
"""
from __future__ import annotations
import subprocess

_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36")

_HEADERS = [
    ("User-Agent", _UA),
    ("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),
    ("Accept-Language", "en-US,en;q=0.9"),
    ("Sec-Ch-Ua", '"Not)A;Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"'),
    ("Sec-Ch-Ua-Mobile", "?0"),
    ("Sec-Ch-Ua-Platform", '"macOS"'),
    ("Sec-Fetch-Dest", "document"),
    ("Sec-Fetch-Mode", "navigate"),
    ("Sec-Fetch-Site", "cross-site"),          # the load-bearing header (2026-08-11)
    ("Sec-Fetch-User", "?1"),
    ("Referer", "https://www.sec.gov/cgi-bin/browse-edgar"),
    ("Upgrade-Insecure-Requests", "1"),
]


class SecFetchError(RuntimeError):
    pass


def fetch(url: str, timeout: int = 30) -> str:
    """Fetch a sec.gov URL with the full Chrome fingerprint. Raises SecFetchError on
    non-200 so callers surface DEGRADED loudly instead of caching a 403 body."""
    cmd = ["curl", "-s", "--max-time", str(timeout), "--compressed",
           "-w", "\n%{http_code}", url]
    for k, v in _HEADERS:
        cmd += ["-H", f"{k}: {v}"]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 10)
    body, _, code = r.stdout.rpartition("\n")
    if code.strip() != "200":
        raise SecFetchError(f"sec.gov {code.strip() or 'no-response'} for {url}")
    return body
