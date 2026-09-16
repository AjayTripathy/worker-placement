"""triage — the social-thesis funnel (SPEC.md §3 decision matrix), Phase 1.

social attention (reddit_mentions) -> rank -> conditioning (discovery_state: regime + squeeze-fuel
veto) + IV richness (iv_richness) -> classify into the decision matrix -> log a ranked, conditioned
candidate list to outputs/social_thesis_log.jsonl. The diligence column (OVERSTATED/REAL) is filled
in Phase 2 by the signalos-quant-analyst; here it is PENDING, so actions are pre-diligence labels.

NEVER places an order. Output is a watchlist for diligence + paper-tracking.
"""
from __future__ import annotations

import concurrent.futures
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Overall wall-clock budget for the concurrent conditioning batch (seconds). Leaves margin under
# the 600s desk-cron cap for the downstream IV-richness step. Stragglers past this = TIMEOUT regime.
_DS_BUDGET = 240

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from verticals.buyside_dd.connectors import reddit_mentions
from verticals.buyside_dd.connectors.discovery_state import discovery_state
import iv_richness

def _safe_richness(tickers):
    """{} when the gateway is down — every caller already handles missing IVs per-ticker."""
    if not _gateway_up():
        print("[iv] gateway unreachable — IV enrichment SKIPPED (attention/conditioning legs only; SELL_VOL suppressed)", flush=True)
        return {}
    try:
        return iv_richness.richness_batch(tickers)
    except Exception as e:
        print(f"[iv] richness failed ({type(e).__name__}) — continuing without IV", flush=True)
        return {}


def _gateway_up(host="127.0.0.1", port=4001, timeout=3):
    """The IV step hangs the whole engine when the gateway is down (3x600s silent deaths,
    Jul 1-6). Probe first; degrade to attention+conditioning-only when it's unreachable."""
    import socket
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False

LOG = Path(__file__).resolve().parent / "outputs" / "social_thesis_log.jsonl"
QUEUE = Path(__file__).resolve().parent / "outputs" / "needs_diligence.json"
SI_SQUEEZE = 20.0     # short-interest % that, with attention, = squeeze fuel (veto)
# Control universe: stable large/mid caps that rarely WSB-spike — for the matched short-vol
# control (SPEC §6). Each sell-vol candidate is paired to the closest-IV name here.
CONTROL_UNIVERSE = ["KO", "PG", "JNJ", "PEP", "CL", "MMM", "CAT", "DUK", "SO", "WM",
                    "MCD", "COST", "HON", "LMT", "TXN", "ADP", "CB", "MDT", "GIS", "K"]


def _squeeze_fuel(ds: dict) -> tuple[bool, str]:
    """Derive the SPEC §3 squeeze-fuel veto from discovery_state components."""
    comp = ds.get("components", {}) or {}
    si = comp.get("short_interest", {}) or {}
    ftd = comp.get("ftd", {}) or comp.get("sec_ftd", {}) or {}
    reasons = []
    si_pct = si.get("short_interest_pct")
    dtc = si.get("days_to_cover")
    if isinstance(si_pct, (int, float)) and si_pct >= SI_SQUEEZE:
        reasons.append(f"SI {si_pct}%")
    if isinstance(dtc, (int, float)) and dtc >= 5:
        reasons.append(f"days-to-cover {dtc}")
    drivers = str(comp.get("_regime_drivers", "")).lower()
    if "ftd" in drivers or ftd.get("spike"):
        reasons.append("FTD spike")
    return (len(reasons) > 0, "; ".join(reasons))


def classify(ds: dict, ivr: dict) -> tuple[str, str]:
    """Decision matrix (pre-diligence). Returns (action, rationale)."""
    regime = ds.get("regime", "UNKNOWN")
    squeeze, sq_why = _squeeze_fuel(ds)
    verdict = ivr.get("verdict", "UNAVAILABLE")
    if squeeze:
        return "VETO_SQUEEZE_FUEL", f"do NOT sell premium / short — {sq_why}"
    if verdict == "RICH" and regime != "UNDISCOVERED":
        return "SELL_VOL_CANDIDATE", ("rich IV, crowded, not squeeze-fueled → run diligence; "
                                      "if move is OVERDONE, sell defined-risk premium")
    if regime == "UNDISCOVERED":
        return "DIRECTIONAL_CANDIDATE", "undiscovered → run diligence; if thesis REAL, directional"
    if verdict == "CHEAP":
        return "NO_VOL_SALE", "realized vol >= implied — vol is cheap, don't sell it"
    return "WATCH", f"regime={regime}, IV={verdict} — no clean action yet"


