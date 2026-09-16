"""Live validation: Carbon Mapper satellite connector + how it augments detector confidence.

Run from repo root:
    python3 -m verticals.buyside_dd.validate_carbon_mapper

Three things demonstrated end-to-end against the REAL public API:
  1. DISCRIMINATION — connector returns super-emitter plumes over an active O&G basin
     and zero over a clean control area.
  2. CONFIDENCE LIFT — feeding the Tier-1 satellite observation into the EXISTING
     comparator._compute_confidence raises a weakly-sourced environmental finding's
     confidence (the "augment our detectors to get confidence" mechanic).
  3. HONESTY CONTRADICTION — when a marketed "no significant methane" claim meets a
     measured plume, it flips to a refuted/SEVERE finding at Tier-1 confidence.
"""
from __future__ import annotations

from verticals.buyside_dd.connectors.base import ConnectorRequest
from verticals.buyside_dd.connectors.carbon_mapper import CarbonMapperConnector
from verticals.buyside_dd.comparator import _compute_confidence
from verticals.buyside_dd.schemas import StopReason
from verticals.buyside_dd.source_atlas import source_by_id

# Known active O&G basin (Permian, TX/NM) vs. a clean rural control (NE Vermont).
POSITIVE = {"name": "Permian Basin O&G AOI (TX/NM)", "lat": 31.9, "lon": -102.3, "radius_km": 40}
CONTROL = {"name": "Rural control (NE Vermont)", "lat": 44.55, "lon": -72.0, "radius_km": 40}


def run_site(site: dict) -> "object":
    conn = CarbonMapperConnector()
    req = ConnectorRequest(extra={"lat": site["lat"], "lon": site["lon"],
                                  "radius_km": site["radius_km"], "gas": "CH4",
                                  "emission_min_kg_hr": 0})
    res = conn.query(req)
    print(f"\n── {site['name']}  (lat {site['lat']}, lon {site['lon']}, r={site['radius_km']}km)")
    if not res.success:
        print(f"   query failed: {res.error_kind} — {res.error_detail}")
        return res
    by = {o.attribute: o for o in res.observations}
    present = by["methane_super_emitter_present"].value
    n = by["methane_plume_count"].value
    mx = by["methane_max_emission_kg_hr"].value
    n_super = by["methane_super_emitter_present"].extra.get("n_super_emitters")
    print(f"   super-emitter present: {present}   plumes: {n}   max: {mx:,.0f} kg/hr   "
          f"super-emitters(>=1000): {n_super}")
    for o in res.observations:
        if o.attribute.startswith("methane_plume["):
            p = o.value
            print(f"      • {p['emission_kg_hr']:>8,.0f} kg/hr  {p['gas']}  "
                  f"{p['instrument'] or '?':24} {p['acq_date'] or '?'}  q={p['quality']}  {p['plume_id']}")
            if o.attribute.endswith("[4]"):
                print("        …(showing 5 strongest)")
                break
    return res


def demo_confidence_augmentation(sat_result) -> None:
    """Show the comparator's confidence change when the satellite source is added."""
    print("\n" + "=" * 78)
    print("CONFIDENCE AUGMENTATION (verticals/buyside_dd/comparator.py::_compute_confidence)")
    print("=" * 78)
    cm = source_by_id("carbon_mapper")               # authority_tier = 1
    weak = source_by_id("zillow_redfin_sale_snippet")  # authority_tier = 5 (stand-in weak web src)

    # BEFORE: an environmental_status finding backed only by a weak Tier-5 web snippet.
    before = _compute_confidence([_FakeOK("zillow_redfin_sale_snippet")],
                                 [weak], StopReason.CONVERGED)
    # AFTER: add the Tier-1 satellite measurement as a corroborating source.
    after = _compute_confidence([_FakeOK("zillow_redfin_sale_snippet"), sat_result],
                                [weak, cm], StopReason.CONVERGED)
    print(f"  environmental finding, weak web source only      -> confidence {before:.2f}")
    print(f"  + Carbon Mapper Tier-1 satellite corroboration   -> confidence {after:.2f}"
          f"   (+{after - before:.2f})")

    print("\nHONESTY CONTRADICTION (Mode-B): marketed claim vs. measured plume")
    print("  Claim:    issuer/operator markets 'no significant methane emissions at the asset'")
    print("            (expected: methane_super_emitter_present = False)")
    sp = next(o for o in sat_result.observations if o.attribute == "methane_super_emitter_present")
    print(f"  Observed: methane_super_emitter_present = {sp.value}  "
          f"(max {next(o for o in sat_result.observations if o.attribute=='methane_max_emission_kg_hr').value:,.0f} kg/hr, "
          f"Tier-1 instrument-measured)")
    contradiction = (sp.value is True)
    verdict = "REFUTED / SEVERE — independent satellite measurement contradicts the claim" if contradiction \
        else "consistent — no super-emitter measured"
    conf = _compute_confidence([sat_result], [source_by_id("carbon_mapper")], StopReason.CONFLICT
                               if contradiction else StopReason.CONVERGED)
    print(f"  Finding:  {verdict}")
    print(f"            confidence {conf:.2f} at authority_tier 1")


class _FakeOK:
    """Minimal stand-in ConnectorResult for the weak baseline source (success + 1 obs)."""
    def __init__(self, source_id):
        from datetime import datetime, timezone
        from verticals.buyside_dd.connectors.base import ConnectorObservation, ConnectorRequest, ConnectorResult
        self._r = ConnectorResult(source_id=source_id, request=ConnectorRequest(),
                                  queried_at=datetime.now(timezone.utc), success=True,
                                  observations=[ConnectorObservation(attribute="environmental_status",
                                                                     value="mention", confidence=0.5)])
    # _compute_confidence accesses .success, .observations, .source_id
    success = property(lambda s: s._r.success)
    observations = property(lambda s: s._r.observations)
    source_id = property(lambda s: s._r.source_id)


def main():
    print("CARBON MAPPER CONNECTOR — live validation against the public plume catalog")
    pos = run_site(POSITIVE)
    run_site(CONTROL)
    if pos.success:
        demo_confidence_augmentation(pos)
    print("\ndone.")


if __name__ == "__main__":
    main()
