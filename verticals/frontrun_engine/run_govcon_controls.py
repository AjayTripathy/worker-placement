"""Phase-2 §4 controls: timing-shuffle placebo + honest clustered-N + edge(A)-edge(B).

Reads outputs/phase2_govcon_backtest.json (built by run_govcon_backtest.py) and
applies:
  - PLACEBO: shuffle the mapping signal_direction -> (rev_dir, drift) within each arm
    many times; if real hit-rate/drift is inside the shuffled null, the 'edge' is noise.
  - CLUSTERED-N: cluster events by calendar quarter (names co-move on budget cycles);
    effective independent N = number of distinct quarter-clusters, not raw event count.
  - edge(A) - edge(B) on the censored signal (the primary deliverable).
"""
import json
import random
import statistics as st
from pathlib import Path

HERE = Path(__file__).resolve().parent
random.seed(20260624)


def fired_events(bt, arm, which="censored"):
    return bt[f"{arm}_{which}"]["events"]


def hit_rate(evs):
    n = len(evs)
    return (sum(1 for e in evs if e["hit"]) / n) if n else None


def dir_drift(evs):
    ds = []
    for e in evs:
        nd = e["net_drift"]
        if nd is None:
            continue
        ds.append(nd if e["sig_dir"] == "up" else -nd)
    return ds


def placebo_hit(evs, iters=5000):
    """Null: signal direction is uninformative -> randomize predicted dir, recompute hit-rate."""
    real = hit_rate(evs)
    if real is None or not evs:
        return None
    rev_dirs = [e["rev_dir"] for e in evs]
    null = []
    for _ in range(iters):
        rnd = [random.choice(["up", "down"]) for _ in evs]
        null.append(sum(1 for p, r in zip(rnd, rev_dirs) if p == r) / len(evs))
    pct = sum(1 for x in null if x >= real) / iters
    ups = sum(1 for e in evs if e["rev_dir"] == "up") / len(evs)
    majority_base = max(ups, 1 - ups)
    return {"real_hit_rate": real, "null_mean": round(st.mean(null), 3),
            "rev_up_base_rate": round(ups, 3), "always_majority_hit": round(majority_base, 3),
            "beats_majority": real > majority_base,
            "pctile_vs_null": round(1 - pct, 3), "p_one_sided": round(pct, 4)}


def placebo_drift(evs, iters=5000):
    """Null: sign the drift randomly (direction carries no info)."""
    ds_signed = dir_drift(evs)
    if not ds_signed:
        return None
    # raw magnitudes irrespective of signal direction
    raw = []
    for e in evs:
        if e["net_drift"] is not None:
            raw.append(e["net_drift"])
    real = st.mean(ds_signed)
    null = []
    for _ in range(iters):
        null.append(st.mean([x if random.random() < 0.5 else -x for x in raw]))
    pct = sum(1 for x in null if x >= real) / iters
    return {"real_mean_dir_drift": round(real, 4), "null_mean": round(st.mean(null), 4),
            "p_one_sided": round(pct, 4), "n": len(ds_signed)}


def clustered_n(evs):
    quarters = set(e["q"] for e in evs)
    return {"raw_n": len(evs), "distinct_quarter_clusters": len(quarters),
            "effective_independent_n": len(quarters),
            "note": "names co-move on the federal budget cycle; cluster by quarter -> "
                    "effective N = distinct quarters, not raw events"}


def main():
    bt = json.load(open(HERE / "outputs" / "phase2_govcon_backtest.json"))
    out = {"as_of": bt["as_of"], "primary": "edge(ArmA) - edge(ArmB), censored signal"}

    for which in ["censored", "leaky"]:
        A = fired_events(bt, "armA", which)
        Bv = fired_events(bt, "armB", which)
        hA, hB = hit_rate(A), hit_rate(Bv)
        dA, dB = dir_drift(A), dir_drift(Bv)
        out[which] = {
            "armA": {"n": len(A), "hit_rate": hA,
                     "mean_dir_drift": round(st.mean(dA), 4) if dA else None,
                     "placebo_hit": placebo_hit(A), "placebo_drift": placebo_drift(A),
                     "clustered_n": clustered_n(A)},
            "armB": {"n": len(Bv), "hit_rate": hB,
                     "mean_dir_drift": round(st.mean(dB), 4) if dB else None,
                     "placebo_hit": placebo_hit(Bv), "placebo_drift": placebo_drift(Bv),
                     "clustered_n": clustered_n(Bv)},
            "edge_A_minus_B": {
                "hit_rate_diff": (round(hA - hB, 3) if (hA is not None and hB is not None) else None),
                "drift_diff": (round((st.mean(dA) if dA else 0) - (st.mean(dB) if dB else 0), 4)
                               if (dA or dB) else None)},
        }
    json.dump(out, open(HERE / "outputs" / "phase2_govcon_controls.json", "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
