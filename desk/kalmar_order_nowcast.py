"""kalmar_order_nowcast v2 — forward instrumentation for the KALMAR.HE starter.
v1 built 2026-07-29 (orders side); v2 same day adds the DELIVERIES side + splits the PR classifier.

The position's load-bearing variable is EQUIPMENT ORDER INTAKE: the court's kill list carries
"two consecutive qtrs group book-to-bill <0.95" (Q2-26 printed 0.94 = strike one) and
"eco order share <35%" (Q2 at 40%). This watch nowcasts intake AND deliveries ahead of the
Q3 report (2026-10-29) from public data that leads the print:

  ORDERS (intake — feeds the B2B tripwire numerator):
  1. TED (EU public procurement) — port cargo-handling tenders under CPV 42414* + free-text.
     Tenders are public MONTHS before any OEM books the order. Publication-date censoring only.
  2. Kalmar ORDER-class press releases, counted quarter-to-date (GlobeNewswire). Large orders
     only get PRs -> a FLOOR detector (zero past day 45 = visibly weak), never a point estimate.

  DELIVERIES (the revenue side — cross-checks "Americas strength" and the order-book drawdown):
  3. Kalmar DEPLOY-class press releases (fleet expansions / deployments / in-operation) — these
     mark equipment ENTERING SERVICE, i.e. orders booked quarters ago now delivering. v1 counted
     these as orders (the WTC T2-EV fleet PR); v2 splits them out.
  4. Plant hiring velocity (LinkedIn guest endpoint via the hiring_velocity connector) at
     Kalmar's own sites — Ottawa KS (terminal tractors), Stargard PL (reachstackers/heavy),
     Tampere FI (straddle/automation). Production-role posting wave/taper proxies the
     delivery ramp a quarter out. SERIES signal — first sample banks the baseline.
  5. US customs imports (Census intltrade, vessel) — HS 842720 from Poland (the live Kalmar
     Stargard lane, ~$3-5M/mo) + HS 842612/842720 from Finland (lumpy, often zero). CAVEAT:
     HS x origin is a COHORT proxy (other OEMs export from PL too), read the trend not the
     level; Census publishes ~2 months in arrears.

  MACRO ANCHOR: 6. RWI/ISL container-throughput index (parse v2 still owed).
  ECO FEED: 7. EPA Clean Ports page change-detect (ZE cargo-handling awards).

DOCTRINE: a TRIPWIRE NOWCAST for our own kill/add decisions and the frozen Oct-29 calibration
call (KALMAR.HE|2026-10-29, earnings_operating) — NOT claimed alpha (frontrun ledger 4-for-4
negative on pipeline-leads-the-stock). A blocked source is DATA MISSING, never zero (the SPCX
false-absence guard — hiring uses an unfiltered probe to distinguish blocked from truly-zero).
Grades at the Oct-29 print; the detector earns trust empirically or dies.
"""
from __future__ import annotations
import json, re, sys, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "desk" / "data" / "kalmar_nowcast"
STATE = DATA / "state.json"
HISTORY = DATA / "history.jsonl"

TED_API = "https://api.ted.europa.eu/v3/notices/search"
GNW_FEED = "https://www.globenewswire.com/RssFeed/organization/xNvREUZAX-XU8SFUKUAJgQ==/feedTitle/Kalmar"
GNW_SEARCH = "https://www.globenewswire.com/en/search/organization/Kalmar"
ISL_URL = "https://www.isl.org/en/containerindex"
EPA_URL = "https://www.epa.gov/ports-initiative/clean-ports-program"

# v2 SPLIT classifier: ORDER = fresh intake (feeds the B2B tripwire read);
# DEPLOY = equipment entering service = the DELIVERIES series (booked quarters ago).
# "showcases"/"unveils"/"launches" are marketing — deliberately in NEITHER class.
ORDER_CLASS = re.compile(
    r"receives?.(an?.)?order|order.for|to.(deliver|supply)|signs?.(an?.)?(agreement|contract)"
    r"|frame.agreement|repeat.order|books?.(an?.)?order", re.I)
