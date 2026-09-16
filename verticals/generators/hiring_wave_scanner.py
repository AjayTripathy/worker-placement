"""hiring_wave_scanner — Stage 0b generator: HIRING WAVES across the research universe (LinkedIn guest,
via the existing hiring_velocity connector machinery).

Inverts the per-site verifier into a universe sweep: posting counts per book/ledger name, delta vs the last
run's state. A posting WAVE = capacity/GTM ramp 1-2 quarters before revenue; a freeze after a wave = the
taper tell. Rate-limit-aware: sweeps <=25 names per run, rotating through the universe (state remembers the
cursor), 2s throttle, degrades honestly on blocks.

  python3 verticals/generators/hiring_wave_scanner.py
Writes data/HIRING_WAVES.json (+ rolling state). READ-ONLY.
"""
from __future__ import annotations
import json, time, datetime, urllib.parse, urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
STATE = HERE / "data" / "hiring_wave_state.json"
OUT = HERE / "data" / "HIRING_WAVES.json"
GUEST = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
      "Accept-Language": "en-US,en;q=0.9"}
BATCH = 25


def _count_postings(company: str) -> int | None:
    """Rough count of current US postings for a company via the guest search (cards on page 1 + total hint)."""
    q = urllib.parse.urlencode({"keywords": f'"{company}"', "location": "United States", "f_C": "", "start": 0})
    try:
        req = urllib.request.Request(f"{GUEST}?{q}", headers=UA)
        with urllib.request.urlopen(req, timeout=30) as r:
            html = r.read().decode("utf-8", "ignore")
    except Exception:
        return None
    return html.count("base-card")            # job cards on the first page (0-25; saturates at 25)


def scan() -> dict:
    led = json.loads((ROOT / "desk" / "data" / "research_ledger.json").read_text()).get("names", [])
    universe = [(n["ticker"], (n.get("name") or n["ticker"]).split("(")[0].strip()) for n in led]
    st = json.loads(STATE.read_text()) if STATE.exists() else {"cursor": 0, "counts": {}}
    start = st.get("cursor", 0) % max(len(universe), 1)
    batch = [universe[(start + i) % len(universe)] for i in range(min(BATCH, len(universe)))]
    today = datetime.date.today().isoformat()
    moves, degraded = [], 0
    for tkr, name in batch:
        c = _count_postings(name)
        time.sleep(2.0)
        if c is None:
            degraded += 1
            continue
        prev = (st["counts"].get(tkr) or {}).get("count")
        st["counts"][tkr] = {"count": c, "date": today, "prev": prev}
        if prev is not None and abs(c - prev) >= 8:
            moves.append({"ticker": tkr, "name": name[:40], "postings": c, "prev": prev, "delta": c - prev})
    st["cursor"] = (start + len(batch)) % max(len(universe), 1)
    STATE.write_text(json.dumps(st))
    moves.sort(key=lambda m: -abs(m["delta"]))
    return {"asof": today, "swept": len(batch), "degraded": degraded, "universe": len(universe),
            "moves": moves, "counts_tracked": len(st["counts"]),
            "note": "page-1 card counts (saturate at 25) — a coarse wave/freeze tell, not a census; SignalOS verifies any move at the source before it seeds"}


def main():
    res = scan()
    print(f"=== HIRING-WAVE SCANNER  {res['asof']}  (swept {res['swept']}/{res['universe']} ledger names, "
          f"{res['degraded']} degraded, {res['counts_tracked']} tracked) ===")
    if res["moves"]:
        for m in res["moves"]:
            arrow = "WAVE" if m["delta"] > 0 else "FREEZE"
            print(f"   {m['ticker']:<9} {m['name']:<38} {m['prev']} -> {m['postings']}  ({m['delta']:+d})  {arrow}")
    else:
        print("   no >=8-posting moves this sweep (baselines accumulate as the cursor rotates)")
    print(f"  {res['note']}")
    OUT.write_text(json.dumps(res, indent=1))
    print(f"[-> {OUT.name}]")


if __name__ == "__main__":
    main()
