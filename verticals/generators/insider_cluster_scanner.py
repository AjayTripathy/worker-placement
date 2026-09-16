"""insider_cluster_scanner — Stage 0b generator: CLUSTERED open-market insider BUYS, whole market (EDGAR Form 4).

HONESTY DOCTRINE (from the priced-in debate): Form 4s are maximally public — NO informational edge exists. The
scanner's claims are narrower: (1) ATTENTION ALLOCATION — clusters point scarce diligence at names where DD is
likelier to find verified substance (the Isaacman/FOUR pattern); (2) any residual drift lives in a CONDITIONED
subset (>=2 distinct insiders, code-P open-market, >=$50k each, within 7 days, SMALL/uncovered names) and was TESTED
by the pre-registered drift backtest 2026-07-02: **NULL** — small-cap clusters showed NEGATIVE median 63d excess
(median -21%, hit 36%, n=28; even with survivorship bias INFLATING it). Verdict applied mechanically: this scanner
is attention-allocation ONLY, its seeds carry NO priority, and cluster-buys must never be cited as evidence of
likely drift. The scanner proposes; it never sizes.

Mechanics: EDGAR daily index -> Form 4 XMLs (throttled, SEC-compliant UA) -> parse code-P acquisitions ->
cluster by issuer over a trailing window held in data/insider_form4_state.json.

  python3 verticals/generators/insider_cluster_scanner.py [--days 5]
Writes data/INSIDER_CLUSTERS.json. READ-ONLY.
"""
from __future__ import annotations
import json, re, time, datetime, argparse, urllib.request
from pathlib import Path
from xml.etree import ElementTree as ET

HERE = Path(__file__).resolve().parent
STATE = HERE / "data" / "insider_form4_state.json"
OUT = HERE / "data" / "INSIDER_CLUSTERS.json"
HDRS = {"User-Agent": "signalos-research 4tripathy@gmail.com"}
MIN_BUY_USD = 50_000
CLUSTER_WINDOW_D = 7
KEEP_DAYS = 21


def _get(url: str, retries: int = 2) -> bytes | None:
    for _ in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers=HDRS)
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read()
        except Exception:
            time.sleep(1.0)
    return None


def _day_form4s(d: datetime.date) -> list[str]:
    """Accession paths of every Form 4 filed on date d (EDGAR daily form index)."""
    q = (d.month - 1) // 3 + 1
    url = f"https://www.sec.gov/Archives/edgar/daily-index/{d.year}/QTR{q}/form.{d:%Y%m%d}.idx"
    raw = _get(url)
    if not raw:
        return []
    paths = []
    for line in raw.decode("latin-1").splitlines():
        if line.startswith("4 ") or line.startswith("4/A "):
            m = re.search(r"(edgar/data/\d+/[\w.-]+\.txt)\s*$", line)
            if m and line.startswith("4 "):        # skip amendments
                paths.append(m.group(1))
    # the daily form index lists each Form 4 TWICE (issuer row + reporting-owner row, same path) —
    # dedupe or every buy double-counts (caught 2026-07-02: KMX cluster reported 2x actual)
    return list(dict.fromkeys(paths))


def _parse_form4(path: str) -> dict | None:
    """Open-market purchase summary from one Form 4, or None. Throttled by the caller."""
    raw = _get(f"https://www.sec.gov/Archives/{path}")
    if not raw:
        return None
    txt = raw.decode("latin-1", "ignore")
    m = re.search(r"<XML>(.*?)</XML>", txt, re.S | re.I)
    if not m:
        return None
    try:
        root = ET.fromstring(m.group(1).strip())
    except ET.ParseError:
        return None
    issuer = root.findtext(".//issuerName") or ""
    sym = (root.findtext(".//issuerTradingSymbol") or "").upper().strip()
    owner = root.findtext(".//rptOwnerName") or ""
    officer = (root.findtext(".//isOfficer") or "0") in ("1", "true")
    director = (root.findtext(".//isDirector") or "0") in ("1", "true")
    buy_usd = 0.0
    for tr in root.iter("nonDerivativeTransaction"):
        code = tr.findtext(".//transactionCode") or ""
        acq = tr.findtext(".//transactionAcquiredDisposedCode/value") or ""
        if code == "P" and acq == "A":
            sh = float(tr.findtext(".//transactionShares/value") or 0)
            px = float(tr.findtext(".//transactionPricePerShare/value") or 0)
            buy_usd += sh * px
    if buy_usd < MIN_BUY_USD or not sym or sym in ("NONE", "N/A", "NA"):
        return None
    if any(k in issuer.upper() for k in (" FUND", " L.P", " LP,", "CAPITAL INCOME", "INFRASTRUCTURE STRATEGIES")):
        return None            # fund-closing Form 4s (LP mechanics) are not insider conviction signals
    return {"symbol": sym, "issuer": issuer[:60], "owner": owner[:40],
            "role": "officer" if officer else "director" if director else "10%+",
            "buy_usd": round(buy_usd)}


