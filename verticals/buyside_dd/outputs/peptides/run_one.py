"""Single-ticker discovery_state with a hard wall-clock timeout via signal.alarm.
Usage: python run_one.py TICKER "Company Name" shares_out_or_blank divergence_type
Prints one JSON line; appends to latency_log.
"""
import json, sys, signal
sys.path.insert(0, "/Users/ajay/exalted/signalos")
from verticals.buyside_dd.connectors.discovery_state import discovery_state
from verticals.buyside_dd.connectors.latency_log import log_divergence

class TO(Exception): pass
def _h(sig, frm): raise TO()
signal.signal(signal.SIGALRM, _h)

tk = sys.argv[1]; name = sys.argv[2]
so = int(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[3] else None
dtype = sys.argv[4] if len(sys.argv) > 4 else "glp1_secondary_effect"
ASOF = "2026-06-25"

signal.alarm(90)
try:
    ds = discovery_state(tk, asof=ASOF, company_name=name, shares_outstanding=so,
                         enable_options=False, enable_13f=False)
    signal.alarm(0)
    comp = ds.get("components", {})
    def st(k):
        v = comp.get(k, {})
        return v.get("status", "OK") if isinstance(v, dict) and v.get("status") else (
            v.get("subscore") if isinstance(v, dict) else None)
    rec = {"ticker": tk, "regime": ds.get("regime"),
           "attention": ds.get("attention_score"), "positioning": ds.get("positioning_score"),
           "confidence": ds.get("confidence"),
           "si": (comp.get("short_interest", {}) or {}).get("subscore"),
           "ftd": (comp.get("ftd", {}) or {}).get("subscore"),
           "stwits": (comp.get("stocktwits", {}) or {}).get("subscore"),
           "wiki": (comp.get("wikipedia", {}) or {}).get("subscore")}
    log_divergence(tk, divergence_type=dtype, source_connector="glp1_secondary_effects_screen",
                   discovery=ds, detection_date=ASOF, extra={"name": name})
    print(json.dumps(rec))
except TO:
    print(json.dumps({"ticker": tk, "regime": "TIMEOUT_90s", "note": "I/O blocked"}))
except Exception as e:
    print(json.dumps({"ticker": tk, "regime": "ERROR", "err": f"{type(e).__name__}: {e}"}))
