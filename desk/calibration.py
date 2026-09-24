"""calibration — THE CALIBRATION EXPERIMENT. The system's directional record is unproven (anti-book: 36%
hit-rate, high-conviction 29% — conviction INVERTED), yet the catalyst-mispricing scanner sizes edges off our
probabilities. Before trusting any edge_pp for sizing, this module freezes every dated probability call at
prediction time (pre-registration), scores it when the catalyst resolves, and builds the calibration curve:

  - Brier(ours) vs Brier(market-implied) vs Brier(coin 0.5)  — the decisive test: do our p's add information
    over the market's? If Brier(ours) >= Brier(market), edge_pp is noise and must not size positions.
  - calibration buckets (predicted p vs realized frequency) + the conviction-inversion check.

LEDGER: desk/data/calibration_ledger.jsonl — append-only; a record is NEVER edited after freeze except to add
its resolution. Ingests from catalyst_predictions.json (directional p_favorable calls) + CATALYST_MISPRICING.json
(scenario names: favorable = base-or-better, so our_p = p_base + p_bull and market_p = implied p_base + p_bull).

RESOLUTION is an adjudication, not a price print — a catalyst can resolve favorably into a down-tape. When a
cat_date passes, the run FLAGS it; resolve with:

  python3 -m desk.calibration resolve TICKER OUTCOME [--date CAT_DATE] [--note "..."]
      OUTCOME: FAVORABLE | UNFAVORABLE | MIXED  (MIXED scores 0.5)

  python3 -m desk.calibration            # ingest new predictions + score + report

READ-ONLY on the market; never places orders. Registered as a weekday watch.
"""
from __future__ import annotations
import json, sys, argparse, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "desk" / "data" / "calibration_ledger.jsonl"
PRED = ROOT / "desk" / "data" / "catalyst_predictions.json"
CATMIS = ROOT / "desk" / "data" / "CATALYST_MISPRICING.json"
OUT = ROOT / "desk" / "data" / "CALIBRATION.json"
YF = {"COSMECCA": "241710.KQ", "SILICON2": "257720.KQ", "COSMAX": "192820.KS", "HUGEL": "145020.KQ",
      "028260.KS": "028260.KS", "AMV0.DE": "AMV0.DE", "HSBK.L": "HSBK.L", "PKO.WA": "PKO.WA",
      "TBCG.L": "TBCG.L", "BRBY.L": "BRBY.L", "KER.PA": "KER.PA", "PRY.MI": "PRY.MI"}
NO_PX = {"UKRAIN-StepUp-B"}          # bond / no equity line — skip price stamping


def _load() -> list[dict]:
    if not LEDGER.exists():
        return []
    return [json.loads(l) for l in LEDGER.read_text().splitlines() if l.strip()]


def _write(rows: list[dict]):
    LEDGER.write_text("\n".join(json.dumps(r) for r in rows) + ("\n" if rows else ""))


def _px_many(tickers) -> dict:
    syms = {t: YF.get(t, t) for t in tickers if t not in NO_PX}
    out = {}
    try:
        import yfinance as yf
        df = yf.download(sorted(set(syms.values())), period="3d", progress=False, auto_adjust=True)["Close"]
        for t, s in syms.items():
            try:
                col = df[s] if hasattr(df, "columns") and s in getattr(df, "columns", []) else df
                v = col.dropna()
                if len(v):
                    out[t] = round(float(v.iloc[-1]), 2)
            except Exception:
                pass
    except Exception:
        pass
    return out


