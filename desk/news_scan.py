"""news_scan — raw material collector for news/data-driven thesis generation.

NOT a thesis generator by itself: it collects candidate EVENTS into
desk/data/news_candidates.jsonl for the Desk/analyst triage pass, which grades
each against the four edge patterns (see TRIAGE PROTOCOL in the registry note):
  insulation | second-order read-through | data-release front-run | round-trip
and then routes survivors through tape-verify -> conditioning -> the courts.

Sources (free, no keys):
  1. EDGAR EFTS full-text: fresh 8-K material events (items via form filter) —
     bankruptcies, NT filings, item-8.01 surprises across the whole market.
  2. GDELT doc API: last-hours news volume spikes on the desk's THEME terms
     (chokepoints, sanctions, recalls, strikes, tariffs, defaults...).
  3. The data-release calendar seed (static, desk/data/data_calendar.json):
     recurring official releases mapped to exposed book/watch names.

Cadence: the Desk hourly heartbeat (registered in desk/registry.py).
    python3 -m desk.news_scan [--dry]
READ-ONLY; emits candidates + counts only.
"""
from __future__ import annotations

import datetime
import json
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "desk" / "data" / "news_candidates.jsonl"
STATE = ROOT / "desk" / "data" / "news_scan_state.json"
HDRS = {"User-Agent": "signalos-research 4tripathy@gmail.com"}

# theme terms the KG has live mechanisms for — each maps to a pattern hint
THEMES = {
    "strait of hormuz": "round_trip", "suez": "round_trip", "panama canal": "round_trip",
    "secondary sanctions": "insulation", "ofac designat": "insulation",
    "chapter 11": "insulation", "going concern": "insulation",
    # CDS legs of the AI-break tripwires (2026-09-12): press-quoted single-name CDS levels are the
    # only free price signal on ORCL/CoreWeave-class credit; a GDELT volume spike on these terms =
    # a credit desk is talking about the AI refi wall. Route to the AI-break court, not a trade.
    "credit default swap": "second_order", "coreweave debt": "second_order", "oracle bonds": "second_order",
    "port strike": "second_order", "recall": "second_order",
    "export ban": "second_order", "tariff": "second_order",
    "ceasefire": "round_trip", "windfall tax": "insulation",
    "short squeeze": "round_trip", "tender offer": "second_order",
}


def _edgar_fresh(hours: int = 6) -> list[dict]:
    """Material 8-K items filed in the last N hours, market-wide."""
    now = datetime.datetime.utcnow()
    day = now.date().isoformat()
    prev = (now - datetime.timedelta(hours=hours + 18)).date().isoformat()
    q = urllib.parse.urlencode({
        "q": '"item 8.01" OR "item 1.03" OR "item 2.06"',
        "forms": "8-K,NT 10-K,NT 10-Q,NT 20-F", "startdt": prev, "enddt": day,   # span the UTC midnight roll; NT-* = late-filing landmines (clock-atlas build 2026-07-08: 'we cannot file on time' is a top-tier distress tell, EDGAR-visible in minutes, uncovered in smallcaps — route to the trap catalog / any HELD name = immediate alert)
    })
    url = f"https://efts.sec.gov/LATEST/search-index?{q}"
    out = []
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=HDRS), timeout=25) as r:
            js = json.load(r)
        for h in js.get("hits", {}).get("hits", [])[:40]:
            src = h.get("_source", {})
            out.append({"src": "edgar", "id": h.get("_id", ""),
                        "name": (src.get("display_names") or [""])[0],
                        "filed": src.get("file_date", day)})
    except Exception:
        pass
    return out


def _gdelt(hours: int = 6) -> list[dict]:
    """News-volume hits on KG theme terms in the last N hours."""
    out = []
    for term, pattern in THEMES.items():
        q = urllib.parse.urlencode({
            "query": f'"{term}"', "mode": "artlist", "maxrecords": 4,
            "timespan": f"{hours}h", "format": "json", "sort": "hybridrel",
        })
        try:
            with urllib.request.urlopen(
                    f"https://api.gdeltproject.org/api/v2/doc/doc?{q}", timeout=20) as r:
                js = json.load(r)
            arts = js.get("articles", [])
            # event-vs-marketing filter: kill PR-wire itinerary/deal/award fluff
            NOISE = ("announces", "unveils", "celebrat", "itinerar", "award", "partners with",
                     "launches new", "cruise", "sweepstake", "anniversary")
            arts = [a for a in arts if not any(n in a.get("title", "").lower() for n in NOISE)]
            if arts:
                out.append({"src": "gdelt", "term": term, "pattern_hint": pattern,
                            "n": len(arts),
                            "top": [{"t": a.get("title", "")[:140], "u": a.get("url", "")}
                                    for a in arts[:2]]})
        except Exception:
            continue
    return out


def main(dry: bool = False) -> dict:
    state = json.load(open(STATE)) if STATE.exists() else {"seen": []}
    seen = set(state["seen"][-800:])
    stamp = datetime.datetime.utcnow().isoformat(timespec="minutes")
    fresh = []
    for ev in _edgar_fresh() + _gdelt():
        key = ev.get("id") or f"{ev.get('term')}|{(ev.get('top') or [{}])[0].get('u','')}"
        if key in seen:
            continue
        seen.add(key)
        ev["ts"] = stamp
        fresh.append(ev)
    if not dry and fresh:
        with open(OUT, "a") as f:
            for ev in fresh:
                f.write(json.dumps(ev) + "\n")
    if not dry:
        state["seen"] = sorted(seen)
        json.dump(state, open(STATE, "w"), indent=1)
    print(f"[news_scan] {len(fresh)} fresh candidates "
          f"({sum(1 for e in fresh if e['src']=='edgar')} edgar / "
          f"{sum(1 for e in fresh if e['src']=='gdelt')} gdelt themes) -> news_candidates.jsonl")
    return {"fresh": len(fresh)}


if __name__ == "__main__":
    import sys
    main(dry="--dry" in sys.argv)
