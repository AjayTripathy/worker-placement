"""nongaap_adjustment_gap — honesty detector: fires when a company's headline metric is flattered
by an OUTSIZED non-GAAP adjustment vs its peers, and especially when that adjustment FLIPS its
peer rank (worse-than-peers on GAAP, but at/above peers on the marketed "adjusted" figure).

WHY IT'S A DETECTOR, NOT JUST A RATIO. Every company has some non-GAAP adjustments — that alone is
not a signal. The discriminating, high-precision tell is being a PEER-RELATIVE OUTLIER: the company
needs a bigger add-back than its competitors to reach a comparable headline number, so a peer
comparison done on the *adjusted* numbers overstates its relative quality. The killer condition is
the RANK FLIP — the company looks BEST-in-group on adjusted while sitting MID/BOTTOM on GAAP. That
is the masked-takeaway-vs-data divergence the honesty framework exists to catch.

Surfaced 2026-06-09 from the Palomar (PLMR) comp screen: adjusted combined ratio 76.0% (best-looking
in the specialty-P&C group) vs GAAP 84.5% (2nd-worst) — an 8.5pt gap, widest in the peer set, that
flips its rank vs Kinsale (which has ~0 adjustment gap).

GENERALIZES: insurance (adjusted vs GAAP combined ratio / ROE), software & tech (adjusted EBITDA /
non-GAAP EPS / "adjusted operating margin" vs GAAP — SBC + recurring "one-time" add-backs), any
sector with a marketed non-GAAP headline.

CONTRACT: evaluate(subject_name, data) -> {fires, reason, severity, evidence}. Same shape as the
muni detectors; APPLIES_TO any equity that reports a non-GAAP headline alongside GAAP.
"""

from __future__ import annotations

APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": [],
    "asset_classes": ["public_equity_forensics"],
    "applies_universally": True,
    "kind": "detector",
    "summary": "Peer-relative non-GAAP add-back outlier + GAAP/adjusted rank-flip; the marketed-takeaway divergence detector.",
}
import statistics

# metric -> +1 if HIGHER is better, -1 if LOWER is better
METRIC_DIR = {
    "roe": 1, "eps": 1, "ebitda_margin": 1, "operating_margin": 1, "net_margin": 1, "fcf": 1,
    "combined_ratio": -1, "expense_ratio": -1, "loss_ratio": -1,
}


def _flatter(adjusted, gaap, direction):
    """How much the adjustment improves the metric in the FAVORABLE direction (>=0 = flattering)."""
    return (adjusted - gaap) * direction


def _better(a, b, direction):
    return (a - b) * direction > 0


