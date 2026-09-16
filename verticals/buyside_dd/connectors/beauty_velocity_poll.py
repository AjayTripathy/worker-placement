"""beauty_velocity_poll — DAILY virality velocity poll via a real browser (Playwright). SCAFFOLD.

WHY: virality moves in DAYS, so monthly/weekly agent WebSearch scans are too slow to run daily.
GOAL: a scheduled browser scrape gives a DAILY trend/product-velocity feed for $0 agent tokens.

REALITY CHECK (probed 2026-06-26 — READ THIS before trusting the output):
  - TikTok Creative Center LOADS in a real browser (not Cloudflare-blocked) BUT the data is AUTH-GATED:
    without a TikTok Business login you see only the TOP-3 *general* hashtags (#happyfathersday etc.),
    not the beauty-industry filter or the full top-20 / Top-Products. -> To get the rich beauty signal,
    run with a PERSISTED LOGGED-IN session (storage_state from a one-time TikTok Business login — the
    'land-first-for-session-cookie' playbook in reference_browser_automation_gated_portals). Pass
    storage_state path via env COSMO_TT_AUTH. WITHOUT it this poller is near-empty (by design, honestly).
  - Amazon Movers&Shakers throws a Prime-Day interstitial + lazy product list -> needs interstitial
    dismissal + scroll-to-load (TODO); currently low-yield.
  - Sephora/Reddit/Google-Trends: hard 403/gated even via browser.
  So: this is a SCAFFOLD that becomes a real $0 daily feed ONLY with a TikTok login session. The
  no-new-deps daily path today = a narrow daily WebSearch delta cron (modest tokens). Mapping reuses
  beauty_virality. The weekly agent scan stays for the qualitative layer (influencer, ODM confirmation).

  OUTPUT: beauty-filtered trending hashtags (TikTok CC, authed) scanned against the brand->vehicle map +
  ingredient themes, with a DELTA = new brand-hashtags not yet tracked. Logs to beauty_velocity_log.jsonl.
"""

from __future__ import annotations

# Knowledge-graph dispatch contract (see knowledge_graph/dispatch.py) — added 2026-07-29 gap-close.
APPLIES_TO = {
    "kind": 'm_source',
    "sic_codes": [2844],
    "sic_prefixes": ['284', '512'],
    "issuer_features": ['consumer_beauty_brand', 'consumer_virality_claim'],
    "asset_classes": ['corporate_ipo_dd'],
    "applies_universally": False,
    "summary": 'Daily TikTok virality velocity for tracked beauty brands (browser poll).',
}
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[3]))  # signalos repo root
from verticals.buyside_dd.connectors.beauty_virality import BRAND_TO_VEHICLE, map_to_vehicle

LOG = HERE.parent.parent / "outputs" / "medspa" / "beauty_velocity_log.jsonl"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
DEFAULT_AUTH = Path.home() / ".cosmo_tt_auth.json"  # logged-in TikTok storage_state (from Chrome cookie)


def _auth_path():
    import os
    a = os.environ.get("COSMO_TT_AUTH") or str(DEFAULT_AUTH)
    return a if Path(a).exists() else None

# cosmeceutical ingredient/claim themes — frequency = theme-velocity proxy
THEMES = ["pdrn", "exosome", "peptide", "snail mucin", "centella", "cica", "retinal", "niacinamide",
          "glass skin", "ceramide", "bio-collagen", "salmon", "azelaic", "tranexamic", "spf", "sunscreen", "salicylic", "collagen", "breakouts", "glow up", "derm"]
# brand candidate = Capitalized 1-3 word token immediately before a product noun in a title
_PRODUCT_NOUN = r"(?:Sunscreen|SPF|Serum|Mask|Cream|Toner|Cleanser|Essence|Ampoule|Moisturizer|Sun Stick|Cushion|Lip|Balm|Peel|Pads?)"
_BRAND_CAND = re.compile(r"\b([A-Z][A-Za-z'&.]+(?:\s+[A-Z][A-Za-z'&.]+){0,2})\s+" + _PRODUCT_NOUN)


def _scrape(url: str, timeout=30000):
    from playwright.sync_api import sync_playwright
    auth = _auth_path()  # Playwright storage_state path (logged-in TikTok session)
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        kw = {"user_agent": UA, "locale": "en-US", "viewport": {"width": 1280, "height": 1000}}
        if auth:
            kw["storage_state"] = auth
        ctx = b.new_context(**kw)
        pg = ctx.new_page()
        try:
            pg.goto(url, timeout=timeout, wait_until="domcontentloaded")
            pg.wait_for_timeout(3500)  # let JS render the trend/product cards
            txt = pg.inner_text("body")
        except Exception as e:
            txt = f"__ERR__ {e}"
        finally:
            b.close()
        return txt


def _match_brands(text: str) -> dict:
    low = text.lower()
    hit = sorted({k for k in BRAND_TO_VEHICLE if k in low})
    themes = {t: low.count(t) for t in THEMES if t in low}
    cands = sorted({m.strip() for m in _BRAND_CAND.findall(text)})
    # candidate brands NOT already in the registry or the known-noise set
    noise = {"The", "New", "Best", "Mineral", "Daily", "Face", "Skin", "Gel", "Hydrating", "Korean", "Clear"}
    new_cands = [c for c in cands if c.lower() not in BRAND_TO_VEHICLE and c.split()[0] not in noise][:25]
    return {"tracked_brands_seen": hit, "theme_velocity": themes, "new_brand_candidates": new_cands}


