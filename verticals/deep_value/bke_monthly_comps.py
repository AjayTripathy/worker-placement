"""bke_monthly_comps — PRIMARY-data melt tripwire for BKE (The Buckle).

Buckle is one of the last US retailers still reporting MONTHLY net sales + comparable sales by press
release — a monthly-latency, primary-source answer to "melting or strong?" that the attention layer
could not provide (heat triangulation 2026-07-02: BKE unmeasurable, apparel instrument NULL).

Scrapes the IR news feed for the latest "Reports ... Net Sales" release, extracts the comp %, keeps a
history, and fires on the melt tripwire: comparable sales NEGATIVE (single month = flag; the DD
falsifier is the trend, so 2 consecutive negative months = MELT WARNING).

  python3 verticals/deep_value/bke_monthly_comps.py
Writes data/bke_monthly_comps.json. READ-ONLY.
"""
from __future__ import annotations
import json, re, datetime, urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "data" / "bke_monthly_comps.json"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"}
# Buckle files each monthly sales release as an 8-K exhibit -> EDGAR is the durable feed (CIK 885245)
def _efts_url():
    import datetime as _dt
    start = (_dt.date.today() - _dt.timedelta(days=60)).isoformat()
    return ("https://efts.sec.gov/LATEST/search-index?q=%22comparable+store+net+sales%22"
            f"&forms=8-K&ciks=0000885245&dateRange=custom&startdt={start}&enddt={_dt.date.today().isoformat()}")
SEC_UA = {"User-Agent": "signalos-research 4tripathy@gmail.com"}


def _get(url):
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.read().decode("utf-8", "ignore")
    except Exception:
        return None


def latest_monthly() -> dict | None:
    """Newest monthly-sales headline via Buckle's IR JSON API (Q4 platform). Monthlies are NOT reliably
    8-K'd (checked 2026-07-02: June-4 May-sales PR has no 8-K), so detection = IR feed; the comp % is
    parsed from the 8-K when one exists, else flagged for a manual one-number read."""
    url = ("https://corporate.buckle.com/feed/PressRelease.svc/GetPressReleaseList"
           "?LanguageId=1&pressReleaseDateFilter=3&pageSize=10&pageNumber=0")
    txt = _get(url)
    if not txt:
        return None
    try:
        rows = json.loads(txt)["GetPressReleaseListResult"]
    except Exception:
        return None
    for r in rows:
        h = r.get("Headline", "")
        m = re.search(r"Reports (January|February|March|April|May|June|July|August|September|October|November|December) (\d{4}) Net Sales", h)
        if not m:
            continue
        detail = "https://corporate.buckle.com" + (r.get("LinkToDetailPage") or "")
        # best-effort comp parse from a matching 8-K exhibit (often absent for monthlies)
        comp = _comp_from_recent_8k()
        return {"title": h, "url": detail, "pub": (r.get("PressReleaseDate") or "")[:10],
                "period": f"{m.group(1)} {m.group(2)}", "comp_pct": comp,
                "comp_source": ("8-K" if comp is not None else "UNPARSED — read the PR (one number)")}
    return None


def _comp_from_recent_8k() -> float | None:
    try:
        req = urllib.request.Request(_efts_url(), headers=SEC_UA)
        with urllib.request.urlopen(req, timeout=30) as r:
            hits = json.load(r).get("hits", {}).get("hits", [])
    except Exception:
        return None
    hits.sort(key=lambda h: h.get("_source", {}).get("file_date", ""), reverse=True)
    for h in hits[:3]:
        acc_file = h.get("_id", "")
        if ":" not in acc_file:
            continue
        acc, fname = acc_file.split(":", 1)
        body = _get(f"https://www.sec.gov/Archives/edgar/data/885245/{acc.replace('-','')}/{fname}")
        if not body:
            continue
        # only accept a MONTHLY exhibit ("4-week period") — quarterly comps are tracked separately
        if "4-week" not in body and "5-week" not in body:
            continue
        m = re.search(r"[Cc]omparable store net sales[^.]{0,160}?(increased|decreased)\s+([\d.]+)\s*percent", body)
        if m:
            return float(m.group(2)) * (-1 if "decreas" in m.group(1) else 1)
    return None


def main():
    st = json.loads(OUT.read_text()) if OUT.exists() else {"history": []}
    latest = latest_monthly()
    today = datetime.date.today().isoformat()
    if not latest:
        print(f"=== BKE MONTHLY COMPS  {today}  DEGRADED: no monthly PR found on IR/GlobeNewswire feeds ===")
        st["last_run"] = today
        OUT.write_text(json.dumps(st, indent=1))
        return
    if not any(h["title"] == latest["title"] for h in st["history"]):
        st["history"].append({**latest, "seen": today})
        st["history"] = st["history"][-24:]
    comps = [h.get("comp_pct") for h in st["history"] if h.get("comp_pct") is not None]
    fire = None
    if comps and comps[-1] is not None and comps[-1] < 0:
        fire = "MELT WARNING: 2 consecutive negative months — the DD falsifier is triggering" \
               if len(comps) >= 2 and comps[-2] < 0 else "FLAG: single negative month (watch next print)"
    print(f"=== BKE MONTHLY COMPS  {today} ===")
    print(f"   latest: {latest['title']}  comp {latest['comp_pct']:+.1f}%" if latest.get("comp_pct") is not None
          else f"   latest: {latest['title']}  (comp % not parsed — read the PR: {latest['url']})")
    if len(comps) > 1:
        print(f"   history: {' '.join(f'{c:+.1f}' for c in comps[-8:])}")
    print(f"   {fire}" if fire else "   comps positive — melt falsifier NOT triggered (anti-melt tell intact)")
    st["last_run"], st["fire"] = today, fire
    OUT.write_text(json.dumps(st, indent=1))
    print(f"[-> {OUT.name}]")


if __name__ == "__main__":
    main()
