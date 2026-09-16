"""hiring_velocity — track an employer's job-posting velocity + role-mix at a SITE over time, as a
free "workforce ramp" proxy for a plant coming online. Built for the Stevanato/Ompi Fishers GLP-1
plant-ramp monitor (2026-06), after the satellite-thermal furnace sensor was control-refuted and
free phone/foot-traffic came up empty.

THESIS: a plant ramping from construction to full 24/7 production HIRES IN A WAVE — production
operators, technicians, QC, shift crews — then the postings TAPER as it approaches full staffing.
So (count of open production roles) + (role mix, production-heavy vs overhead) + (posting velocity)
front-runs the utilization/margin inflection. Heavy operator/tech postings = mid-ramp; drying up =
nearing full staff = inflection approaching.

SOURCE: LinkedIn guest jobs endpoint (no auth, posting dates included). Filter to the employer +
site. CAVEAT: a single ~300-person plant posts a small, lumpy number of reqs — read the TREND across
snapshots, not one pull. Stand up the forward snapshot log (run_hiring.py) to accrue velocity.
"""

from __future__ import annotations

# Knowledge-graph dispatch contract (see knowledge_graph/dispatch.py) — added 2026-07-29 gap-close.
APPLIES_TO = {
    "kind": 'm_source',
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": ['capacity_ramp_claim', 'physical_plant_operations'],
    "asset_classes": ['corporate_ipo_dd'],
    "applies_universally": False,
    "summary": 'Job-posting wave/taper at a named site: leading utilization proxy for ramp claims.',
}

import re
import time
import urllib.parse
from collections import Counter
from datetime import date, datetime
from typing import Optional

import requests

from .base import (BaseConnector, ConnectorObservation, ConnectorRequest,
                   ConnectorResult, ErrorKind)

_GUEST = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

# production / floor roles whose posting wave = the plant ramp
_PROD = ("operator", "production", "technician", "maintenance", "machine", "line ", "shift",
         "manufacturing", "assembly", "packaging", "warehouse", "molding", "forming", "inspector",
         "quality control", "qc ", "qa ", "logistics", "material handler", "cleanroom")
_OVERHEAD = ("engineer", "manager", "director", "finance", "human resources", " hr ", "sales",
             "marketing", "analyst", "accountant", "it ", "planner", "specialist", "coordinator",
             "administrator", "buyer", "controller", "counsel")


def _classify(title: str) -> str:
    t = " " + (title or "").lower() + " "
    if any(k in t for k in _PROD):
        return "production"
    if any(k in t for k in _OVERHEAD):
        return "overhead"
    return "other"


def _parse_cards(html: str) -> list[dict]:
    out = []
    for c in html.split('<div class="base-card')[1:]:
        title = re.search(r'base-search-card__title">\s*(.*?)\s*</h3>', c, re.S)
        comp = re.search(r'base-search-card__subtitle">.*?>\s*(.*?)\s*</a>', c, re.S)
        loc = re.search(r'job-search-card__location"?>\s*(.*?)\s*</span>', c, re.S)
        dt = re.search(r'datetime="([0-9\-]+)"', c)
        link = re.search(r'base-card__full-link[^>]*href="([^"?]+)', c)
        if not title:
            continue
        out.append({"title": re.sub(r"\s+", " ", title.group(1)).strip(),
                    "company": re.sub(r"\s+", " ", comp.group(1)).strip() if comp else "",
                    "location": re.sub(r"\s+", " ", loc.group(1)).strip() if loc else None,
                    "posted": dt.group(1) if dt else None,
                    "url": link.group(1) if link else None})
    return out


def fetch_postings(keywords: str, location: str, *, company_filter: tuple[str, ...] = (),
                   max_pages: int = 8) -> list[dict]:
    """LinkedIn guest job postings for keywords+location, optionally filtered to company tokens."""
    sess = requests.Session()
    sess.headers.update({"User-Agent": _UA})
    seen, rows = set(), []
    for start in range(0, max_pages * 25, 25):
        params = {"keywords": keywords, "location": location, "start": start}
        try:
            r = sess.get(_GUEST, params=params, timeout=20)
        except Exception:
            break
        if r.status_code != 200 or "base-card" not in r.text:
            break
        page = _parse_cards(r.text)
        if not page:
            break
        for p in page:
            key = (p["title"], p["company"], p.get("url"))
            if key in seen:
                continue
            seen.add(key)
            if company_filter and not any(c in p["company"].lower() for c in company_filter):
                continue
            rows.append(p)
        time.sleep(0.8)
    return rows


def ramp_metrics(rows: list[dict]) -> dict:
    mix = Counter(_classify(r["title"]) for r in rows)
    dated = [r["posted"] for r in rows if r.get("posted")]
    by_month = Counter(d[:7] for d in dated)
    today = max([date.fromisoformat(d) for d in dated], default=None)
    recent30 = sum(1 for d in dated if today and (today - date.fromisoformat(d)).days <= 30)
    return {
        "n_open": len(rows),
        "role_mix": dict(mix),
        "production_share": round(mix["production"] / max(len(rows), 1), 2),
        "postings_by_month": dict(sorted(by_month.items())),
        "posted_last_30d": recent30,
        "newest": max(dated) if dated else None,
        "oldest": min(dated) if dated else None,
    }


class HiringVelocityConnector(BaseConnector):
    source_id = "hiring_velocity"

    def query(self, request: ConnectorRequest) -> ConnectorResult:
        x = request.extra or {}
        kw = x.get("keywords") or request.entity_name
        loc = x.get("location") or request.city
        if not kw or not loc:
            return self._fail(request, ErrorKind.UNSUPPORTED,
                              "hiring_velocity needs extra.keywords + extra.location")
        cf = tuple(c.lower() for c in (x.get("company_filter") or []))
        rows = fetch_postings(kw, loc, company_filter=cf, max_pages=int(x.get("max_pages", 8)))
        if not rows:
            return self._fail(request, ErrorKind.NOT_FOUND, "no postings (filtered) — check keywords/filter")
        m = ramp_metrics(rows)
        return self._ok(request, [
            ConnectorObservation(attribute="open_reqs", value=m["n_open"], confidence=0.7,
                                 extra={"role_mix": m["role_mix"],
                                        "production_share": m["production_share"],
                                        "posted_last_30d": m["posted_last_30d"]}),
            ConnectorObservation(attribute="hiring_by_month", value=m["postings_by_month"]),
            ConnectorObservation(attribute="postings", value=rows[:40]),
        ])


if __name__ == "__main__":
    import json, sys
    rows = fetch_postings("Stevanato OR Ompi", "Fishers, Indiana",
                          company_filter=("stevanato", "ompi"))
    print(f"{len(rows)} Stevanato/Ompi postings near Fishers")
    for r in sorted(rows, key=lambda z: z.get("posted") or "", reverse=True):
        print(f"  {r.get('posted') or '????-??-??'}  [{_classify(r['title'])[:4]}]  "
              f"{r['title'][:48]:48} | {r['company'][:22]} | {r.get('location')}")
    print("\nRAMP METRICS:", json.dumps(ramp_metrics(rows), indent=2))
