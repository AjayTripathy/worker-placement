"""Google Patents JSON XHR endpoint (USPTO PatentsView retired 2024)."""

from __future__ import annotations

APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": ["patent_portfolio_claim"],
    "asset_classes": ["public_equity_forensics"],
    "applies_universally": False,
    "kind": "m_source",
    "summary": "Google Patents XHR search (rate-limited; superseded by uspto_odp) for patent-portfolio claims.",
}

import urllib.parse

import httpx

UA = {"User-Agent": "Mozilla/5.0"}


def query_assignee(assignee_name: str, cutoff_date: str, categorize: dict[str, list[str]] | None = None) -> dict:
    """Granted patents by assignee with priority date before cutoff.

    categorize: optional {bucket_name: [keyword, ...]} — counts patents whose
    title contains any keyword. First match wins; remainder bucketed as 'other'.
    """
    cutoff_compact = cutoff_date.replace("-", "")
    q = f'assignee="{assignee_name}"&before=priority:{cutoff_compact}'
    url = f"https://patents.google.com/xhr/query?url={urllib.parse.quote(q)}&exp="
    try:
        with httpx.Client(timeout=30, headers=UA) as c:
            r = c.get(url)
            if r.status_code != 200:
                return {"error": f"status_{r.status_code}"}
            data = r.json()
    except Exception as e:
        return {"error": str(e)}

    results = data.get("results", {})
    total = results.get("total_num_results", 0)
    patents = []
    for cluster in results.get("cluster", []) or []:
        for item in cluster.get("result", []) or []:
            p = item.get("patent", {})
            patents.append({
                "patent_id": p.get("publication_number"),
                "title": (p.get("title") or "").strip(),
                "priority_date": p.get("priority_date"),
                "publication_date": p.get("publication_date"),
                "assignee_original": p.get("assignee"),
                "snippet": (p.get("snippet") or "")[:200].strip(),
            })

    out = {
        "assignee_searched": assignee_name,
        "total_granted_patents_pre_cutoff": total,
        "patents": patents[:15],
    }
    if categorize:
        cat_counts = {b: 0 for b in categorize}
        cat_counts["other"] = 0
        for p in patents:
            t = p["title"].lower()
            matched = False
            for bucket, keywords in categorize.items():
                if any(k in t for k in keywords):
                    cat_counts[bucket] += 1
                    matched = True
                    break
            if not matched:
                cat_counts["other"] += 1
        out["category_counts"] = cat_counts
    return out
