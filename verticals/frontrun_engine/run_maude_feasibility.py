"""Phase 1 feasibility for MAUDE_VELOCITY_SPEC.md — report BEFORE scoring.

(a) Class-I universe size + product_code enrichment rate (enforcement -> recall.json Z-join)
(b) MAUDE reporting-lag distribution (date_received - date_of_event) — the make-or-break number
(c) (firm x product_code) -> MAUDE-history resolution rate
"""
import json
import sys
import time
from collections import Counter

sys.path.insert(0, "engine")
import maude_velocity as mv

OUT = "outputs/maude_feasibility.json"
START, END = "2015-01-01", "2024-12-31"


def main():
    rep = {"asof": "2026-06-25", "spec": "MAUDE_VELOCITY_SPEC.md", "window": [START, END]}

    total = mv.class1_total(START, END)
    print(f"Class I device recall records {START}..{END}: {total}", flush=True)
    rep["class1_total_records"] = total

    print("Fetching Class I enforcement records (cap 600) ...", flush=True)
    recalls = mv.fetch_class1_recalls(START, END, limit_total=600)
    print(f"  fetched: {len(recalls)}", flush=True)

    # enrich product_code via Z-number join on a capped sample (API budget)
    N_ENRICH = 160
    print(f"Enriching product_code on {min(N_ENRICH,len(recalls))} via recall.json Z-join ...", flush=True)
    enriched = []
    for r in recalls[:N_ENRICH]:
        z = r.get("recall_number")
        if not z:
            continue
        pc = mv.enrich_product_code(z)
        if pc and pc.get("product_code"):
            r.update(pc)
            enriched.append(r)
        time.sleep(0.15)
    rep["n_enrich_attempted"] = min(N_ENRICH, len(recalls))
    rep["n_product_code_resolved"] = len(enriched)
    rep["product_code_resolution_rate"] = round(len(enriched) / max(min(N_ENRICH, len(recalls)), 1), 3)

    # dedup to events: (firm, product_code, init-month) -> earliest
    events = {}
    for r in enriched:
        pc = r.get("product_code")
        init = r.get("recall_initiation_date") or ""
        firm = (r.get("recalling_firm") or "").strip()
        if not pc or not init or not firm:
            continue
        key = (firm.lower(), pc, init[:6])
        if key not in events or init < events[key]["recall_initiation_date"]:
            events[key] = r
    rep["n_dedup_events"] = len(events)

    # root-cause buckets (structured field)
    buckets = Counter()
    rc_raw = Counter()
    for r in events.values():
        rc_raw[r.get("root_cause_description") or "(none)"] += 1
        buckets[mv.classify_root_cause_structured(
            r.get("root_cause_description") or "", r.get("reason_for_recall") or "")] += 1
    rep["root_cause_buckets"] = dict(buckets)
    rep["root_cause_raw_top"] = rc_raw.most_common(15)

    pc_counts = Counter(r["product_code"] for r in events.values())
    top_codes = [pc for pc, _ in pc_counts.most_common(12)]
    rep["top_product_codes"] = pc_counts.most_common(12)

    # (b) reporting lag
    print(f"Measuring MAUDE reporting lag on {len(top_codes)} product codes ...", flush=True)
    rep["reporting_lag"] = mv.measure_reporting_lag(top_codes, per_code=100)
    print(f"  lag: {rep['reporting_lag']}", flush=True)

    # (c) join resolution: does the cell have >=10 MAUDE reports in 760d pre-window?
    sample = list(events.values())[:40]
    print(f"Probing MAUDE resolution on {len(sample)} events ...", flush=True)
    resolved = 0
    rows = []
    for r in sample:
        pc = r["product_code"]
        init = mv._pd(r["recall_initiation_date"])
        if not init:
            continue
        toks = mv.firm_tokens(r["recalling_firm"])
        dates = mv.fetch_maude_series(toks, pc, init, lookback_days=760)
        ok = len(dates) >= 10
        resolved += int(ok)
        rows.append({"firm": r["recalling_firm"][:36], "pc": pc, "tokens": toks,
                     "n_maude_760d": len(dates), "resolved": ok,
                     "bucket": mv.classify_root_cause_structured(
                         r.get("root_cause_description") or "", r.get("reason_for_recall") or "")})
        time.sleep(0.15)
    rep["join_probe"] = {
        "n_sampled": len(sample),
        "n_resolved_ge10": resolved,
        "resolution_rate": round(resolved / max(len(sample), 1), 3),
        "rows": rows,
    }

    # persist the enriched events for Phase 2 (avoid re-fetching)
    with open("outputs/maude_events.json", "w") as f:
        json.dump(list(events.values()), f, indent=2, default=str)

    with open(OUT, "w") as f:
        json.dump(rep, f, indent=2, default=str)
    print(f"\nWrote {OUT} and outputs/maude_events.json ({len(events)} events)")
    show = {k: v for k, v in rep.items() if k not in ("join_probe",)}
    print(json.dumps(show, indent=2, default=str))
    print("\nJOIN PROBE resolution rate:", rep["join_probe"]["resolution_rate"])


if __name__ == "__main__":
    main()
