"""Measure how common INSIDER SHARE PLEDGES are in small/mid-cap proxies.

Purpose: size the long-term applicability of the ucc_financing_statement
M-source. That source only fires when an insider pledges company stock against
personal debt. This script samples S&P 600 names, pulls each one's latest
DEF 14A, and classifies the pledge disclosure into:

  AFFIRMATIVE_PLEDGE  — at least one insider actually has shares pledged as
                        collateral / in a margin account (the case the source
                        is built for).
  ANTI_PLEDGE_POLICY  — the proxy only mentions pledging to PROHIBIT it
                        (governance boilerplate; NOT a pledge).
  NO_MENTION          — no collateral-pledge language at all.

The affirmative/prohibition split is the whole validity question: a naive
full-text count of "pledge" wildly overstates prevalence because the modal
mention is an anti-pledging policy.
"""
from __future__ import annotations

import json
import random
import re
import sys
import time
from pathlib import Path

from .edgar import list_filings, fetch_filing_text

UNIVERSE = (Path(__file__).parent / "data" / "_smallcap_universe" / "sp600_enriched.json")

_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")
_NBSP = re.compile(r"&#160;|&nbsp;|&#xa0;", re.I)

# Affirmative collateral-pledge phrases (insider stock actually used as loan
# collateral). Deliberately NARROW: bare "margin account" / "shares pledged"
# are too noisy (they dominate anti-pledge policy text), so affirmative requires
# explicit collateral/security framing or a quantified pledge (handled below).
_AFF = re.compile(
    r"pledged as collateral|pledged as security|pledged to secure|"
    r"pledged in connection with|pledged .{0,25}? to secure|"
    r"pledged .{0,25}? as security|pledged .{0,25}? as collateral|"
    r"currently held in (?:a )?margin account|"
    r"are held in (?:a )?margin account|"
    r"shares .{0,20}? are pledged|have pledged .{0,30}? shares",
    re.I,
)
# Prohibition / policy language — these are NOT pledges.
_PROHIB = re.compile(
    r"prohibit|may not pledge|not permitted to pledge|are prohibited from|"
    r"policy .{0,40}? pledg|anti-?pledg|no .{0,20}? may pledge|"
    r"restrict .{0,20}? pledg|forbid|prohibits .{0,30}? pledg|"
    r"from pledging|from hedging or pledging|hedging .{0,10}? pledging|"
    r"may not be .{0,25}? pledged|may not be margined|shall not pledge|"
    r"are restricted from|unless .{0,30}? approved",
    re.I,
)
# Ownership-guideline / policy carve-out language: describes pledged shares as a
# CATEGORY (e.g. "shares that are pledged do not count toward ownership
# guidelines") rather than disclosing an actual insider holding. Suppresses
# affirmative when present in the window.
_EXCLUDE = re.compile(
    r"ownership guideline|do not qualify|do not count|does not count|"
    r"count toward|counted toward|satisfaction of .{0,20}? guideline|"
    r"toward .{0,20}? ownership|excluded from .{0,20}? ownership",
    re.I,
)
# Negation — "no insider HAS pledged", "have not pledged", etc. Kills affirmative.
_NEG = re.compile(
    r"no (?:director|executive|officer|named|member|nominee|shares)|"
    r"have not pledged|has not pledged|did not pledge|not pledged any|"
    r"none of (?:our|the|its)|are not pledged|not been pledged|"
    r"no .{0,30}? (?:have|has) pledged|do not hold .{0,20}? pledge|"
    r"have (?:hedged or )?pledged any of",
    re.I,
)
# Number-of-shares-pledged extractor (tolerates "of such"/"common"/"Class A" filler).
_SHARES = re.compile(
    r"([\d,]{4,})\s+(?:of such |common |class [a-z] |shares of )*(?:common )?shares?"
    r"[^.]{0,80}?pledg", re.I)
_SHARES2 = re.compile(r"pledg[^.]{0,80}?([\d,]{4,})\s+(?:common )?shares?", re.I)


def _strip(html: str) -> str:
    t = _NBSP.sub(" ", html)
    t = _TAG.sub(" ", t)
    return _WS.sub(" ", t)


