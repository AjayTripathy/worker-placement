"""index_events — the S&P index add/delete stream (the MFP class, made recurring).

Clock mismatch: S&P DJI announces constituent changes ~2-5 days before the
effective date; on small-caps the crossing flows (deleted-from sellers vs
added-to buyers) are mechanical, dated, and un-arbitraged at odd-lot size.
MFP (+3% in two days) was the manual proof; this watcher makes the pipeline.

Daily: poll the S&P DJI press-release page for "Set to Join"/"to Replace"
headlines; NEW small/mid-cap events -> notify + append to
desk/data/index_event_pipeline.json for triage (the desk decides which get a
court + an event window in event_windows.json).

    python3 -m desk.index_events        # registered daily
READ-ONLY; alerts only.
"""
from __future__ import annotations
import json, re, urllib.request, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "desk" / "data" / "index_event_pipeline.json"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"}
URL = "https://press.spglobal.com/index.php?s=2429"  # S&P DJI index-news press stream

def _notify(msg):
    try:
        from desk.gauntlet_sentinel import _notify as n; n(msg)
    except Exception:
        print("[index_events] NOTIFY:", msg)

def main():
    st = json.loads(STATE.read_text()) if STATE.exists() else {"seen": [], "pipeline": []}
    try:
        html = urllib.request.urlopen(urllib.request.Request(URL, headers=UA), timeout=25).read(400_000).decode(errors="ignore")
    except Exception as e:
        print("[index_events] fetch failed:", e); return
    # headlines like "X Set to Join S&P SmallCap 600; Y to Replace Z in S&P MidCap 400"
    heads = re.findall(r'>([^<]{15,160}(?:Set to Join|to Replace|Join S&P|Changes to)[^<]{0,120})<', html)
    fresh = []
    for h in dict.fromkeys(heads):
        h = h.strip()
        if h in st["seen"]:
            continue
        st["seen"].append(h)
        if any(k in h for k in ("SmallCap 600", "MidCap 400", "Completion", "SPAC")):
            st["pipeline"].append({"headline": h, "seen": datetime.date.today().isoformat(), "status": "TRIAGE"})
            fresh.append(h)
    STATE.write_text(json.dumps(st, indent=1))
    if fresh:
        _notify("INDEX EVENTS (the MFP class): " + " | ".join(fresh)[:700] +
                " — small/mid-cap index changes create dated crossing flows; the desk triages for an event window.")
    print(f"[index_events] {len(fresh)} new of {len(heads)} headlines")

if __name__ == "__main__":
    main()