DEPLOY_CLASS = re.compile(
    r"expands?.+(fleet|operations.with)|deploys?|in.operation|takes?.delivery"
    r"|enters?.service|now.operating|adds?.+(tractors?|reachstackers?|handlers?|carriers?).to", re.I)

# Kalmar production sites for the hiring-velocity deliveries proxy
PLANT_SITES = [
    ("ottawa_ks", "Ottawa, Kansas, United States"),
    ("stargard_pl", "Stargard, Poland"),
    ("tampere_fi", "Tampere, Finland"),
]

# Census import lanes (HS6, origin Schedule-C code, label). Vessel mode.
IMPORT_LANES = [
    ("842720", "4550", "reachstacker_heavy_PL"),   # the live Kalmar Stargard lane
    ("842720", "4050", "reachstacker_heavy_FI"),
    ("842612", "4050", "straddle_FI"),
]

# Q2-26 actuals from the H1 report (the graded baseline)
BASELINE = {"q2_orders_meur": 449, "q2_sales_meur": 480, "q2_b2b": 0.94, "eco_share_pct": 40,
            "order_book_meur": 986, "quarterly_pace_bar_meur": 440}


def _fetch(url, **kw):
    """curl_cffi chrome fingerprint (gov/enterprise 403 lesson); None on any failure."""
    try:
        from curl_cffi import requests as creq
        r = creq.get(url, impersonate="chrome124", timeout=40, **kw)
        return r if r.status_code == 200 else None
    except Exception:
        return None


def ted_tender_pulse(days=90):
    """Count EU cargo-handling tenders published in the window. DATA MISSING on failure."""
    try:
        from curl_cffi import requests as creq
        since = (datetime.date.today() - datetime.timedelta(days=days)).strftime("%Y%m%d")
        q = ('(classification-cpv IN (42414000 42414100 42414110 42414120 42414400 42418000)) '
             f'AND publication-date >= {since}')
        r = creq.post(TED_API, json={"query": q, "fields": ["publication-number"], "limit": 1},
                      impersonate="chrome124", timeout=40)
        if r.status_code != 200:
            return {"status": "DATA MISSING", "detail": f"TED HTTP {r.status_code}"}
        return {"status": "ok", "window_days": days, "tender_count": r.json().get("totalNoticeCount")}
    except Exception as e:
        return {"status": "DATA MISSING", "detail": str(e)[:120]}