def ingest() -> int:
    """Freeze any dated prediction not yet in the ledger. Keyed (ticker, cat_date); NEVER overwrites."""
    rows = _load()
    have = {(r["ticker"], r["cat_date"]) for r in rows}
    today = datetime.date.today().isoformat()
    new = []
    # (a) directional calls
    try:
        preds = json.loads(PRED.read_text()).get("predictions", {})
    except Exception:
        preds = {}
    for t, p in preds.items():
        cd, pf = p.get("date"), p.get("p_favorable")
        if not cd or pf is None or (t, cd) in have:
            continue
        new.append({"ticker": t, "cat_date": cd, "kind": "directional", "made": today,
                    "event_type": p.get("event_type"), "our_p": float(pf), "market_p": None, "direction": (p.get("direction") or "").upper(),
                    "catalyst": (p.get("prediction") or p.get("catalyst") or "")[:180],
                    "px_at_pred": None, "fv": None, "status": "OPEN", "resolution": None})
    # (b) scenario names from the mispricing scanner (favorable = base-or-better)
    try:
        scored = json.loads(CATMIS.read_text()).get("scored", [])
    except Exception:
        scored = []
    for r in scored:
        t, cd = r["ticker"], r.get("cat_date")
        if not cd or (t, cd) in have or r.get("p_base") is None or r.get("p_bull") is None:
            continue
        mp = r.get("mkt_p_base")
        mp_fav = (max(0.0, min(1.0, mp + r["p_bull"])) if mp is not None else None)
        new.append({"ticker": t, "cat_date": cd, "kind": "scenario", "made": today,
                    "our_p": round(min(1.0, r["p_base"] + r["p_bull"]), 3), "market_p": (round(mp_fav, 3) if mp_fav is not None else None),
                    "direction": "FAVORABLE=BASE_OR_BETTER", "catalyst": (r.get("catalyst") or "")[:180],
                    "px_at_pred": r.get("px"), "fv": {"bear": r.get("bear"), "base": r.get("base"), "bull": r.get("bull")},
                    "status": "OPEN", "resolution": None})
    if new:
        from desk.research_contracts import validate_new
        accepted = list(rows)
        for candidate in new:
            validate_new(candidate, accepted)
            accepted.append(candidate)
        px = _px_many([r["ticker"] for r in new if r["px_at_pred"] is None])
        for r in new:
            if r["px_at_pred"] is None:
                r["px_at_pred"] = px.get(r["ticker"])
        rows.extend(new)
        _write(rows)
    return len(new)


def resolve(ticker: str, outcome: str, date: str | None, note: str):
    outcome = outcome.upper()
    assert outcome in ("FAVORABLE", "UNFAVORABLE", "MIXED"), "outcome must be FAVORABLE|UNFAVORABLE|MIXED"
    rows = _load()
    open_matches = [r for r in rows if r["ticker"] == ticker and r["status"] == "OPEN"
                    and (date is None or r["cat_date"] == date)]
    if not open_matches:
        print(f"no OPEN ledger entry for {ticker}" + (f" @ {date}" if date else ""))
        return
    if len(open_matches) > 1:
        # ambiguous even WITH a date = two events sharing a resolve key (the IVN/IVN-MRE
        # collision class, 2026-07-27) — refuse rather than silently grade the first
        print(f"{ticker} has {len(open_matches)} OPEN entries" + (f" @ {date}" if date else "") +
              " — disambiguate (split the ticker per the HCA-OPS convention): " +
              ", ".join(f"{r['cat_date']}/{r.get('event_type')}" for r in open_matches))
        return
    r = open_matches[0]
    px = _px_many([ticker]).get(ticker)
    r["status"] = "RESOLVED"
    r["resolution"] = {"date": datetime.date.today().isoformat(), "outcome": outcome,
                       "y": {"FAVORABLE": 1.0, "UNFAVORABLE": 0.0, "MIXED": 0.5}[outcome],
                       "px_at_resolve": px, "note": note}
    y = r["resolution"]["y"]
    # PERSIST the Brier score. It was previously computed only inside the print() below, so the
    # scoreboard had to recompute it and any consumer counting rows with a top-level `brier` field
    # under-reported the book 4x ("14 resolved" against 62 actually gradeable).
    if isinstance(r.get("our_p"), (int, float)):
        r["brier"] = round((r["our_p"] - y) ** 2, 4)
    _write(rows)
    print(f"resolved {ticker} @ {r['cat_date']}: {outcome}  (our_p {r['our_p']:.2f} -> brier {(r['our_p']-y)**2:.3f})")
    try:                       # a resolve changes the scoreboard — refresh the Strategy page now, no stale gap
        from desk.strategy_book import main as _sb
        _sb()
    except Exception:
        pass
    try:                       # CLOSE THE ACTION LOOP: fire any pre-registered action the instant it grades
        from desk.catalyst_action import arm
        fired = arm()
        for a in fired:
            print(f"  ⚡ ARMED {a['ticker']} {a['do']} (SLA {a['sla_min']}m): {a['plan'][:120]}")
    except Exception as e:
        print(f"  [catalyst_action] arm skipped: {type(e).__name__}")


