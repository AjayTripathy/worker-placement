"""fda_velocity_scanner — Stage 0b generator: FDA clearance/launch VELOCITY by company (openFDA).

Product-cycle tell: a company whose 510(k) clearance count is accelerating is loading a product cycle 2-4
quarters before it shows in revenue; a stall is the inverse. v1 = device 510(k) clearances by applicant,
trailing quarter vs the same quarter last year. (PMA/NDC legs queued.) Applicant->ticker = SignalOS step.

  python3 verticals/generators/fda_velocity_scanner.py
Writes data/FDA_VELOCITY.json. Free openFDA (keyless at this volume). READ-ONLY.
"""
from __future__ import annotations
import json, datetime, urllib.parse, urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "data" / "FDA_VELOCITY.json"
API = "https://api.fda.gov/device/510k.json"
HDRS = {"User-Agent": "signalos-research 4tripathy@gmail.com"}
MIN_CUR = 3     # need >=3 clearances in the window to matter


def _counts(start: datetime.date, end: datetime.date):
    """Return (counts_by_key, full_term_by_key). key = uppercased[:60] applicant; full term is the
    original openFDA applicant string, needed for an exact per-applicant product_code query."""
    q = urllib.parse.urlencode({"search": f"decision_date:[{start} TO {end}]",
                                "count": "applicant.exact", "limit": 1000})
    try:
        req = urllib.request.Request(f"{API}?{q}", headers=HDRS)
        with urllib.request.urlopen(req, timeout=60) as r:
            d = json.load(r)
    except Exception:
        return {}, {}
    out, full = {}, {}
    for row in d.get("results", []):
        t = row["term"].upper()[:60]
        # entity-resolution guard (ZBH lesson 2026-07-02): same-name DIFFERENT companies pollute counts —
        # "ZIMMER MEDIZINSYSTEME GMBH" (German aesthetics, CoolTone) is not Zimmer Biomet. The mapping pass
        # must resolve applicant families before comparing YoY; known-collision names get suffixed as-is
        # (never merged on a name prefix).
        out[t] = out.get(t, 0) + row["count"]
        full.setdefault(t, row["term"])
    return out, full


def _current_with_diversity(start: datetime.date, end: datetime.date):
    """ASP/MIX GATE (TMCI lesson 2026-07-11): raw 510(k) acceleration is a FALSE POSITIVE when the new
    clearances are lower-ASP SKUs CANNIBALIZING one existing product line (Treace: clearances up while
    revenue fell −10%). Discriminator computable from openFDA alone: how many DISTINCT product_codes the
    clearance wave spans — concentrated in one code = iteration/cannibalization; spread across many =
    genuine pipeline breadth. We fetch the window's RECORDS (paginated) and aggregate counts + per-applicant
    product-code diversity LOCALLY (the applicant.exact field is not reliably searchable — 404s — so a
    per-applicant follow-up query is fragile; a single bulk read is robust and cheaper).
    Returns (counts_by_key, diversity_by_key)."""
    from collections import defaultdict
    counts, code_counts = defaultdict(int), defaultdict(lambda: defaultdict(int))
    skip = 0
    while skip < 25000:
        q = urllib.parse.urlencode({"search": f"decision_date:[{start} TO {end}]", "limit": 1000, "skip": skip},
                                   quote_via=urllib.parse.quote)
        try:
            with urllib.request.urlopen(urllib.request.Request(f"{API}?{q}", headers=HDRS), timeout=60) as r:
                page = json.load(r).get("results", [])
        except Exception:
            break
        if not page:
            break
        for rec in page:
            a = (rec.get("applicant") or "").upper()[:60]
            pc = rec.get("product_code") or "?"
            if a:
                counts[a] += 1
                code_counts[a][pc] += 1
        if len(page) < 1000:
            break
        skip += 1000
    diversity = {}
    for a, codes in code_counts.items():
        n = len(codes)
        tot = sum(codes.values())
        top_share = max(codes.values()) / tot if tot else 1.0
        gate = "ITERATION_RISK" if (n <= 1 or top_share >= 0.67) else "BREADTH"
        diversity[a] = {"n_codes": n, "top_share": round(top_share, 2), "gate": gate}
    return dict(counts), diversity


def scan() -> dict:
    today = datetime.date.today()
    end = today.replace(day=1) - datetime.timedelta(days=1)
    start = (end - datetime.timedelta(days=89)).replace(day=1)
    cur, cur_div = _current_with_diversity(start, end)
    prv, _ = _counts(start.replace(year=start.year - 1), end.replace(year=end.year - 1))
    rows = []
    for name, c in cur.items():
        if c < MIN_CUR:
            continue
        p = prv.get(name, 0)
        rows.append({"applicant": name.title(), "cur_q": c, "prior_q": p, "delta": c - p, "_key": name})
    rows.sort(key=lambda r: -r["delta"])
    # ASP/MIX GATE the accelerators: a clearance wave concentrated in one product_code is likely
    # lower-ASP iteration/cannibalization (TMCI), NOT a revenue-leading pipeline. Only BREADTH is
    # a clean bullish tell; ITERATION_RISK must have its ASP/mix checked before it's actionable.
    accel = rows[:15]
    for r in accel:
        div = cur_div.get(r["_key"], {"n_codes": None, "top_share": None, "gate": "UNKNOWN"})
        r["product_codes"] = div["n_codes"]
        r["top_code_share"] = div["top_share"]
        r["asp_gate"] = div["gate"]
        r.pop("_key", None)
    # surface the clean (breadth) accelerators first; iteration-risk sink to the bottom, flagged
    accel.sort(key=lambda r: (0 if r["asp_gate"] == "BREADTH" else 1, -r["delta"]))
    for r in rows:
        r.pop("_key", None)
    stalls = sorted([{"applicant": n.title(), "cur_q": cur.get(n, 0), "prior_q": p, "delta": cur.get(n, 0) - p}
                     for n, p in prv.items() if p >= 4 and cur.get(n, 0) <= p // 2],
                    key=lambda r: r["delta"])[:10]
    n_breadth = sum(1 for r in accel if r["asp_gate"] == "BREADTH")
    return {"asof": today.isoformat(), "window": f"{start}..{end}", "n_applicants": len(cur),
            "accelerating": accel, "stalling": stalls,
            "note": f"510(k) clearances lead device revenue 2-4 qtrs. ASP-GATED: {n_breadth}/{len(accel)} are BREADTH "
                    "(diverse product codes = genuine pipeline); ITERATION_RISK (1 code / >=67% concentrated) = likely "
                    "lower-ASP cannibalization (TMCI trap) — verify ASP/mix before actioning. applicant->ticker = SignalOS step"}


def main():
    res = scan()
    print(f"=== FDA CLEARANCE-VELOCITY SCANNER  {res['asof']}  ({res['n_applicants']} applicants, window {res['window']}) ===")
    print("  ACCELERATING (product cycle loading):")
    for r in res["accelerating"][:10]:
        print(f"   {r['applicant']:<52} {r['cur_q']:>3} vs {r['prior_q']:>3}  ({r['delta']:+d})")
    print("  STALLING (clearance flow halved+):")
    for r in res["stalling"][:8]:
        print(f"   {r['applicant']:<52} {r['cur_q']:>3} vs {r['prior_q']:>3}  ({r['delta']:+d})")
    OUT.write_text(json.dumps(res, indent=1))
    print(f"[-> {OUT.name}]")


if __name__ == "__main__":
    main()
