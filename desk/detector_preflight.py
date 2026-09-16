"""detector_preflight — R1.12: run the appropriate detectors BEFORE the benches sit,
selected by a cheap reasoning pass (principal directive 2026-08-08: "why not run the
appropriate detectors after a quick cheap reasoning pass?").

R1.11 injects the dispatch-matched atlas as a consult-list; the benches could only
file UNCHECKABLE for anything needing live data. This module closes that loop for the
uniformly-invocable subset (BaseConnector modules — one request schema, one query()):

  1. PLAN    one volume-tier headless pass reads the case + the runnable atlas subset
             and emits a runlist: which connectors, on WHICH RESOLVED ENTITIES, with
             which ConnectorRequest fields. Entity resolution is the whole point —
             the query subject is rarely the ticker (permits need the GC, customs
             needs the shipper alias, rents need the metro). kwarg KEYS are validated
             against the ConnectorRequest schema; unknown keys are dropped loudly.
  2. EXECUTE each planned call runs time-boxed and fault-isolated through the
             standard load_connector().query() path; results compact-rendered.
  3. INJECT  court_runner appends "## DETECTOR RESULTS (pre-flight executed)" to both
             bench prompts; cached per (ticker, day) so red and blue share one run.

Compiled non-connector detectors stay consult-only under R1.11; the benches'
UNCHECKABLE dispositions are the demand signal for onboarding them here.

  python3 -m desk.detector_preflight TICKER   # manual: plan + execute + print
"""
from __future__ import annotations

import concurrent.futures
import datetime
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "desk" / "data" / "preflight_cache.json"
MAX_CALLS = 6
CALL_TIMEOUT_S = 75
# aggregates that chain many sub-connectors get a bigger box; satellite fetches scenes
TIMEOUT_OVERRIDES = {"discovery_state": 300, "sentinel2_buildout": 240, "plant_thermal": 240}

REQUEST_FIELDS = {"address", "parcel_id", "entity_name", "person_name",
                  "geographic_area", "state", "city", "year", "extra"}


def _runnable_atlas(ticker: str, context: str) -> list[dict]:
    """Dispatch-matched entries whose module is a BaseConnector (uniform contract)."""
    from desk.court_dispatch import atlas_for, _index
    by_name = {e.get("name"): e for e in _index()}
    out = []
    for h in atlas_for(ticker, context):
        e = by_name.get(h["name"], {})
        mod = e.get("module") or ""
        if ".connectors." in mod:
            out.append({**h, "module": mod})
    return out


def plan(ticker: str, context: str) -> list[dict]:
    """Cheap reasoning pass -> validated runlist. [] on any failure (never blocks)."""
    runnable = _runnable_atlas(ticker, context)
    if not runnable:
        return []
    menu = "\n".join(f"- {r['module']} : {r['summary']} (matched: {r['why']})" for r in runnable)
    try:
        from desk.facilities_resolver import render_facilities
        facilities = render_facilities(ticker)
    except Exception:
        facilities = ""
    try:
        from desk.official_series import render_series
        market_layer = render_series(f"{ticker}\n{context[:4000]}")
    except Exception:
        market_layer = ""
    prompt = f"""You are the desk's detector-dispatch planner. Case: {ticker}.

CASE CONTEXT (truncated):
{context[:4000]}

{facilities or "(no facilities resolved — satellite/thermal connectors need extra.lat/lon or an address; SKIP them and say so)"}

MARKET LAYER (official series)
{market_layer or "(no registered official series match this issuer)"}

RUNNABLE CONNECTORS (uniform interface; each takes ONE request object):
{menu}

Request schema (use ONLY these keys, omit what a connector doesn't need):
entity_name, person_name, address, parcel_id, geographic_area (zip/county/MSA),
state (2-letter), city, year, extra (dict).
Satellite/thermal connectors: plant_thermal takes extra.lat + extra.lon (floats);
sentinel2_buildout takes address OR extra.lat/lon — use the RESOLVED FACILITIES
coordinates above, and pick the SITE the thesis is about (the plant under
construction / the collateral), never the HQ by default.

Emit a runlist of AT MOST {MAX_CALLS} calls that would produce decision-relevant
evidence for an adversarial court on this case. CRITICAL — resolve entities first:
the query subject is rarely the ticker (customs wants the operating company or
shipper alias; permits want the GC or address; labor data wants the plant city;
rent benchmarks want the actual metro). If you cannot resolve the right subject
from the context, SKIP that connector rather than querying the wrong entity.
Skip any connector whose answer could not change a verdict.

Skipping ALL connectors is a valid answer (emit an empty list) — never manufacture
irrelevant corroboration.

Output ONLY a fenced block, then one line "SKIP-RATIONALE: ..." naming the actual
verdict axis and why the skipped connectors cannot move it:
```runlist
[{{"module": "...", "why": "one line — what verdict-relevant fact this checks",
   "request": {{"entity_name": "...", "state": "..."}}}}]
```"""
    try:
        from desk.court_runner import _dispatch, MODEL_VOLUME
        res = _dispatch(prompt, MODEL_VOLUME)
        txt = res.get("text", "")
        m = re.search(r"```runlist\s*(\[.*?\])\s*```", txt, re.S)
        raw = json.loads(m.group(1)) if m else []
        rm = re.search(r"SKIP-RATIONALE:\s*(.+)", txt, re.S)
        plan.last_rationale = (rm.group(1).strip()[:900] if rm else "")
    except Exception:
        return []
    allowed = {r["module"] for r in runnable}
    valid = []
    for call in raw[:MAX_CALLS]:
        if call.get("module") not in allowed:
            continue
        req = call.get("request") or {}
        dropped = set(req) - REQUEST_FIELDS
        call["request"] = {k: v for k, v in req.items() if k in REQUEST_FIELDS}
        if dropped:
            call["why"] = call.get("why", "") + f" [planner keys dropped: {sorted(dropped)}]"
        valid.append(call)
    return valid