def _y(r: dict) -> float | None:
    """Resolution outcome as y in {1, 0.5, 0} — tolerant of BOTH record shapes: the resolve()
    dict ({outcome, y, ...}) and the plain-string outcomes written by interactive grading
    sessions ("FAVORABLE"). The string shape silently crashed score() from ~2026-07-22 on,
    which is why CALIBRATION.json sat stale at 07-15 (found + fixed 2026-07-27)."""
    res = r.get("resolution")
    if isinstance(res, dict):
        y = res.get("y")
        if isinstance(y, (int, float)):
            return float(y)
        res = res.get("outcome")
    if isinstance(res, str):
        u = res.upper()
        if u.startswith("FAV"):
            return 1.0
        if u.startswith("UNFAV"):
            return 0.0
        if u.startswith("MIX"):
            return 0.5
    return None


def partition_of(r: dict) -> str:
    """Skill-class partition (2026-07-27, from the Brier-book decomposition): controls are
    absolute-calibration only; reaction legs are the price-guessing class we measured weak;
    ops/data is the connector-fed class we measured strong; narrative is the story class
    (the FR.PA overconfidence pocket). Normalizes over the known event-enum drift
    (stock_reaction vs earnings_stock_reaction etc.) WITHOUT touching the closed enum —
    canonicalization stays the user's call."""
    if r.get("kind") == "control":
        return "control"
    t = str(r.get("ticker") or "")
    et = str(r.get("event_type") or "")
    if et in ("stock_reaction", "earnings_stock_reaction") or t.endswith(("-STK", "-RXN")):
        return "reaction"
    if et in ("peer_read", "political_process"):
        return "narrative"
    if et in ("earnings_print", "earnings_operating", "operating", "earnings_operating_print",
              "monthly_data", "production_ops") or t.endswith("-OPS"):
        return "ops_data"
    return "other"


def is_genuine_anchor(r: dict) -> bool:
    """GATE-ELIGIBLE market_p = a real external crowd price, never a derived gauge.
    Genuine: an explicit market_p_source (venue quote or options-implied stamp), or a
    hand-annotated directional call (the GOOGL/DGX/TSLA class). NOT genuine: scenario-kind
    market_p inverted from OUR OWN FVs by catalyst_mispricing — that is a consistency gauge
    (feedback_mispricing_artifact_taxonomy, 2026-07-14) and it must not grade the market."""
    if r.get("market_p") is None:
        return False
    if r.get("kind") == "control":
        return False               # controls calibrate us absolutely; they are not the edge gate
    if r.get("market_p_source"):
        return True
    return r.get("kind") == "directional"


def score() -> dict:
    from desk.research_contracts import project_calibration
    rows, audit = project_calibration(_load())
    res = [r for r in rows if r["status"] == "RESOLVED"]
    out = {"n_open": sum(1 for r in rows if r["status"] == "OPEN"), "n_resolved": len(res)}
    out["contract_audit"] = audit
    out['by_submitter'] = score_by_actor(rows, 'submitter')
    out['by_agent'] = score_by_actor(rows, 'agent')
    out['by_submitter_agent'] = score_by_actor(rows, 'submitter_agent')
    # ---- THE PARTITION (skill classes) + THE GATE (genuine anchors only) ----
    parts = {}
    for r in res:
        parts.setdefault(partition_of(r), []).append(r)
    out["partitions"] = {}
    for name, rs in sorted(parts.items()):
        ys = [(r["our_p"], _y(r)) for r in rs if _y(r) is not None]
        if not ys:
            continue
        bri = round(sum((p - y) ** 2 for p, y in ys) / len(ys), 3)
        dec = [(p, y) for p, y in ys if y != 0.5]
        hit = (round(sum(1 for p, y in dec if (p >= 0.5) == (y >= 0.5)) / len(dec), 2) if dec else None)
        out["partitions"][name] = {"n": len(ys), "brier": bri, "hit_rate": hit,
                                   "n_open": sum(1 for r in rows if r["status"] == "OPEN" and partition_of(r) == name)}
    gate = [r for r in res if is_genuine_anchor(r) and _y(r) is not None]
    g = {"n": len(gate), "n_required": 20,
         # resolved records carrying a market_p with NO recorded provenance (pre-2026-07-27
         # hand-annotations): excluded from the gate until someone backfills where each number
         # came from — the artifact-taxonomy lesson is that unprovenanced anchors were the bug
         "legacy_unprovenanced": sum(1 for r in res if r.get("market_p") is not None
                                     and not r.get("market_p_source") and r.get("kind") != "control"
                                     and r.get("kind") != "directional")}
    if gate:
        g["brier_ours"] = round(sum((r["our_p"] - _y(r)) ** 2 for r in gate) / len(gate), 4)
        g["brier_market"] = round(sum((r["market_p"] - _y(r)) ** 2 for r in gate) / len(gate), 4)
        g["ours_beats_market"] = g["brier_ours"] < g["brier_market"]
    g["status"] = ("EARNED" if g.get("ours_beats_market") and len(gate) >= 20 else
                   ("ON TRACK" if g.get("ours_beats_market") else "NOT EARNED"))
    out["gate"] = g
    if any(_y(r) is not None for r in res):
        scored_res = [r for r in res if _y(r) is not None]
        briers_ours = [(r["our_p"] - _y(r)) ** 2 for r in scored_res]
        out["brier_ours"] = round(sum(briers_ours) / len(briers_ours), 4)
        out["brier_coin"] = round(sum((0.5 - _y(r)) ** 2 for r in scored_res) / len(scored_res), 4)
        mk = [r for r in scored_res if r.get("market_p") is not None]
        if mk:
            out["brier_market"] = round(sum((r["market_p"] - _y(r)) ** 2 for r in mk) / len(mk), 4)
            out["n_with_market"] = len(mk)
            out["ours_beats_market"] = out["brier_ours"] < out["brier_market"]
        # calibration buckets
        buckets = {}
        for r in scored_res:
            b = f"{int(r['our_p'] * 100) // 20 * 20}-{int(r['our_p'] * 100) // 20 * 20 + 20}%"
            buckets.setdefault(b, []).append(_y(r))
        out["buckets"] = {b: {"n": len(v), "predicted_mid": None, "realized": round(sum(v) / len(v), 2)}
                          for b, v in sorted(buckets.items())}
        # conviction-inversion check (the anti-book pathology)
        hi = [r for r in scored_res if r["our_p"] >= 0.6 or r["our_p"] <= 0.35]
        lo = [r for r in scored_res if 0.35 < r["our_p"] < 0.6]
        def _hit(rs):
            # a call "hits" if the outcome landed on the side our p leaned
            h = [1 if ((r["our_p"] >= 0.5) == (_y(r) >= 0.5)) else 0 for r in rs if _y(r) != 0.5]
            return round(100 * sum(h) / len(h)) if h else None
        out["hit_conviction"] = _hit(hi)
        out["hit_coinflippy"] = _hit(lo)
    return out