def kalmar_pr_pulse():
    """QTD PR counts, SPLIT order-class vs deploy-class (v2). 0 items parsed = DATA MISSING."""
    r = _fetch(GNW_FEED) or _fetch(GNW_SEARCH)
    if r is None:
        return {"status": "DATA MISSING", "detail": "GNW feed+search both failed"}
    text = r.text
    today = datetime.date.today()
    qstart = datetime.date(today.year, 3 * ((today.month - 1) // 3) + 1, 1)
    items = re.findall(r"<item>(.*?)</item>", text, re.S) or \
            re.findall(r'<a[^>]+href="(/news-release/[^"]+)"[^>]*>([^<]+)</a>', text)
    if not items:
        return {"status": "DATA MISSING", "detail": "0 items parsed from feed/search page"}
    orders, deploys, o_titles, d_titles = 0, 0, [], []
    for it in items:
        blob = it if isinstance(it, str) else " ".join(it)
        title_m = re.search(r"<title>(.*?)</title>", blob, re.S)
        title = (title_m.group(1) if title_m else blob)[:160]
        indate = True
        date_m = re.search(r"<pubDate>(.*?)</pubDate>", blob)
        url_m = re.search(r"/news-release/(\d{4})/(\d{2})/(\d{2})/", blob)
        if date_m:
            try:
                pub = datetime.datetime.strptime(date_m.group(1)[:16].strip(), "%a, %d %b %Y").date()
                indate = pub >= qstart
            except Exception:
                pass
        elif url_m:
            indate = datetime.date(*map(int, url_m.groups())) >= qstart
        if not indate:
            continue
        if ORDER_CLASS.search(blob):
            orders += 1; o_titles.append(title.strip()[:120])
        elif DEPLOY_CLASS.search(blob):
            deploys += 1; d_titles.append(title.strip()[:120])
    return {"status": "ok", "qtd_order_prs": orders, "qtd_delivery_prs": deploys,
            "quarter_start": str(qstart), "order_titles": o_titles[:8], "deploy_titles": d_titles[:8]}


def plant_hiring_pulse():
    """Kalmar production-site posting counts (deliveries-ramp proxy). Blocked != zero:
    an unfiltered probe must return rows for a site before 0 Kalmar rows counts as zero."""
    try:
        from verticals.buyside_dd.connectors.hiring_velocity import fetch_postings, _classify
    except Exception as e:
        return {"status": "DATA MISSING", "detail": f"hiring connector import failed: {e}"}
    sites, any_ok = {}, False
    for key, loc in PLANT_SITES:
        try:
            rows = fetch_postings("Kalmar", loc, company_filter=("kalmar",), max_pages=3)
            if not rows:
                probe = fetch_postings("engineer", loc, max_pages=1)  # endpoint-alive check
                if not probe:
                    sites[key] = {"status": "DATA MISSING", "detail": "endpoint returned nothing (blocked?)"}
                    continue
            prod = sum(1 for x in rows if _classify(x["title"]) == "production")
            sites[key] = {"status": "ok", "open_postings": len(rows), "production_roles": prod}
            any_ok = True
        except Exception as e:
            sites[key] = {"status": "DATA MISSING", "detail": str(e)[:100]}
    return {"status": "ok" if any_ok else "DATA MISSING", "sites": sites}


def us_import_pulse():
    """Census vessel-import series on Kalmar-correlated HS x origin lanes (deliveries, ~2mo lag).
    COHORT proxy — other OEMs share the lanes; read trend, not level."""
    try:
        from verticals.buyside_dd.connectors.customer_id import census_trade_flow
    except Exception as e:
        return {"status": "DATA MISSING", "detail": f"customs connector import failed: {e}"}
    start = (datetime.date.today().replace(day=1) - datetime.timedelta(days=550)).strftime("%Y-%m")
    lanes, any_ok = {}, False
    for hs, cty, label in IMPORT_LANES:
        r = census_trade_flow(hs, cty, start=start, end=datetime.date.today().strftime("%Y-%m"), mode="vessel")
        ser = r.get("series") or []
        if r.get("status") not in ("OK", "THIN") or not ser:
            lanes[label] = {"status": "DATA MISSING", "detail": r.get("status", "?")}
            continue
        vals = [x["total_M"] for x in ser]
        recent3 = round(sum(vals[-3:]) / max(1, len(vals[-3:])), 2)
        base12 = round(sum(vals[-15:-3]) / max(1, len(vals[-15:-3])), 2)
        lanes[label] = {"status": "ok", "latest_month": ser[-1]["month"], "recent_3mo_avg_M": recent3,
                        "baseline_12mo_avg_M": base12,
                        "ratio": round(recent3 / base12, 2) if base12 else None}
        any_ok = True
    return {"status": "ok" if any_ok else "DATA MISSING", "lanes": lanes}


def throughput_pulse():
    """Latest RWI/ISL container-throughput index reading off the public page."""
    r = _fetch(ISL_URL)
    if r is None:
        return {"status": "DATA MISSING", "detail": "ISL page fetch failed"}
    m = re.findall(r"(\d{3}[.,]\d)\s*(?:points?|Punkte)?", r.text)
    mon = re.search(r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+20\d\d", r.text)
    if not m:
        return {"status": "DATA MISSING", "detail": "no index value parsed"}
    return {"status": "ok", "latest_index": m[0].replace(",", "."), "as_of": mon.group(0) if mon else "unparsed"}


def us_subsidy_pulse(prev):
    """Change-detect on the EPA Clean Ports page (ZE cargo-handling money = eco-share feed)."""
    r = _fetch(EPA_URL)
    if r is None:
        return {"status": "DATA MISSING", "detail": "EPA page fetch failed"}
    import hashlib
    h = hashlib.sha256(re.sub(r"\s+", " ", r.text).encode()).hexdigest()[:16]
    changed = bool(prev) and prev.get("page_hash") not in (None, h)
    return {"status": "ok", "page_hash": h, "changed_since_last": changed}


def main():
    DATA.mkdir(parents=True, exist_ok=True)
    prev = json.loads(STATE.read_text()) if STATE.exists() else {}
    now = datetime.datetime.now().isoformat(timespec="seconds")

    ted = ted_tender_pulse()
    prs = kalmar_pr_pulse()
    hiring = plant_hiring_pulse()
    imports = us_import_pulse()
    thru = throughput_pulse()
    epa = us_subsidy_pulse(prev.get("us_subsidy", {}))

    flags = []
    if ted["status"] == "ok" and prev.get("ted", {}).get("status") == "ok":
        prior = prev["ted"].get("tender_count") or 0
        if prior and ted["tender_count"] < 0.7 * prior:
            flags.append(f"FLAG: EU tender pulse -{100 - 100*ted['tender_count']//prior}% vs last sample ({ted['tender_count']} vs {prior}) — intake headwind")
    if prs["status"] == "ok" and prs["qtd_order_prs"] == 0:
        qday = (datetime.date.today() - datetime.date.fromisoformat(prs["quarter_start"])).days
        if qday > 45:
            flags.append("FLAG: ZERO Kalmar ORDER-class PRs this quarter past day 45 — floor detector tripped (visibly weak intake)")
    if hiring["status"] == "ok" and prev.get("plant_hiring", {}).get("status") == "ok":
        cur = sum(s.get("production_roles", 0) for s in hiring["sites"].values() if s.get("status") == "ok")
        pri = sum(s.get("production_roles", 0) for s in prev["plant_hiring"]["sites"].values() if s.get("status") == "ok")
        if pri >= 5 and cur < 0.5 * pri:
            flags.append(f"FLAG: plant production-role postings -{100 - 100*cur//pri}% ({cur} vs {pri}) — delivery-ramp TAPER")
        elif pri >= 3 and cur > 1.5 * pri:
            flags.append(f"INFO: plant production postings +{100*cur//pri - 100}% ({cur} vs {pri}) — delivery-ramp building")
    if imports["status"] == "ok":
        pl = imports["lanes"].get("reachstacker_heavy_PL", {})
        if pl.get("status") == "ok" and pl.get("ratio") is not None and pl["ratio"] < 0.5:
            flags.append(f"FLAG: PL heavy-equipment import lane at {pl['ratio']}x its 12mo baseline — US deliveries stalling (cohort proxy, ~2mo lag)")
    if epa.get("changed_since_last"):
        flags.append("INFO: EPA Clean Ports page changed — re-read for new ZE cargo-handling awards (eco-share feed)")

    snap = {"ts": now, "ted": ted, "kalmar_prs": prs, "plant_hiring": hiring, "us_imports": imports,
            "throughput": thru, "us_subsidy": epa, "baseline": BASELINE, "flags": flags}
    STATE.write_text(json.dumps(snap, indent=1))
    with HISTORY.open("a") as f:
        f.write(json.dumps(snap) + "\n")

    print(f"[kalmar_nowcast v2] {now}")
    for k, v in (("TED tenders", ted), ("Kalmar PRs", prs), ("Plant hiring", hiring),
                 ("US imports", imports), ("Throughput", thru), ("US subsidy", epa)):
        slim = {kk: vv for kk, vv in v.items() if kk not in ("order_titles", "deploy_titles")}
        print(f"  {k}: {json.dumps(slim)}")
    for t in prs.get("order_titles", []):
        print(f"    ORDER PR: {t}")
    for t in prs.get("deploy_titles", []):
        print(f"    DELIVERY PR: {t}")
    for fl in flags:
        print(f"  {fl}")
    if not flags:
        print("  no flags — tripwires quiet (B2B strike count stays 1; eco share last 40%)")
    print("  grades vs KALMAR.HE|2026-10-29 (frozen earnings_operating call) — PAPER until then")
    return 0


if __name__ == "__main__":
    sys.exit(main())