_ROW_RE = re.compile(r"(\d+)\s+(#\S+)\s+(.+?)\s+([\d.]+[KMB]?)\s+Posts\s+([\d.]+[KMB]?)\s+Views")


# consumer-product industries to sweep on TikTok Creative Center (beauty + the cross-category set)
INDUSTRIES = ["Beauty & Personal Care", "Food & Beverage", "Apparel & Accessories",
              "Tech & Electronics", "Household Products"]


def _vnum(s):
    m = {"K": 1e3, "M": 1e6, "B": 1e9}
    try:
        return float(s[:-1]) * m[s[-1]] if s and s[-1] in m else float(s or 0)
    except Exception:
        return 0.0


def poll_cc(industries=None):
    """Sweep TikTok Creative Center trending hashtags across consumer INDUSTRIES (authed), and map
    brand-hashtags to public vehicles. Returns {status, by_industry:{ind:[rows]}, mapped:[...]}."""
    industries = industries or INDUSTRIES
    auth = _auth_path()
    if not auth:
        return {"status": "NO_AUTH", "note": "no ~/.cosmo_tt_auth.json — logged-in TikTok session needed"}
    from playwright.sync_api import sync_playwright
    by_ind = {}
    try:
        with sync_playwright() as p:
            b = p.chromium.launch(headless=True)
            pg = b.new_context(user_agent=UA, locale="en-US", viewport={"width": 1440, "height": 1500},
                               storage_state=auth).new_page()
            pg.goto("https://ads.tiktok.com/business/creativecenter/inspiration/popular/hashtag/pc/en",
                    timeout=40000, wait_until="domcontentloaded")
            pg.wait_for_timeout(5500)
            for ind in industries:
                try:
                    pg.get_by_text(ind, exact=True).first.click(timeout=3500, force=True)
                except Exception:
                    pg.eval_on_selector_all("*", "els=>{let h=els.find(e=>e.children.length===0&&e.innerText"
                        "&&e.innerText.trim()===" + repr(ind) + "); if(h){h.click();return 1}return 0}")
                pg.wait_for_timeout(3000)
                rows, key = {}, ind.split(" ")[0]
                for _ in range(9):
                    for rk, tag, cat, posts, views in _ROW_RE.findall(pg.inner_text("body")):
                        if key in cat:
                            rows[tag] = {"rank": int(rk), "tag": tag, "views": views, "v": _vnum(views)}
                    pg.mouse.wheel(0, 2300); pg.wait_for_timeout(600)
                by_ind[ind] = sorted(rows.values(), key=lambda r: -r["v"])
            b.close()
    except Exception as e:
        return {"status": "ERR", "note": str(e)[:160]}
    # map brand-hashtags -> public vehicles (dedup by ticker, keep highest-views)
    seen = {}
    for ind, rows in by_ind.items():
        for r in rows:
            v = map_to_vehicle(r["tag"][1:])
            if v.get("ticker"):
                cur = seen.get(v["ticker"])
                if not cur or _vnum(r["views"]) > _vnum(cur["views"]):
                    seen[v["ticker"]] = {"industry": ind, "tag": r["tag"], "views": r["views"], **v}
    return {"status": "OK", "by_industry": by_ind, "mapped": list(seen.values())}


def daily_poll():
    asof = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    cc = poll_cc()
    print(f"=== CONSUMER VIRALITY POLL {asof} (TikTok CC, authed, $0 agent — DAILY) ===")
    if cc["status"] != "OK":
        print(f"  TikTok CC: {cc['status']} — {cc.get('note','')}")
        if cc["status"] == "NO_AUTH":
            print("  -> TikTok session expired (~few weeks) — re-grab the cookie from Chrome.")
        with open(LOG, "a") as f:
            f.write(json.dumps({"asof": asof, "status": cc["status"]}, default=str) + "\n")
        return cc
    for ind, rows in cc["by_industry"].items():
        top = ", ".join(f"{r['tag']}({r['views']}v)" for r in rows[:6]) or "—"
        print(f"  {ind:<24}: {top}")
    mapped = sorted(cc["mapped"], key=lambda x: -_vnum(x["views"]))
    print("  -> VIRAL -> PUBLIC vehicle:")
    for m in mapped:
        print(f"     {m['tag']:<22} {m['views']:>6}v -> {m['ticker']:<8} {m['name']} [{m.get('cat','')}]")
    if not mapped:
        print("     (no trending hashtag mapped to a public ticker today — mostly themes/private/foreign)")
    with open(LOG, "a") as f:
        f.write(json.dumps({"asof": asof, "by_industry": cc["by_industry"], "mapped": mapped},
                           ensure_ascii=False, default=str) + "\n")
    print(f"[-> {LOG.name}]")
    return {"asof": asof, "mapped": mapped}


if __name__ == "__main__":
    daily_poll()