def score_by_event_type(records):
    """Per-event-type calibration — taxonomy frozen 2026-07-03 BEFORE any resolutions (no post-hoc
    re-bucketing). Answers 'are we calibrated on politics vs prints vs peer-reads', which the
    aggregate Brier hides. Types with n<5 resolved are reported but flagged small-sample."""
    from desk.research_contracts import project_calibration
    records, _ = project_calibration(records)
    by = {}
    for r in records:
        by.setdefault(r.get("event_type", "earnings_print"), []).append(r)
    out = {}
    for et, rs in sorted(by.items()):
        resolved = [r for r in rs if r.get("status") == "RESOLVED" and _y(r) is not None]
        row = {"n_open": sum(1 for r in rs if r.get("status") == "OPEN"), "n_resolved": len(resolved)}
        # resolution is a DICT {outcome, y, ...}; use resolution["y"] exactly like score()
        # (the old code tested the dict against ("HIT", True) → always False → every call mis-scored y=0).
        scored = [(r["our_p"], _y(r)) for r in resolved if _y(r) is not None]
        if scored:
            bri = [(p - y) ** 2 for p, y in scored]
            row["brier_ours"] = round(sum(bri) / len(bri), 3)
            decisive = [(p, y) for p, y in scored if y != 0.5]          # a "hit" = outcome on the side our_p leaned
            if decisive:
                hits = sum(1 for p, y in decisive if (p >= 0.5) == (y >= 0.5))
                row["hit_rate"] = round(hits / len(decisive), 2)
            mkt = [(r["market_p"], _y(r)) for r in resolved
                   if r.get("market_p") is not None and _y(r) is not None]
            if mkt:
                row["brier_market"] = round(sum((mp - y) ** 2 for mp, y in mkt) / len(mkt), 3)
            row["brier_coin"] = 0.25
            if len(scored) < 5:
                row["small_sample"] = True
        out[et] = row
    return out


def score_by_actor(records, dimension):
    """Binary outcomes only; missing legacy authorship stays unattributed."""
    groups = {}
    for row in records:
        provenance = row.get('attribution') or {}
        actor = provenance.get(dimension) if dimension != 'submitter_agent' else json.dumps(
            [provenance.get('submitter'), provenance.get('agent')])
        group = groups.setdefault(actor or 'unattributed', {'forecasts': 0, 'resolved': 0, 'pending': 0, 'excluded': 0, 'loss': 0.})
        group['forecasts'] += 1
        y = _y(row)
        if row.get('status') == 'RESOLVED' and y in (0., 1.):
            group['resolved'] += 1
            group['loss'] += (row['our_p'] - y) ** 2
        elif row.get('status') == 'OPEN':
            group['pending'] += 1
        else:
            group['excluded'] += 1
    for group in groups.values():
        loss = group.pop('loss')
        group['brier'] = round(loss / group['resolved'], 4) if group['resolved'] else None
    return groups


