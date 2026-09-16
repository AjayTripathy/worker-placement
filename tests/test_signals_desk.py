"""The desk fleet registered into the capability registry (F3b first sweep)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def test_fleet_registers_and_maps():
    import officekit_signals as sig
    import desk.signals_desk as sd
    assert sd.N_GENERATORS >= 40                      # the real generator fleet
    gens = [c for c in sig.CAPABILITIES.values() if c["kind"] == "generator"]
    assert len(gens) >= 41
    # hand-mapped strategy bindings resolve through the union
    names = {c["name"] for c in sig.applicable(strategy="quality_drawdown", kinds=("generator",))}
    assert "quality_drawdown" in names
    names = {c["name"] for c in sig.applicable(strategy="value_band_entry", kinds=("generator",))}
    assert "dislocation_sweep" in names and "lockup_expiry_scanner" in names
    # detectors wrapped from the buyside connectors
    for d in ("litigation_screen", "app_review_velocity", "gov_contracts"):
        assert d in sig.CAPABILITIES and sig.CAPABILITIES[d]["kind"] == "detector"
        assert sig.CAPABILITIES[d]["datasources"], f"{d} must enumerate datasources"


def test_wrapped_generators_ship_their_real_code():
    import officekit_signals as sig
    import desk.signals_desk  # noqa: F401
    code = sig.source_code("quality_drawdown")
    assert "def assess(" in code and len(code.splitlines()) > 300   # the scanner, not the wrapper
    # metadata parsed from the module's own docstring, never imported at registration
    cap = sig.CAPABILITIES["quality_drawdown"]
    assert "money actually came from" in (cap["label"] + cap["desc"])


def test_unmapped_generators_are_honestly_labeled():
    import officekit_signals as sig
    import desk.signals_desk  # noqa: F401
    unmapped = [c for c in sig.CAPABILITIES.values()
                if c["kind"] == "generator" and not c["applies_to"]["strategies"]
                and not c["applies_to"]["universal"]]
    assert unmapped, "expect some index-only generators"
    assert all("index-only" in c["desc"] for c in unmapped)