def run(top_n: int = 8, require_spike: bool = False) -> dict:
    social = reddit_mentions.scan()
    items = list(social["tickers"].items())
    if require_spike:
        items = [(t, a) for t, a in items if a.get("spike")]
    cands = [t for t, _ in items[:top_n]]
    print(f"[social] {social['n_tickers']} tickers; triaging top {len(cands)}: {cands}", flush=True)

    print("[iv] pulling IV richness via TWS ...", flush=True)
    ivr_all = _safe_richness(cands)

    asof = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    # Conditioning per name CONCURRENTLY with a hard per-name timeout. Fix 2026-07-11: the
    # serial loop timed out the 600s cron for 12 straight days — discovery_state stalls on the
    # cloud-IP-blocked GDELT/Google-Trends connectors (~20s each x N names). Running them in a
    # bounded thread pool collapses the wall-clock and a hung connector degrades that ONE name to
    # a TIMEOUT regime instead of killing the whole run. (The dead connectors are already handled
    # as UNAVAILABLE subscores inside discovery_state; this only caps the wait.)
    ds_by_ticker = {}
    ex = concurrent.futures.ThreadPoolExecutor(max_workers=min(8, len(cands) or 1))
    futs = {ex.submit(discovery_state, t): t for t in cands}
    try:
        for fut in concurrent.futures.as_completed(futs, timeout=_DS_BUDGET):
            t = futs[fut]
            try:
                ds_by_ticker[t] = fut.result()
            except Exception as e:
                ds_by_ticker[t] = {"regime": "ERROR", "components": {}, "_err": str(e)[:80]}
    except concurrent.futures.TimeoutError:
        pass  # overall budget hit — stragglers fall through to TIMEOUT below
    ex.shutdown(wait=False, cancel_futures=True)
    # any name not back within the budget -> TIMEOUT regime (don't let it kill the run)
    for t in cands:
        ds_by_ticker.setdefault(t, {"regime": "TIMEOUT", "components": {},
                                    "_err": f"discovery_state exceeded {_DS_BUDGET}s budget"})
    rows = []
    for t in cands:
        a = social["tickers"][t]
        ds = ds_by_ticker.get(t) or {"regime": "TIMEOUT", "components": {}}
        print(f"[conditioning] {t} -> {ds.get('regime')}", flush=True)
        ivr = ivr_all.get(t, {})
        action, why = classify(ds, ivr)
        squeeze, sq_why = _squeeze_fuel(ds)
        row = {
            "asof": asof, "ticker": t, "name": a.get("name"),
            "mentions": a.get("mentions"), "velocity": a.get("velocity"), "spike": a.get("spike"),
            "lean": a.get("sentiment"),
            "regime": ds.get("regime"), "attention_score": ds.get("attention_score"),
            "positioning_score": ds.get("positioning_score"), "cap_tier": ds.get("cap_tier"),
            "squeeze_fuel": squeeze, "squeeze_why": sq_why,
            "iv": ivr.get("iv"), "hv": ivr.get("hv"), "iv_hv": ivr.get("iv_hv"),
            "iv_pctile": ivr.get("iv_pctile"), "iv_verdict": ivr.get("verdict"),
            "action": action, "rationale": why, "diligence": "PENDING",
        }
        rows.append(row)

    # --- matched short-vol control: pair each SELL_VOL candidate to the closest-IV control name ---
    sell_cands = [r for r in rows if r["action"] == "SELL_VOL_CANDIDATE"]
    control_rows = []
    if sell_cands:
        print(f"[control] {len(sell_cands)} sell-vol candidate(s) -> pulling control IVs ...", flush=True)
        ctrl_iv = _safe_richness([c for c in CONTROL_UNIVERSE])
        used = set()
        for cand in sell_cands:
            civ = cand.get("iv") or 0
            best, bestd = None, 1e9
            for ct, info in ctrl_iv.items():
                if ct in used or info.get("iv") is None:
                    continue
                d = abs(info["iv"] - civ)
                if d < bestd:
                    bestd, best = d, ct
            if best:
                used.add(best)
                info = ctrl_iv[best]
                control_rows.append({
                    "asof": asof, "ticker": best, "name": f"control for {cand['ticker']}",
                    "action": "CONTROL", "matched_to": cand["ticker"],
                    "iv": info.get("iv"), "hv": info.get("hv"), "iv_hv": info.get("iv_hv"),
                    "iv_pctile": info.get("iv_pctile"), "iv_verdict": info.get("verdict"),
                    "regime": "CONTROL", "diligence": "N/A",
                    "rationale": f"matched short-vol control (closest IV to {cand['ticker']})"})

    # --- diligence queue: candidates that need a signalos-quant-analyst pass (Phase 2) ---
    queue = [{"ticker": r["ticker"], "name": r["name"], "action": r["action"],
              "regime": r["regime"], "iv": r["iv"], "iv_hv": r["iv_hv"],
              "iv_verdict": r["iv_verdict"], "mentions": r["mentions"], "asof": asof,
              "ask": ("Is this social-driven move OVERDONE/overstated (sell vol) — run two-mode "
                      "diligence + honesty pass; return verdict OVERSTATED | REAL | INCONCLUSIVE.")}
             for r in rows if r["action"] in ("SELL_VOL_CANDIDATE", "DIRECTIONAL_CANDIDATE")]
    QUEUE.write_text(json.dumps(queue, indent=2, default=str))

    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a") as f:
        for r in rows + control_rows:
            f.write(json.dumps(r, default=str) + "\n")

    # print summary table
    print(f"\n=== SOCIAL-THESIS TRIAGE {asof} (pre-diligence) ===")
    print(f"{'TICK':6}{'MENT':>5}{'VEL':>5} {'REGIME':16}{'IV/HV':>6}{'IVv':>9} {'ACTION':22} WHY")
    for r in sorted(rows, key=lambda x: {"SELL_VOL_CANDIDATE": 0, "DIRECTIONAL_CANDIDATE": 1,
                                         "VETO_SQUEEZE_FUEL": 2}.get(x["action"], 3)):
        print(f"{r['ticker']:6}{str(r['mentions']):>5}{str(r['velocity']):>5} "
              f"{str(r['regime'] or '-'):16}{str(r['iv_hv'] or '-'):>6}{str(r['iv_verdict'] or '-'):>9} "
              f"{r['action']:22} {r['rationale'][:46]}")
    print(f"\n[logged {len(rows)} candidate + {len(control_rows)} control rows -> {LOG}]")
    print(f"[diligence queue: {len(queue)} name(s) -> {QUEUE}]")
    return {"asof": asof, "rows": rows, "queue": queue, "controls": control_rows}


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    run(top_n=n)