def scan(days: int) -> dict:
    state = json.loads(STATE.read_text()) if STATE.exists() else {"buys": [], "scanned_days": []}
    today = datetime.date.today()
    # scan business days not yet in state
    d, new = today, 0
    checked = 0
    while checked < days + 3 and (today - d).days <= days + 5:
        if d.weekday() < 5 and d.isoformat() not in state["scanned_days"]:
            paths = _day_form4s(d)
            for i, p in enumerate(paths):
                r = _parse_form4(p)
                if r:
                    r["date"] = d.isoformat()
                    key = (r["symbol"], r["owner"], r["date"], r["buy_usd"])
                    if key not in {(b["symbol"], b["owner"], b["date"], b["buy_usd"]) for b in state["buys"]}:
                        state["buys"].append(r)
                        new += 1
                if i % 8 == 7:
                    time.sleep(0.5)          # ~SEC-safe pace
            state["scanned_days"].append(d.isoformat())
        if d.weekday() < 5:
            checked += 1
        d -= datetime.timedelta(days=1)
    # prune old
    cutoff = (today - datetime.timedelta(days=KEEP_DAYS)).isoformat()
    state["buys"] = [b for b in state["buys"] if b["date"] >= cutoff]
    state["scanned_days"] = sorted(set(s for s in state["scanned_days"] if s >= cutoff))
    STATE.write_text(json.dumps(state))
    # cluster: >=2 distinct owners, code-P >= $50k each, within CLUSTER_WINDOW_D
    win = (today - datetime.timedelta(days=CLUSTER_WINDOW_D)).isoformat()
    recent = [b for b in state["buys"] if b["date"] >= win]
    by_sym = {}
    for b in recent:
        by_sym.setdefault(b["symbol"], []).append(b)
    clusters = []
    for sym, buys in by_sym.items():
        owners = {b["owner"] for b in buys}
        if len(owners) >= 2:
            clusters.append({"symbol": sym, "issuer": buys[0]["issuer"], "n_insiders": len(owners),
                             "total_usd": sum(b["buy_usd"] for b in buys),
                             "roles": sorted({b["role"] for b in buys}),
                             "buys": sorted(buys, key=lambda x: -x["buy_usd"])[:6]})
    clusters.sort(key=lambda c: (-c["n_insiders"], -c["total_usd"]))
    return {"asof": today.isoformat(), "window_days": CLUSTER_WINDOW_D, "new_filings_parsed": new,
            "n_single_buys": len(recent), "clusters": clusters}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=5, help="business days of Form 4s to ensure scanned")
    a = ap.parse_args()
    res = scan(a.days)
    print(f"=== INSIDER CLUSTER SCANNER  {res['asof']}  ({res['new_filings_parsed']} new code-P buys parsed; "
          f"{res['n_single_buys']} buys in the {res['window_days']}d window) ===")
    if res["clusters"]:
        print(f"  CLUSTERS (>=2 distinct insiders, >=${MIN_BUY_USD/1000:.0f}k each) — attention-allocation seeds:")
        for c in res["clusters"][:12]:
            print(f"   {c['symbol']:<6} {c['issuer'][:42]:<42} {c['n_insiders']} insiders  ${c['total_usd']:>10,}  ({'/'.join(c['roles'])})")
        print("  PROMOTE: trap-screen the small/uncovered clusters first (capacity niche); famous names are priced.")
    else:
        print("  no clusters in the window")
    print("  DOCTRINE: no informational edge claimed (Form 4s are public); value = attention allocation + the")
    print("  CONDITIONED small-cap subset pending our own drift backtest. The scanner proposes; the pipeline disposes.")
    OUT.write_text(json.dumps(res, indent=1))
    print(f"[-> {OUT.name}]")


if __name__ == "__main__":
    main()
