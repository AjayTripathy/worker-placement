"""Diff B1 vs B2 scores — which claims flipped, which composites moved."""
from __future__ import annotations

import json
from pathlib import Path

B1 = Path("verticals/public_co/data/_backtest/2024_05_17")
B2 = Path("verticals/public_co/data/_backtest/2024_05_17_v2_epa")

SEV_WEIGHT = {
    "SEVERE_UNDERDELIVERY":  1.0,
    "MODERATE_UNDERDELIVERY": 0.5,
    "RED_FLAG_NEGATIVE":      0.5,
    "PASS":                   0.0,
    "UNVERIFIABLE":           0.0,
}


def composite(scores: list[dict]) -> float:
    n = len(scores)
    if not n:
        return 0.0
    return sum(SEV_WEIGHT.get(s["severity"], 0.0) for s in scores) / n


def load_scores(path: Path) -> list[dict] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text()).get("scores", [])


def main():
    industrial = ["PLUG", "FCEL", "HYZN", "BE", "BLDP", "LIN", "APD",
                  "ENVX", "MVST", "QS", "SES", "SLDP", "ALB", "LAC"]

    print(f"{'TK':6s}  {'B1 comp':>8s}  {'B2 comp':>8s}  {'Δ':>6s}  flipped-claims")
    print("-" * 88)
    for tk in industrial:
        s1 = load_scores(B1 / f"{tk}.scores.json")
        s2 = load_scores(B2 / f"{tk}.scores.json")
        if s1 is None or s2 is None:
            print(f"  {tk:6s}  missing")
            continue
        c1 = composite(s1)
        c2 = composite(s2)
        # Find claims whose severity changed
        s1_by_cid = {s["claim_id"]: s for s in s1}
        s2_by_cid = {s["claim_id"]: s for s in s2}
        flips = []
        for cid in sorted(set(s1_by_cid) | set(s2_by_cid)):
            sev1 = s1_by_cid.get(cid, {}).get("severity", "—")
            sev2 = s2_by_cid.get(cid, {}).get("severity", "—")
            if sev1 != sev2:
                flips.append(f"{cid}:{sev1[:4]}→{sev2[:4]}")
        flip_str = ", ".join(flips) if flips else ""
        delta = c2 - c1
        arrow = "+" if delta > 0 else ("-" if delta < 0 else " ")
        print(f"  {tk:6s}  {c1:8.3f}  {c2:8.3f}  {arrow}{abs(delta):.3f}  {flip_str}")


if __name__ == "__main__":
    main()
