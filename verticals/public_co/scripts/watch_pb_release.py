"""
PB-release watcher — poll comptroller.war.gov + saffm.hq.af.mil for new
FY28 budget materials. Run periodically (cron / launchd / GitHub Actions).

When new content is detected, writes:
  - data/_jbook_exposure_cohort/PB_RELEASE_DETECTED.json (timestamp + URL list)

Suggested cadence: daily during Feb–May 2027 (FY28 PB window).
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path

import httpx

# Pages to check for FY28 J-Book content
WATCH_URLS = [
    "https://comptroller.war.gov/Budget-Materials/FY2028BudgetJustification/",
    "https://comptroller.war.gov/Budget-Materials/Budget2028/",
    "https://www.saffm.hq.af.mil/FM-Resources/Budget/Air-Force-Presidents-Budget-FY28/",
]

DATA = Path("verticals/public_co/data") / "_jbook_exposure_cohort"
DATA.mkdir(parents=True, exist_ok=True)
STATUS_FILE = DATA / "PB_RELEASE_DETECTED.json"

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh) AppleWebKit/605.1.15 Safari/605.1.15"}


def _check(url: str) -> dict:
    try:
        r = httpx.get(url, headers=HEADERS, timeout=20, follow_redirects=True)
        if r.status_code == 200:
            html = r.text
            # Look for FY28 PDF links
            pdfs = re.findall(r'href="([^"]+\.pdf)"[^>]*>([^<]+)</a>', html, re.IGNORECASE)
            fy28_pdfs = [
                (p, t) for p, t in pdfs
                if re.search(r"FY\s*?2028|FY?28|PB\s*?2028|PB28", p + " " + t, re.IGNORECASE)
            ]
            return {"url": url, "status": 200, "n_pdfs": len(pdfs),
                    "n_fy28_pdfs": len(fy28_pdfs),
                    "fy28_links": [{"url": p if p.startswith("http") else url + p, "label": t.strip()} for p, t in fy28_pdfs[:30]]}
        return {"url": url, "status": r.status_code, "n_pdfs": 0, "n_fy28_pdfs": 0}
    except Exception as e:
        return {"url": url, "status": "error", "error": str(e)}


def main():
    results = [_check(u) for u in WATCH_URLS]
    total_fy28 = sum(r.get("n_fy28_pdfs", 0) for r in results)

    snapshot = {
        "checked_at": datetime.utcnow().isoformat() + "Z",
        "results":    results,
        "total_fy28_pdfs_seen": total_fy28,
    }
    STATUS_FILE.write_text(json.dumps(snapshot, indent=2, default=str))

    print(f"{snapshot['checked_at']}: {total_fy28} FY28 PDFs detected across {len(results)} pages",
          file=sys.stderr)
    for r in results:
        s = r.get("n_fy28_pdfs", 0)
        st = r.get("status")
        print(f"  {r['url']:<70} → status {st}, fy28_pdfs={s}", file=sys.stderr)
        for link in r.get("fy28_links", [])[:5]:
            print(f"    • {link['label'][:60]:<60}  {link['url']}", file=sys.stderr)

    if total_fy28 > 0:
        print(f"\n🚨 FY28 PB content detected. Trigger rebalance pipeline.")
        sys.exit(0)
    else:
        print(f"\nNo FY28 content yet.")
        sys.exit(1)


if __name__ == "__main__":
    main()