def classify(text: str) -> dict:
    """Per-occurrence classification of 'pledg' contexts in proxy text."""
    low = text.lower()
    aff_hits, pro_hits = [], []
    for m in re.finditer(r"pledg", low):
        a, b = max(0, m.start() - 180), min(len(low), m.end() + 180)
        win = low[a:b]
        is_pro = bool(_PROHIB.search(win))
        is_neg = bool(_NEG.search(win))
        is_excl = bool(_EXCLUDE.search(win))
        is_aff = bool(_AFF.search(win))
        if is_aff and not is_pro and not is_neg and not is_excl:
            aff_hits.append(win)
        elif is_pro:
            pro_hits.append(win)
    shares = None
    if aff_hits:
        for rx in (_SHARES, _SHARES2):
            mm = rx.search(text)
            if mm:
                try:
                    shares = int(mm.group(1).replace(",", ""))
                    break
                except ValueError:
                    pass
    if aff_hits:
        cat = "AFFIRMATIVE_PLEDGE"
    elif pro_hits:
        cat = "ANTI_PLEDGE_POLICY"
    else:
        cat = "NO_MENTION"
    return {"category": cat, "n_affirmative": len(aff_hits),
            "n_prohibition": len(pro_hits), "shares_pledged": shares,
            "evidence": (aff_hits[0][:200] if aff_hits else "")}


def latest_proxy(cik: str):
    try:
        name, rows = list_filings(cik)
    except Exception as e:
        return None, None, f"list_error: {e}"
    proxies = [r for r in rows if r["form"] == "DEF 14A"]
    if not proxies:
        proxies = [r for r in rows if r["form"].startswith("DEF 14A")]
    if not proxies:
        return name, None, "no_def14a"
    proxies.sort(key=lambda r: r["filing_date"], reverse=True)
    return name, proxies[0], None


def _wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float, float]:
    if n == 0:
        return 0.0, 0.0, 0.0
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = (z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5)) / denom
    return p, max(0.0, centre - half), min(1.0, centre + half)


def run(n: int = 150, seed: int = 42, out: str | None = None) -> dict:
    universe = json.loads(UNIVERSE.read_text())
    random.seed(seed)
    sample = random.sample(universe, min(n, len(universe)))
    results, errors = [], []
    cats = {"AFFIRMATIVE_PLEDGE": 0, "ANTI_PLEDGE_POLICY": 0, "NO_MENTION": 0}
    by_sector_aff: dict[str, int] = {}
    by_sector_tot: dict[str, int] = {}
    for i, co in enumerate(sample):
        cik = co["cik"]
        name, proxy, err = latest_proxy(cik)
        if err or not proxy:
            errors.append({"ticker": co["ticker"], "err": err})
            print(f"[{i+1}/{len(sample)}] {co['ticker']:6} SKIP {err}", file=sys.stderr)
            continue
        html = fetch_filing_text(cik, proxy["accession"], proxy["primary_document"])
        if not html:
            errors.append({"ticker": co["ticker"], "err": "fetch_fail"})
            continue
        c = classify(_strip(html))
        cats[c["category"]] += 1
        sec = co.get("sector") or "?"
        by_sector_tot[sec] = by_sector_tot.get(sec, 0) + 1
        rec = {"ticker": co["ticker"], "name": co["name"], "sector": sec,
               "market_cap_B": round(co.get("market_cap_B") or 0, 2),
               "proxy_date": proxy["filing_date"], **c}
        del rec["evidence"]
        if c["category"] == "AFFIRMATIVE_PLEDGE":
            by_sector_aff[sec] = by_sector_aff.get(sec, 0) + 1
            rec["evidence"] = c["evidence"]
        results.append(rec)
        flag = "  <== PLEDGE" if c["category"] == "AFFIRMATIVE_PLEDGE" else ""
        print(f"[{i+1}/{len(sample)}] {co['ticker']:6} {c['category']:18}"
              f" aff={c['n_affirmative']} pro={c['n_prohibition']}{flag}", file=sys.stderr)
        time.sleep(0.1)

    n_classified = sum(cats.values())
    k_aff = cats["AFFIRMATIVE_PLEDGE"]
    p, lo, hi = _wilson(k_aff, n_classified)
    summary = {
        "n_sampled": len(sample),
        "n_classified": n_classified,
        "n_errors": len(errors),
        "categories": cats,
        "affirmative_pledge_rate": round(p, 4),
        "affirmative_pledge_ci95": [round(lo, 4), round(hi, 4)],
        "anti_policy_rate": round(cats["ANTI_PLEDGE_POLICY"] / n_classified, 4) if n_classified else 0,
        "by_sector_affirmative": dict(sorted(by_sector_aff.items(), key=lambda x: -x[1])),
        "by_sector_total": by_sector_tot,
        "affirmative_names": [r for r in results if r["category"] == "AFFIRMATIVE_PLEDGE"],
    }
    if out:
        Path(out).write_text(json.dumps({"summary": summary, "all_results": results,
                                          "errors": errors}, indent=2))
    return summary


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 150
    s = run(n=n, out="verticals/public_co/data/_smallcap_universe/pledge_prevalence.json")
    print(json.dumps(s, indent=2))
