"""hubs_breeze_tripwires — the three July pre-print tripwires for the HUBS Aug-5 decision (from the 2026-07-01
Breeze evidence sweep; full rubric in desk/data/edge_classifications/HUBS.json .breeze_evidence).

  A. CONSUMPTION CHATTER — community.hubspot.com credits/billing thread velocity: continued new credit-burn /
     billing-surprise posts = live consumption (bullish); sudden silence = usage stalling (bearish).
  B. PRICING ITERATION — the credits knowledge page + product catalog: another packaging/$-per-credit change
     before Aug-5 = active monetization tuning (bullish confirm). Detected by normalized-text hash diff.
  C. MONETIZATION HIRING — careers listings mentioning monetization/credits/pricing-strategy: req count
     growing = credits treated as a durable revenue line.

Each run diffs against data/hubs_tripwires_state.json and FLAGs deltas (the generic extractor lifts FLAG lines
to the signal feed). A blocked/JS-walled source prints DEGRADED — never a fabricated reading. AUTO-RETIRES
after 2026-08-05 (the print). READ-ONLY.

  python3 verticals/deep_value/hubs_breeze_tripwires.py
"""
from __future__ import annotations
import json, re, hashlib, datetime, urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
STATE = HERE / "data" / "hubs_tripwires_state.json"
PRINT_DATE = datetime.date(2026, 8, 5)
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36", "Accept-Language": "en-US,en;q=0.9"}

SOURCES = {
    # A: community boards / search pages that list threads (thread-ish links counted by regex)
    "community_credits": "https://community.hubspot.com/t5/forums/searchpage/tab/message?q=credits%20billing&collapse_discussion=true",
    # B: pricing/catalog pages (hash-diffed)
    "credits_kb": "https://knowledge.hubspot.com/account-management/hubspot-credits",
    "product_catalog": "https://legal.hubspot.com/hubspot-product-and-services-catalog",
    # C: careers search (may be a JS shell — degrade honestly)
    "careers_monetization": "https://www.hubspot.com/careers/jobs?q=monetization",
}


def _get(url: str) -> str | None:
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.read().decode("utf-8", "ignore")
    except Exception:
        return None


def _get_browser(url: str, headed: bool = False, wait_ms: int = 4500) -> str | None:
    """Tiered browser fetch (real-Chrome pattern): headless passes knowledge/careers; the Cloudflare-walled
    community board needs HEADED (same precedent as the daily TikTok poll)."""
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            b = p.chromium.launch(channel="chrome", headless=not headed)
            pg = b.new_page()
            pg.goto(url, wait_until="domcontentloaded", timeout=35000)
            pg.wait_for_timeout(wait_ms)
            html = pg.content()
            b.close()
        if "Just a moment" in html[:4000] and not headed:
            return _get_browser(url, headed=True)          # escalate once past Cloudflare
        return html if "Just a moment" not in html[:4000] else None
    except Exception:
        return None


def _norm_hash(html: str) -> str:
    """Hash of the visible-ish text with volatile junk stripped (scripts, csrf tokens, timestamps)."""
    t = re.sub(r"<script.*?</script>|<style.*?</style>", " ", html, flags=re.S | re.I)
    t = re.sub(r"<[^>]+>", " ", t)
    t = re.sub(r"(csrf|token|nonce|timestamp|__[a-z]+)[\"'=:\s\w-]{0,60}", " ", t, flags=re.I)
    t = re.sub(r"\s+", " ", t).strip().lower()
    return hashlib.sha256(t.encode()).hexdigest()[:16]


