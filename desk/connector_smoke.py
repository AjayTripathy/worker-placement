"""connector_smoke — assert every KG-dispatched connector is actually CALLABLE.

WHY THIS EXISTS (2026-08-17/18). Two connectors built in one day — app_review_velocity and
expedition_inventory — both ran perfectly from their `__main__` CLI, were declared tested, were
registered in the knowledge graph, and BOTH CRASHED THE MOMENT ANYTHING DISPATCHED THEM:

    TypeError: _ok() got an unexpected keyword argument 'raw_response_snippet'

The base signature is `_ok(request, observations, raw=None)`. The CLI path never touches `_ok`,
so testing the command line proved nothing about the interface the graph actually uses. A
connector in this state is WORSE than a missing one: the KG advertises it as available, a bench
dispatches it, the call dies, and the bench records a COVERAGE GAP — an infrastructure failure
wearing the costume of an analytic absence. The LIND blue bench caught exactly this and wrote
"expedition_inventory — FIRED (degraded) ... both re-runs crashed. Repair required."

WHAT IT CHECKS — TWO ASSERTIONS.
  1. DOES NOT RAISE. For every module carrying APPLIES_TO, find its BaseConnector subclass and
     call `query()`. A connector that returns success=False for want of inputs PASSES — that is
     the interface working. Only an exception fails: TypeError, AttributeError, bad signature,
     missing import.
  2. DOES NOT SILENTLY DEFAULT TO AN ISSUER. Called with NO inputs, a connector must NOT return
     success=True. Added after assertion 1 alone PASSED a genuinely dangerous bug: expedition_
     inventory carried `or "LIND"`, so an empty request returned Lindblad's real book with
     success=True, and the NCLH bench consumed it as NCL data ("byte-identical output for ncl.com
     and rssc.com"). Real-looking numbers for the wrong company are strictly worse than a crash,
     and assertion 1 rewards them — a well-formed result was returned.

NEITHER ASSERTION PROVES USABILITY. resort_snowpack passed assertion 1 while resolving only on
ticker, so every bench dispatching a RESORT NAME got UNSUPPORTED: 5 dispatches, 0 observations,
logged by the bench as "infra failure wearing the costume of an analytic absence". It declined
politely and was useless. Contract tests bound the failure modes; they do not certify fitness.

NETWORK IS OPT-IN. By default every request carries no usable inputs, so well-formed connectors
short-circuit to a `_fail(UNSUPPORTED)` without a network call, which is exactly the contract
under test. `--live` passes real inputs to the named connectors instead.

    python3 -m desk.connector_smoke            # contract only, no network, seconds
    python3 -m desk.connector_smoke --live app_review_velocity expedition_inventory
"""
from __future__ import annotations

import argparse
import importlib
import inspect
import json
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

KG = ROOT / "knowledge_graph" / "knowledge_graph.json"
OUT = ROOT / "desk" / "data" / "connector_smoke.json"

# Minimal inputs for --live runs, keyed by module name.
LIVE_INPUTS = {
    "app_review_velocity": {"ticker": "IBKR"},
    "expedition_inventory": {"ticker": "LIND"},
    "consumer_product_heat": {"ticker": "SUJA"},
    "consumer_product_reviews": {"ticker": "SUJA"},
}


def _connector_classes(mod):
    from verticals.buyside_dd.connectors.base import BaseConnector
    out = []
    for _, obj in inspect.getmembers(mod, inspect.isclass):
        if issubclass(obj, BaseConnector) and obj is not BaseConnector \
                and obj.__module__ == mod.__name__:
            out.append(obj)
    return out


def run(live: list[str] | None = None, verbose: bool = True) -> dict:
    from verticals.buyside_dd.connectors.base import ConnectorRequest
    live = live or []
    try:
        kg = json.loads(KG.read_text())
    except (OSError, ValueError) as e:
        return {"error": f"knowledge graph unreadable: {e}"}

    mods = sorted({d["module"] for d in kg.get("dispatch_index", [])
                   if d.get("module") and ".connectors." in d["module"]})
    passed, failed, skipped = [], [], []
    for m in mods:
        short = m.rsplit(".", 1)[-1]
        try:
            mod = importlib.import_module(m)
        except Exception as e:
            failed.append({"module": short, "stage": "import",
                           "error": f"{type(e).__name__}: {e}"})
            continue
        classes = _connector_classes(mod)
        if not classes:
            skipped.append({"module": short, "why": "no BaseConnector subclass (m_source module)"})
            continue
        for cls in classes:
            extra = LIVE_INPUTS.get(short, {}) if short in live else {}
            try:
                res = cls().query(ConnectorRequest(extra=extra))
                ok = bool(getattr(res, "success", None))
                # ASSERTION 2 — SILENT DEFAULT (added 2026-08-18, and this test PASSED the bug it
                # now catches). A connector called with NO issuer must not answer. expedition_
                # inventory carried `or "LIND"`, so an empty request returned Lindblad's real book
                # with success=True; the NCLH bench received it as NCL data and reported
                # "byte-identical output for ncl.com and rssc.com". Returning another issuer's
                # numbers is strictly worse than crashing, and assertion 1 (does not raise) rewards
                # it. In contract mode — no inputs supplied — success MUST be False.
                if not extra and ok:
                    failed.append({"module": short, "class": cls.__name__, "stage": "silent_default",
                                   "error": ("returned success=True to an EMPTY request — the "
                                             "connector is guessing an issuer. Whose data is this?"),
                                   "observations": len(getattr(res, "observations", []) or [])})
                    continue
                passed.append({"module": short, "class": cls.__name__, "success": ok,
                               "observations": len(getattr(res, "observations", []) or []),
                               "mode": "live" if extra else "contract"})
            except Exception as e:
                failed.append({"module": short, "class": cls.__name__, "stage": "query",
                               "error": f"{type(e).__name__}: {e}",
                               "trace": traceback.format_exc(limit=3).splitlines()[-3:]})

    res = {"connectors_indexed": len(mods), "passed": len(passed), "failed": len(failed),
           "skipped_no_class": len(skipped), "failures": failed, "results": passed,
           "note": ("success=False is a PASS — this asserts the CONTRACT (callable, right "
                    "signature), not the data. Only an exception fails.")}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(res, indent=1))
    if verbose:
        print(f"[connector_smoke] {len(mods)} dispatch-indexed connector modules | "
              f"PASS {len(passed)} | FAIL {len(failed)} | no-class {len(skipped)}")
        for f in failed:
            print(f"  FAIL {f['module']}.{f.get('class','-')} [{f['stage']}] {f['error']}")
        if not failed:
            print("  all dispatch-callable")
    return res


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", nargs="*", default=[],
                    help="module names to call with real inputs (network)")
    a = ap.parse_args()
    r = run(live=a.live)
    sys.exit(1 if r.get("failed") else 0)
