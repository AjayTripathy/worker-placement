"""Phase 2 scoring for MAUDE_VELOCITY_SPEC.md.

For each resolved Class I recall event:
  - REAL: point-in-time MAUDE velocity (date_received) in 760d pre-announcement -> spike, lead_days
  - CONTROL: a matched no-recall window (announcement - 730d) -> does the spike fire on noise?
  - LEAK-CHECK (fired subset): re-run on date_of_event -> phantom-lead inflation
Aggregate: recall (sensitivity), median lead overall & by SLOW/SUDDEN bucket, precision
(real fires / (real+control fires)), public/tradeable subset. §6 success criteria applied.
"""
import json
import sys
import time
from datetime import timedelta
from statistics import median

sys.path.insert(0, "engine")
import maude_velocity as mv

EVENTS = "outputs/maude_events.json"
OUT = "outputs/maude_backtest.json"

# Curated public US-listed device makers (firm-token -> ticker) for the tradeable subset.
PUBLIC = {
    "medtronic": "MDT", "abbott": "ABT", "boston scientific": "BSX", "insulet": "PODD",
    "tandem": "TNDM", "baxter": "BAX", "becton": "BDX", "stryker": "SYK", "edwards": "EW",
    "dexcom": "DXCM", "resmed": "RMD", "zimmer": "ZBH", "intuitive": "ISRG", "hologic": "HOLX",
    "teleflex": "TFX", "masimo": "MASI", "penumbra": "PEN", "inspire": "INSP", "nevro": "NVRO",
    "globus": "GMED", "integra": "IART", "merit medical": "MMSI", "cardinal": "CAH",
    "ge healthcare": "GEHC", "philips": "PHG", "siemens": "SMMNY", "smith": "SNN",
    "abiomed": "ABMD", "natera": "NTRA", "livanova": "LIVN", "alphatec": "ATEC",
}


def ticker_for(firm: str):
    f = (firm or "").lower()
    for k, v in PUBLIC.items():
        if k in f:
            return v
    return None


def score_event(r, *, do_leak: bool):
    init = mv._pd(r.get("recall_initiation_date"))
    if not init:
        return None
    pc = r.get("product_code")
    toks = mv.firm_tokens(r.get("recalling_firm"))
    bucket = mv.classify_root_cause_structured(
        r.get("root_cause_description") or "", r.get("reason_for_recall") or "")

    # REAL (point-in-time, date_received)
    real_dates = mv.fetch_maude_series(toks, pc, init, lookback_days=760)
    time.sleep(0.15)
    real = mv.detect_spike(real_dates, init)

    # CONTROL window: 730d earlier pseudo-announcement (no-recall regime for this cell)
    ctrl_anchor = init - timedelta(days=730)
    ctrl_dates = mv.fetch_maude_series(toks, pc, ctrl_anchor, lookback_days=760)
    time.sleep(0.15)
    ctrl = mv.detect_spike(ctrl_dates, ctrl_anchor)

    out = {
        "firm": r.get("recalling_firm"),
        "product_code": pc,
        "device_name": r.get("device_name"),
        "recall_initiation_date": r.get("recall_initiation_date"),
        "root_cause": r.get("root_cause_description"),
        "bucket": bucket,
        "ticker": ticker_for(r.get("recalling_firm")),
        "n_maude_760d": len(real_dates),
        "real_fired": real.get("fired", False),
        "real_lead_days": real.get("lead_days"),
        "real_baseline": real.get("baseline_rate"),
        "real_reason": real.get("reason"),
        "control_fired": ctrl.get("fired", False),
    }
    if do_leak and real.get("fired"):
        leak_dates = mv.fetch_maude_series(toks, pc, init, lookback_days=760,
                                           date_field="date_of_event")
        time.sleep(0.15)
        leak = mv.detect_spike(leak_dates, init)
        out["leak_fired"] = leak.get("fired", False)
        out["leak_lead_days"] = leak.get("lead_days")
    return out


def main():
    events = json.load(open(EVENTS))
    # keep only cells with a resolvable MAUDE history (>=10 in 760d gets re-checked inline)
    print(f"Scoring {len(events)} events ...", flush=True)
    rows = []
    for i, r in enumerate(events):
        try:
            res = score_event(r, do_leak=True)
        except Exception as e:
            res = None
            print(f"  [{i}] error: {e}", flush=True)
        if res:
            rows.append(res)
        if i % 15 == 0:
            print(f"  {i}/{len(events)} ...", flush=True)

    # aggregate
    resolved = [x for x in rows if x["real_reason"] != "no_maude_history"
                and x["real_reason"] != "sparse_baseline"]
    fired = [x for x in resolved if x["real_fired"] and (x["real_lead_days"] or 0) > 0]
    leads = [x["real_lead_days"] for x in fired]
    by_bucket = {}
    for b in ("SLOW_BURN", "SUDDEN", "AMBIGUOUS"):
        bl = [x["real_lead_days"] for x in fired if x["bucket"] == b]
        nres = [x for x in resolved if x["bucket"] == b]
        by_bucket[b] = {
            "n_resolved": len(nres),
            "n_fired_pos": len(bl),
            "median_lead": median(bl) if bl else None,
            "fire_rate": round(len(bl) / max(len(nres), 1), 3),
        }

    # precision via control
    real_fires = sum(1 for x in resolved if x["real_fired"] and (x["real_lead_days"] or 0) > 0)
    ctrl_fires = sum(1 for x in resolved if x["control_fired"])
    precision = round(real_fires / max(real_fires + ctrl_fires, 1), 3)

    # leak-check delta
    leakrows = [x for x in fired if "leak_lead_days" in x and x["leak_lead_days"] is not None]
    leak_delta = None
    if leakrows:
        leak_delta = round(median([x["leak_lead_days"] for x in leakrows])
                           - median([x["real_lead_days"] for x in leakrows]), 1)

    pub = [x for x in fired if x["ticker"]]

    summary = {
        "n_events": len(rows),
        "n_resolved": len(resolved),
        "n_fired_pos": len(fired),
        "sensitivity": round(len(fired) / max(len(resolved), 1), 3),
        "median_lead_days": median(leads) if leads else None,
        "lead_iqr": [min(leads), max(leads)] if leads else None,
        "precision": precision,
        "control_fires": ctrl_fires,
        "real_fires": real_fires,
        "by_bucket": by_bucket,
        "leak_check_median_inflation_days": leak_delta,
        "public_subset": {
            "n_fired_pos_public": len(pub),
            "median_lead_public": median([x["real_lead_days"] for x in pub]) if pub else None,
            "tickers": sorted({x["ticker"] for x in pub}),
        },
    }
    json.dump({"summary": summary, "rows": rows}, open(OUT, "w"), indent=2, default=str)
    print("\n=== PHASE 2 SUMMARY ===")
    print(json.dumps(summary, indent=2, default=str))
    print(f"\nWrote {OUT}")


if __name__ == "__main__":
    main()