def probe() -> dict:
    out = {}
    # A — thread velocity: count message links on the community search page (Cloudflare -> browser tier)
    html = _get_browser(SOURCES["community_credits"], wait_ms=8000)   # Khoros renders results via XHR; urllib/quick loads give a false 0
    if html:
        threads = len(set(re.findall(r'href="(/t5/[^"]*/m-p/\d+[^"]*)"', html)))
        if threads < 3:
            html = None   # results pane didn't render -> unreliable, degrade rather than baseline a false 0
    if html:
        titles = re.findall(r'<a[^>]*class="[^"]*message-subject[^"]*"[^>]*>([^<]{10,90})</a>', html)[:5] or \
                 re.findall(r'/m-p/\d+[^>]*>([^<]{15,90})<', html)[:5]
        out["community_credits"] = {"thread_links": threads, "sample_titles": [t.strip() for t in titles]}
    else:
        out["community_credits"] = {"degraded": "fetch blocked/failed — no reading (do NOT infer silence)"}
    # B — pricing iteration hashes
    for k in ("credits_kb", "product_catalog"):
        html = _get(SOURCES[k]) or _get_browser(SOURCES[k])
        out[k] = {"hash": _norm_hash(html), "bytes": len(html)} if html else {"degraded": "fetch blocked/failed"}
    # C — careers: count monetization-ish mentions; JS shells return ~0 real listings -> degraded
    html = _get(SOURCES["careers_monetization"])
    best = 0
    if html:
        best = len(re.findall(r"monetization|pricing strateg|credits? pricing", html, flags=re.I))
    if best <= 2:   # urllib shell had no rendered text -> browser tier
        hb = _get_browser(SOURCES["careers_monetization"], wait_ms=7000)
        if hb:
            best = max(best, len(re.findall(r"monetization|pricing strateg|credits? pricing", hb, flags=re.I)))
    if best > 2:
        out["careers_monetization"] = {"mention_count": best}   # DELTA metric: req growth -> mention growth (level is noisy, change is the signal)
    else:
        out["careers_monetization"] = {"degraded": "no rendered listings in either tier — check LinkedIn manually"}
    return out


def main():
    today = datetime.date.today()
    if today > PRINT_DATE:
        print(f"=== HUBS BREEZE TRIPWIRES — RETIRED (print {PRINT_DATE} has passed; resolve the calibration "
              f"entry + grade the Aug-5 rubric instead) ===")
        return
    days = (PRINT_DATE - today).days
    prev = json.loads(STATE.read_text()) if STATE.exists() else {}
    cur = probe()

    print(f"=== HUBS BREEZE TRIPWIRES  {today}  (Aug-5 print in {days}d; rubric in HUBS.json .breeze_evidence) ===")
    flags = []
    # A: velocity delta
    a, pa = cur.get("community_credits", {}), prev.get("community_credits", {})
    if "degraded" in a:
        print(f"  A consumption-chatter: DEGRADED — {a['degraded']}")
    else:
        d = a["thread_links"] - pa.get("thread_links", a["thread_links"])
        print(f"  A consumption-chatter: {a['thread_links']} credit/billing threads on the search page "
              f"({'Δ%+d vs last run' % d if pa else 'baseline set'})")
        if pa and d >= 3:
            flags.append(f">>> FLAG HUBS-TRIPWIRE A: credit/billing chatter UP (+{d} threads) — consumption live, bullish confirm")
        if pa and d <= -3:
            flags.append(f">>> FLAG HUBS-TRIPWIRE A: credit/billing chatter DOWN ({d}) — possible usage stall, bearish tell; verify manually")
    # B: pricing iteration
    for k, label in (("credits_kb", "credits knowledge page"), ("product_catalog", "product catalog")):
        c, p = cur.get(k, {}), prev.get(k, {})
        if "degraded" in c:
            print(f"  B pricing-iteration ({label}): DEGRADED — {c['degraded']}")
        elif p.get("hash") and c["hash"] != p["hash"]:
            print(f"  B pricing-iteration ({label}): CHANGED since last run")
            flags.append(f">>> FLAG HUBS-TRIPWIRE B: {label} CHANGED pre-print — likely packaging/pricing iteration (bullish tuning signal); diff it manually")
        else:
            print(f"  B pricing-iteration ({label}): {'unchanged' if p.get('hash') else 'baseline set'} (hash {c['hash']})")
    # C: hiring
    c, p = cur.get("careers_monetization", {}), prev.get("careers_monetization", {})
    if "degraded" in c:
        print(f"  C monetization-hiring: DEGRADED — {c['degraded']}")
    else:
        d = c["mention_count"] - p.get("mention_count", c["mention_count"])
        print(f"  C monetization-hiring: {c['mention_count']} monetization/pricing mentions (rendered page) "
              f"({'Δ%+d' % d if p else 'baseline set'})")
        if p and d > 0:
            flags.append(f">>> FLAG HUBS-TRIPWIRE C: monetization hiring mentions UP (+{d}) — durable-revenue-line signal")
    for f in flags:
        print("  " + f)
    if not flags:
        print("  no tripwire deltas this run" + (" (baselines established)" if not prev else ""))
    STATE.write_text(json.dumps(cur, indent=1))
    print(f"[-> {STATE.name}]  decision rubric: grade Aug-5 on SEQUENTIAL credit consumption + NRR direction; "
          f"missing standalone Breeze $ARR is NOT failure; scale to 6-7% only if tripwires stayed clean AND the print confirms.")


if __name__ == "__main__":
    main()
