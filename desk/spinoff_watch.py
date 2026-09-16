"""spinoff_watch — the Form 10-12B pipeline (spin-off / post-reorg orphan stream).

Mechanism: a spun company registers on Form 10-12B weeks-to-months before its
shares distribute. At distribution, index funds and mandate-constrained
holders sell mechanically regardless of price — the orphan window (the first
~1-6 weeks) is where uncovered spincos misprice. This watcher maintains the
registration pipeline so the desk studies each spinco BEFORE its orphan
window opens, instead of discovering it after.

Daily: poll EDGAR EFTS for 10-12B + amendments (90d window), dedupe by CIK,
notify on NEW registrants, track amendment cadence (amendments accelerating =
distribution approaching). State -> desk/data/spinoff_pipeline.json.

    python3 -m desk.spinoff_watch          # registered daily
READ-ONLY; alerts only, never orders.
"""
from __future__ import annotations

import datetime
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "desk" / "data" / "spinoff_pipeline.json"
UA = {"User-Agent": "SignalOS research desk 4tripathy@gmail.com"}


def _efts(days=90):
    end = datetime.date.today()
    start = end - datetime.timedelta(days=days)
    url = (f"https://efts.sec.gov/LATEST/search-index?forms=10-12B"
           f"&dateRange=custom&startdt={start}&enddt={end}")
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=25) as r:
        return json.loads(r.read()).get("hits", {}).get("hits", [])


def _notify(msg: str):
    try:
        from desk.gauntlet_sentinel import notify
        notify("SPINOFF PIPELINE", msg)
    except Exception:
        print(f"[spinoff_watch] NOTIFY: {msg}")


def main():
    state = json.loads(STATE.read_text()) if STATE.exists() else {"pipeline": {}}
    pipe = state["pipeline"]
    try:
        hits = _efts()
    except Exception as e:
        print(f"[spinoff_watch] EFTS unreachable: {e}")
        return
    fresh = []
    for h in hits:
        s = h["_source"]
        cik = str(s.get("cik") or (s.get("ciks") or [""])[0])
        name = ", ".join(s.get("display_names", []))[:80]
        fdate = s.get("file_date")
        ftype = s.get("file_type", "10-12B")
        if not cik:
            continue
        rec = pipe.get(cik)
        if rec is None:
            pipe[cik] = {"name": name, "first_seen": fdate, "filings": [f"{fdate} {ftype}"],
                         "status": "REGISTERING"}
            fresh.append(name)
        else:
            key = f"{fdate} {ftype}"
            if key not in rec["filings"]:
                rec["filings"].append(key)
    # amendment-cadence read: 3+ filings = distribution likely approaching
    for cik, rec in pipe.items():
        if len(rec["filings"]) >= 3 and rec.get("status") == "REGISTERING":
            rec["status"] = "LATE-STAGE (amendments accelerating — study NOW, orphan window approaching)"
    state["asof"] = datetime.date.today().isoformat()
    STATE.write_text(json.dumps(state, indent=1))
    if fresh:
        _notify(f"NEW spinco registration(s): {'; '.join(fresh)} — study before the orphan window "
                f"(index-fund forced selling in distribution weeks 1-6). Pipeline: {len(pipe)} names.")
    late = [r["name"] for r in pipe.values() if r["status"].startswith("LATE")]
    print(f"[spinoff_watch] pipeline {len(pipe)} | new {len(fresh)} | late-stage: {late}")


if __name__ == "__main__":
    main()
