"""detector_scan — runs an info-asymmetry detector over the BOOK SUBSET its APPLIES_TO contract matches,
and prints structured DETFIRE lines the Desk extractor turns into DETECTOR_FIRE signals (which the Desk
agent then auto-escalates to SignalOS for read-only verification).

  python3 -m desk.detector_scan litigation        # over all litigation:true names
  python3 -m desk.detector_scan usaspending        # over gov_revenue names (tracks award-flow drops)
  python3 -m desk.detector_scan all

DISPATCH DISCIPLINE: a detector never scans a name outside its feature subset. Heavy/auth-gated detectors
(customer_id customs, satellite) degrade gracefully to a NOTE when inputs/keys are absent — they're mapped
and scheduled, but only fire where they can actually execute.
"""
from __future__ import annotations
import sys, json, time
from pathlib import Path
from . import book_universe as BU

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
STATE = Path(__file__).resolve().parent / "data" / "detector_state.json"


def _state():
    return json.loads(STATE.read_text()) if STATE.exists() else {}


def _save_state(s):
    STATE.write_text(json.dumps(s, indent=1))


def _fire(detector, ticker, sev, evidence):
    print(f"DETFIRE|{detector}|{ticker}|{sev}|{evidence[:240]}")


def _note(detector, ticker, msg):
    print(f"DETNOTE|{detector}|{ticker}|{msg[:160]}")


# ---------------- detector runners ----------------
def run_litigation(ticker):
    from verticals.buyside_dd.connectors.litigation_screen import screen_entity
    try:
        r = screen_entity(BU.legal(ticker), is_person=False)
    except Exception as e:
        return _note("litigation", ticker, f"error {e}")
    if r.get("error"):
        return _note("litigation", ticker, r["error"])
    mh = r.get("material_hits") or []
    if mh:
        cases = "; ".join(f"{h['case']} ({h.get('subj','')}{h['bucket']})" for h in mh[:3])
        _fire("litigation", ticker, "HIGH", f"{len(mh)} MATERIAL federal docket(s): {cases}")
    else:
        _note("litigation", ticker, f"{r.get('dockets',0)} dockets, 0 material")


def run_usaspending(ticker):
    from verticals.buyside_dd.connectors.usaspending import UsaSpendingConnector
    from verticals.buyside_dd.connectors.base import ConnectorRequest
    try:
        res = UsaSpendingConnector().query(ConnectorRequest(entity_name=BU.legal(ticker)))
    except Exception as e:
        return _note("usaspending", ticker, f"error {e}")
    if not res.success:
        return _note("usaspending", ticker, f"{res.error_kind}: {(res.error_detail or '')[:80]}")
    obs = {o.attribute: o.value for o in res.observations}
    by_agency = obs.get("federal_awards_by_agency") or {}
    total = sum(by_agency.values()) if isinstance(by_agency, dict) and by_agency else None
    if total is None:
        total = next((o.value for o in res.observations if isinstance(o.value, (int, float))), None)
    st = _state(); key = f"usaspending:{ticker}"; prior = st.get(key)
    st[key] = total; _save_state(st)
    if total is None:
        return _note("usaspending", ticker, "awards found, total not parsed")
    if prior and prior > 0 and total < prior * 0.85:
        _fire("usaspending", ticker, "HIGH",
              f"federal award flow DOWN {(total/prior-1)*100:.0f}% (${total/1e6:.0f}M vs ${prior/1e6:.0f}M) — contract-cut tell")
    else:
        _note("usaspending", ticker, f"federal awards ${total/1e6:.0f}M (no material drop vs prior)")


def run_hiring(ticker):
    from verticals.buyside_dd.connectors.hiring_velocity import fetch_postings, ramp_metrics
    feat = BU.BOOK[ticker]["capacity_ramp"]; kw, loc = feat
    try:
        rows = fetch_postings(kw, loc)
        m = ramp_metrics(rows)
    except Exception as e:
        return _note("hiring_velocity", ticker, f"error/needs-key {e}")
    wave = m.get("wave") or m.get("trend")
    if m.get("postings", 0) and (wave in ("RAMP", "WAVE") or (m.get("velocity", 0) and m["velocity"] > 1.3)):
        _fire("hiring_velocity", ticker, "MED", f"hiring wave at {loc}: {m}")
    else:
        _note("hiring_velocity", ticker, f"{m.get('postings','?')} postings, no wave")


def run_customer(ticker):
    from verticals.buyside_dd.connectors.customer_id import resolve_shipping_entities, customs_consignees
    try:
        shippers = resolve_shipping_entities(BU.legal(ticker))
        if not shippers:
            return _note("customer_id", ticker, "no shipper alias resolved (foreign fill-finish bypasses US customs?)")
        cons = customs_consignees(shippers[0])
        top = (cons.get("consignees") or [])[:3]
        if top:
            _fire("customer_id", ticker, "MED", f"customs consignees (undisclosed-customer tell): {top}")
        else:
            _note("customer_id", ticker, "shipper resolved, no consignees")
    except Exception as e:
        _note("customer_id", ticker, f"error/needs-key {e}")


def run_satellite(ticker):
    pa = BU.BOOK[ticker]["physical_asset"]
    # the free connectors need lat/lon AOIs; we carry text AOIs only -> escalation note, not a silent pass
    _note("satellite", ticker, f"AOI '{pa.get('aoi')}' ({pa.get('kind')}) needs lat/lon to execute — escalation/on-demand")


DETECTORS = {
    "litigation":      {"feature": "litigation",      "cadence": "monthly", "run": run_litigation},
    "usaspending":     {"feature": "gov_revenue",     "cadence": "weekly",  "run": run_usaspending},
    "hiring_velocity": {"feature": "capacity_ramp",   "cadence": "monthly", "run": run_hiring},
    "customer_id":     {"feature": "undisclosed_cust","cadence": "monthly", "run": run_customer},
    "satellite":       {"feature": "physical_asset",  "cadence": "monthly", "run": run_satellite},
}


def scan(detector):
    d = DETECTORS[detector]
    subset = BU.names_with(d["feature"])
    print(f"# detector_scan {detector} over {len(subset)} book name(s): {subset}")
    for t in subset:
        try:
            d["run"](t)
        except Exception as e:
            _note(detector, t, f"runner error {e}")
        time.sleep(0.3)


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    for d in (DETECTORS if which == "all" else [which]):
        scan(d)
