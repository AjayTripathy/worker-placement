"""run_hiring — daily snapshot of Stevanato/Ompi Fishers hiring velocity (plant-ramp proxy).
Appends a snapshot to hiring_velocity_log.jsonl so velocity accrues forward; prints the current
read + trend across snapshots. READ-ONLY. Cron it like the social engine for a standing signal."""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from verticals.buyside_dd.connectors.hiring_velocity import fetch_postings, ramp_metrics, _classify

LOG = Path(__file__).resolve().parent / "hiring_velocity_log.jsonl"

# Stevanato ramping plants to monitor (site label -> LinkedIn location string)
SITES = [("Stevanato Fishers IN", "Fishers, Indiana"),
         ("Stevanato Latina IT", "Latina, Italy")]


def main():
    asof = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    for label, loc in SITES:
        rows = fetch_postings("Stevanato OR Ompi", loc, company_filter=("stevanato", "ompi"))
        m = ramp_metrics(rows)
        snap = {"asof": asof, "site": label, "source": "linkedin_guest", **m,
                "titles": [{"t": r["title"], "cls": _classify(r["title"]), "posted": r.get("posted")}
                           for r in rows]}
        with open(LOG, "a") as f:
            f.write(json.dumps(snap, default=str) + "\n")
        print(f"=== {label} — hiring snapshot {asof} ===")
        print(f"open reqs: {m['n_open']} | production share: {m['production_share']:.0%} "
              f"| last-30d: {m['posted_last_30d']} | mix: {m['role_mix']}")
        for r in sorted(rows, key=lambda z: z.get("posted") or "", reverse=True)[:10]:
            print(f"  {r.get('posted') or '?':10} [{_classify(r['title'])[:4]:4}] {r['title'][:50]}")
        # trend for this site across snapshots
        hist = [json.loads(l) for l in LOG.read_text().splitlines() if l.strip()]
        sh = [h for h in hist if h.get("site") == label]
        if len(sh) > 1:
            print("  TREND:", " -> ".join(f"{h['asof'][5:]}:{h['n_open']}r/{h.get('production_share',0):.0%}p" for h in sh[-6:]))
        print()
    print(f"[-> {LOG}]  (cron weekly to accrue ramp/taper velocity)")


if __name__ == "__main__":
    main()
