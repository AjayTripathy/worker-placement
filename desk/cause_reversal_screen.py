"""cause_reversal_screen — mechanizes the BSY pattern, the campaign's one dislocation BUY:
a dated break whose named cause has since REVERSED while the price hasn't.

BSY signature (court 2026-08-07): broke Nov-2025 on cc-ARR deceleration (11.5->10.5);
the metric then ran 11.5 -> 11.5 -> 12.0 (series high) while the stock sat -32% below
pre-break. The courts found it manually; this screen finds candidates mechanically:

  universe   the discovery blob (names >=20% off highs, mcap >= $250M)
  series     revenue quarterly from the evidence-pack XBRL plumbing (audited values)
  signature  (a) a trough quarter exists in the drawdown window (growth deceleration),
             (b) the LATEST 1-2 quarters re-accelerated ABOVE the pre-trough rate,
             (c) price still deep below the high (the market hasn't marked the reversal)
  output     candidates -> desk/data/cause_reversal.json + optional conveyor enqueue
             (growth re-acceleration is the crude v1 proxy; the COURT verifies the true
              named break metric — ARR, bookings, NRR — which XBRL can't see)

  python3 -m desk.cause_reversal_screen [--max 40] [--enqueue 5]     # weekly cron
"""
from __future__ import annotations

import argparse
import datetime
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "desk" / "data" / "cause_reversal.json"


def growth_series(ticker: str) -> list[tuple[str, float]]:
    """YoY revenue growth per quarter from the evidence pack's audited series."""
    from desk.court_evidence import build_pack
    pack = build_pack(ticker)
    rev = (pack.get("xbrl_quarterly") or {}).get("rev") or []
    if len(rev) < 6:
        return []
    by_end = {r["end"]: r["val"] for r in rev}
    out = []
    for r in rev:
        end = datetime.date.fromisoformat(r["end"])
        prior = None
        for k, v in by_end.items():
            kd = datetime.date.fromisoformat(k)
            if abs((end - kd).days - 365) <= 20:
                prior = v
        if prior:
            out.append((r["end"], round(r["val"] / prior - 1, 4)))
    return sorted(out)


def signature(g: list[tuple[str, float]]) -> dict | None:
    """Trough-then-reacceleration: latest growth > trough + 3pp AND latest >= the rate
    two quarters before the trough (the cause reversed, not just bounced)."""
    if len(g) < 4:
        return None
    rates = [x[1] for x in g]
    trough_i = min(range(1, len(rates)), key=lambda i: rates[i])
    if trough_i >= len(rates) - 1:
        return None                                   # trough is the latest print — not reversed
    latest = rates[-1]
    trough = rates[trough_i]
    pre = rates[max(0, trough_i - 2)]
    if not (-0.30 <= trough <= 0.20 and latest <= 0.50):
        return None                                   # base-effect / collapse guard
    if latest >= trough + 0.03 and latest >= pre - 0.01:
        return {"trough_q": g[trough_i][0], "trough_yoy": trough,
                "latest_q": g[-1][0], "latest_yoy": latest, "pre_break_yoy": pre}
    return None


def run(max_names: int, enqueue_k: int) -> list[dict]:
    try:
        blob = json.loads((ROOT / "desk/data/discovery_blob.json").read_text())
    except Exception:
        print("[cause_reversal] no discovery blob — run class_dislocation first")
        return []
    # BSY lives in the MIDDLE of the drawdown distribution: -30..-70%, real-business
    # growth rates. The -80%+ tail is base-effect artifacts (SMR +733% off ~zero) and
    # integrity kills (DVLT) — first-run lesson 2026-08-08.
    from desk.court_queue import QUEUE
    dead = {r["ticker"] for r in QUEUE.rows() if r["stage"] in ("KILLED",)}
    cands = [r for r in blob.get("members", [])
             if (r.get("mcap") or 0) >= 250e6 and -0.70 <= r.get("dd52", 0) <= -0.30
             and r["ticker"] not in dead]
    cands.sort(key=lambda r: r["dd52"])
    hits = []
    for r in cands[:max_names]:
        t = r["ticker"]
        time.sleep(0.5)                               # SEC pacing
        try:
            sig = signature(growth_series(t))
        except Exception:
            continue
        if sig:
            hits.append({**r, **sig})
            print(f"  HIT {t}: trough {sig['trough_yoy']:+.1%} ({sig['trough_q']}) -> "
                  f"latest {sig['latest_yoy']:+.1%}, px {r['dd52']:+.0%} off high")
    OUT.write_text(json.dumps({"asof": datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z",
                               "scanned": min(len(cands), max_names), "hits": hits}, indent=1))
    print(f"[cause_reversal] {len(hits)} signature hits of {min(len(cands), max_names)} scanned")
    if enqueue_k and hits:
        from desk.court_queue import enqueue_candidates
        n = enqueue_candidates(
            [{"ticker": h["ticker"], "context":
              f"BSY-PATTERN candidate (cause_reversal_screen): revenue growth troughed {h['trough_yoy']:+.1%} "
              f"({h['trough_q']}), latest {h['latest_yoy']:+.1%} >= pre-break {h['pre_break_yoy']:+.1%}, "
              f"price {h['dd52']:+.0%} off high. COURT TASK: identify the TRUE named break metric (ARR/bookings/"
              f"NRR/guide — XBRL revenue is the crude proxy), date the break day, verify THAT metric reversed, "
              f"and check the price never marked it. The BSY test: break-cause reversed to a series high."}
             for h in hits[:enqueue_k]],
            source=f"cause_reversal/{datetime.date.today().isoformat()}", stage="TRAP_VERIFY", allow_ledger=True)
        print(f"[cause_reversal] enqueued: {n}")
    return hits


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--max", type=int, default=40)
    ap.add_argument("--enqueue", type=int, default=0)
    a = ap.parse_args()
    run(a.max, a.enqueue)