def main():
    n_new = ingest()
    rows = _load()
    today = datetime.date.today()
    s = score()
    by_type = score_by_event_type(rows)
    OUT.write_text(json.dumps({"asof": today.isoformat(), **s, "by_event_type": by_type}, indent=1))
    print(f"=== CALIBRATION EXPERIMENT  {today}  ({n_new} newly frozen, {s['n_open']} open, {s['n_resolved']} resolved) ===")
    print("  pre-registered probability calls, scored on resolution; the gate: edge_pp sizes positions ONLY once Brier(ours) < Brier(market).")
    if s.get("partitions"):
        print("  BY SKILL CLASS (partition 2026-07-27 — controls/reaction/ops split; the gate reads only genuine anchors):")
        for name, row in s["partitions"].items():
            hit = f" · hit {row['hit_rate']:.0%}" if row.get("hit_rate") is not None else ""
            print(f"    {name:<10} n={row['n']:<3} Brier {row['brier']}{hit} (open {row['n_open']})")
    if s.get("gate"):
        g = s["gate"]
        line = f"  THE GATE (genuine external anchors only, n>={g['n_required']}): n={g['n']}"
        if g.get("brier_ours") is not None:
            line += f" · ours {g['brier_ours']} vs market {g['brier_market']}"
        line += f" -> {g['status']}"
        if g.get("legacy_unprovenanced"):
            line += f"  ({g['legacy_unprovenanced']} legacy anchors excluded pending provenance backfill)"
        print(line)
    print("  BY EVENT TYPE (taxonomy frozen 2026-07-03, pre-resolution):")
    for et, row in by_type.items():
        bits = [f"open {row['n_open']}", f"resolved {row['n_resolved']}"]
        if row.get("hit_rate") is not None:
            bits.append(f"hit {row['hit_rate']:.0%}")
            bits.append(f"Brier ours {row['brier_ours']}" + (f" vs mkt {row['brier_market']}" if row.get("brier_market") is not None else "") + " vs coin 0.25")
            if row.get("small_sample"):
                bits.append("SMALL SAMPLE")
        print(f"    {et:<20} " + " · ".join(bits))
    due = [r for r in rows if r["status"] == "OPEN" and r["cat_date"] <= today.isoformat()]
    upcoming = sorted([r for r in rows if r["status"] == "OPEN" and r["cat_date"] > today.isoformat()],
                      key=lambda r: r["cat_date"])[:6]
    for r in due:
        print(f"  >>> FLAG RESOLVE-NEEDED: {r['ticker']} catalyst date {r['cat_date']} has passed — adjudicate: "
              f"python3 -m desk.calibration resolve {r['ticker']} FAVORABLE|UNFAVORABLE|MIXED")
    if upcoming:
        print("  next resolutions due: " + " | ".join(f"{r['ticker']} {r['cat_date']} (p={r['our_p']:.2f})" for r in upcoming))
    if s["n_resolved"]:
        line = f"  SCORE: Brier ours {s['brier_ours']} vs coin {s['brier_coin']}"
        if "brier_market" in s:
            line += f" vs market {s['brier_market']} ({'OURS ADDS INFO' if s['ours_beats_market'] else 'MARKET BETTER — edge_pp not yet trustworthy'})"
        print(line)
        print(f"  conviction hit {s['hit_conviction']}% vs coin-flippy {s['hit_coinflippy']}%  (inversion check)")
        for b, v in s.get("buckets", {}).items():
            print(f"    {b:<8} n={v['n']:<3} realized {v['realized']}")
    else:
        print("  no resolutions yet — the curve starts when the first catalyst lands (see 'next resolutions due').")
    print(f"[-> {LEDGER.name} / {OUT.name}]")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "resolve":
        ap = argparse.ArgumentParser()
        ap.add_argument("cmd")
        ap.add_argument("ticker")
        ap.add_argument("outcome")
        ap.add_argument("--date", default=None)
        ap.add_argument("--note", default="")
        a = ap.parse_args()
        resolve(a.ticker, a.outcome, a.date, a.note)
    else:
        main()