def _one_call(call: dict) -> dict:
    from verticals.buyside_dd.dispatcher import load_connector
    from verticals.buyside_dd.connectors.base import ConnectorRequest
    conn = load_connector(call["module"])
    if conn is None:
        return {**call, "status": "LOAD_FAILED"}
    res = conn.query(ConnectorRequest(**call["request"]))
    obs = [{"claim_key": getattr(o, "attribute", None) or getattr(o, "claim_key", None),
            "value": str(getattr(o, "value", ""))[:200],
            "confidence": getattr(o, "confidence", None),
            "extra": {k: str(v)[:120] for k, v in (getattr(o, "extra", None) or {}).items()}}
           for o in (getattr(res, "observations", None) or [])[:8]]
    return {**call, "status": getattr(res, "status", "ok"),
            "error": str(getattr(res, "error_detail", "") or "")[:160], "observations": obs}


def execute(runlist: list[dict]) -> list[dict]:
    """Each call time-boxed + fault-isolated; a hung connector costs its slot, not the court."""
    out = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
        futs = {ex.submit(_one_call, c): c for c in runlist}
        for f, c in futs.items():
            tmo = TIMEOUT_OVERRIDES.get(c["module"].rsplit(".", 1)[-1], CALL_TIMEOUT_S)
            try:
                out.append(f.result(timeout=tmo))
            except Exception as e:
                out.append({**c, "status": "FAILED", "error": f"{type(e).__name__}: {e}"[:160]})
    return out


def render_results(ticker: str, context: str) -> str:
    """Cached per (ticker, day): red and blue see the SAME executed facts."""
    key = f"{ticker}|{datetime.date.today().isoformat()}"
    try:
        cache = json.loads(CACHE.read_text())
    except Exception:
        cache = {}
    if key not in cache:
        plan.last_rationale = ""
        rl = plan(ticker, context)
        cache[key] = {"results": execute(rl), "rationale": getattr(plan, "last_rationale", "")}
        cache = {k: v for k, v in cache.items() if k.split("|")[1] >= (
            datetime.date.today() - datetime.timedelta(days=3)).isoformat()}
        try:
            CACHE.write_text(json.dumps(cache, indent=1))
        except Exception:
            pass
    entry = cache[key]
    rows = entry["results"] if isinstance(entry, dict) else entry
    rationale = entry.get("rationale", "") if isinstance(entry, dict) else ""
    if not rows:
        if rationale:
            return (f"## DETECTOR RESULTS (pre-flight)\nPlanner ran NO connectors — its coverage "
                    f"ruling (treat as record; contest it in DETECTORS CONSULTED if wrong):\n"
                    f"{rationale}\n")
        return ""
    lines = []
    for r in rows:
        obs = "; ".join(f"{o['claim_key']}={o['value']}" for o in r.get("observations", [])) \
              or f"(no observations; {r.get('error') or 'empty'})"
        lines.append(f"- {r['module'].rsplit('.',1)[-1]} [{r['status']}] req={json.dumps(r['request'])}\n"
                     f"  why: {r.get('why','')}\n  -> {obs[:500]}")
    return ("## DETECTOR RESULTS (pre-flight executed — these are FACTS in the record; "
            "contradicting one requires a cited primary source)\n" + "\n".join(lines) + "\n")


if __name__ == "__main__":
    import sys
    t = sys.argv[1]
    ctx = sys.argv[2] if len(sys.argv) > 2 else t
    rl = plan(t, ctx)
    print(json.dumps(rl, indent=1))
    print(render_results(t, ctx))