def evaluate(subject_name: str, data: dict) -> dict:
    """
    data = {
      "metric": "combined_ratio" | "roe" | "ebitda_margin" | ...,
      "adjusted": float, "gaap": float,                 # subject's marketed vs GAAP figure
      "peers": [{"name": str, "adjusted": float|None, "gaap": float}, ...],
      "abs_threshold": float (optional, metric units; default 3.0),
      "rel_mult": float (optional; default 1.5),
    }
    A peer with no non-GAAP adjustment passes adjusted == gaap (or adjusted None).
    """
    metric = data.get("metric"); direction = METRIC_DIR.get(metric, 1)
    adj, gaap = data.get("adjusted"), data.get("gaap")
    if adj is None or gaap is None:
        return {"fires": False, "reason": "INSUFFICIENT_DATA", "evidence": {"metric": metric}}

    sub_gap = _flatter(adj, gaap, direction)
    peers = [p for p in data.get("peers", []) if p.get("gaap") is not None]
    peer_gaps = [_flatter(p.get("adjusted", p["gaap"]) if p.get("adjusted") is not None else p["gaap"],
                          p["gaap"], direction) for p in peers]
    peer_med_gap = statistics.median(peer_gaps) if peer_gaps else 0.0
    pct = round(100 * sum(1 for g in peer_gaps if sub_gap > g) / len(peer_gaps), 0) if peer_gaps else None

    # rank flip (the killer signal): the adjustment vaults the subject INTO the top quartile of peers
    # it does not earn on GAAP. Benchmark = the top-quartile peer (best 25%), not the median, so a
    # peer set padded with weak names can't hide the flip. Fires when: subject NOT better than the
    # top-quartile peer on GAAP, but IS better than it on the marketed adjusted figure.
    rank_flip = False; peer_gaap_q = peer_adj_q = None
    if peers:
        g = sorted((p["gaap"] for p in peers), reverse=(direction > 0))                 # best-first
        a = sorted((p.get("adjusted", p["gaap"]) if p.get("adjusted") is not None else p["gaap"]
                    for p in peers), reverse=(direction > 0))
        qi = max(0, int(round(0.25 * (len(peers) - 1))))
        peer_gaap_q, peer_adj_q = g[qi], a[qi]
        rank_flip = (not _better(gaap, peer_gaap_q, direction)) and _better(adj, peer_adj_q, direction)

    abs_thr = data.get("abs_threshold", 3.0); rel_mult = data.get("rel_mult", 1.5)
    outsized = sub_gap >= abs_thr and (not peer_gaps or sub_gap >= rel_mult * max(0.01, peer_med_gap))

    if not (outsized or rank_flip):
        return {"fires": False, "reason": "ADJUSTMENT_IN_LINE_WITH_PEERS",
                "evidence": {"metric": metric, "subject_gap": round(sub_gap, 2),
                             "peer_median_gap": round(peer_med_gap, 2), "gap_percentile_vs_peers": pct}}

    big = peer_med_gap > 0.05 and sub_gap >= 2 * peer_med_gap
    severity = "HIGH" if (rank_flip and (big or peer_med_gap <= 0.05)) else ("REVIEW" if (rank_flip or big) else "LOW")
    reason = "ADJUSTMENT_FLIPS_PEER_RANK" if rank_flip else "OUTSIZED_ADJUSTMENT_GAP_VS_PEERS"
    if rank_flip:
        interp = (f"On the marketed adjusted {metric} the company ranks in the peer top quartile, but on "
                  f"GAAP it does not — the {round(sub_gap,1)}-pt adjustment is doing the work of making it "
                  f"look best-in-class. Peer comparison done on adjusted numbers overstates its quality.")
    elif peer_med_gap <= 0.05:
        interp = (f"Peers barely adjust ({metric} gap median ~0), but this company adds back {round(sub_gap,1)} "
                  f"to its headline — an absolute outlier in non-GAAP reliance.")
    else:
        interp = (f"Adjustment gap ({round(sub_gap,1)}) is {round(sub_gap/peer_med_gap,1)}x the peer median "
                  f"({round(peer_med_gap,1)}) — outsized reliance on non-GAAP framing.")
    return {"fires": True, "reason": reason, "severity": severity,
            "evidence": {"metric": metric, "adjusted": adj, "gaap": gaap,
                         "subject_flattering_gap": round(sub_gap, 2), "peer_median_gap": round(peer_med_gap, 2),
                         "gap_percentile_vs_peers": pct, "rank_flip": rank_flip,
                         "subject_gaap": gaap, "peer_top_quartile_gaap": round(peer_gaap_q, 2) if peer_gaap_q is not None else None,
                         "subject_adjusted": adj, "peer_top_quartile_adjusted": round(peer_adj_q, 2) if peer_adj_q is not None else None,
                         "interpretation": interp}}


if __name__ == "__main__":
    # Demo on the 2026-06-09 PLMR specialty-P&C comp screen (peers report GAAP; ~0 adjustment gap).
    CR = {"metric": "combined_ratio", "adjusted": 76.0, "gaap": 84.5,
          "peers": [{"name": "KNSL", "gaap": 77.4}, {"name": "RLI", "gaap": 86.0},
                    {"name": "SKWD", "gaap": 89.5}, {"name": "HCI", "gaap": 57.0},
                    {"name": "UVE", "gaap": 89.7}]}
    ROE = {"metric": "roe", "adjusted": 26.0, "gaap": 20.6,
           "peers": [{"name": "KNSL", "gaap": 26.8}, {"name": "RLI", "gaap": 22.0},
                     {"name": "SKWD", "gaap": 14.5}, {"name": "HCI", "gaap": 29.8},
                     {"name": "UVE", "gaap": 33.5}]}
    # a control: a peer with no adjustment should NOT fire
    KNSL = {"metric": "combined_ratio", "adjusted": 77.4, "gaap": 77.4,
            "peers": [{"name": "PLMR", "adjusted": 76.0, "gaap": 84.5}, {"name": "RLI", "gaap": 86.0}]}
    for name, d in [("PLMR combined_ratio", CR), ("PLMR roe", ROE), ("KNSL combined_ratio (control)", KNSL)]:
        r = evaluate(name, d)
        print(f"{name:32} fires={r['fires']!s:5} {r.get('severity','-'):6} {r['reason']}")
        if r["fires"]:
            print(f"   {r['evidence']['interpretation']}")
