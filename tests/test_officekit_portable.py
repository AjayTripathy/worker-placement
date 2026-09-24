"""Build/install the wheel and run a second office outside the monorepo.

No dependency downloads, broker calls or model calls. This proves the installed
package boundary; connecting each supported broker is a separate release gate.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile


def test_wheel_supports_an_independent_household(tmp_path):
    from officekit_dist.assemble import stage

    build = stage(tmp_path / "build")
    env = dict(os.environ, PIP_DISABLE_PIP_VERSION_CHECK="1", PIP_NO_INDEX="1",
               PYTHONPYCACHEPREFIX=str(tmp_path / "pycache"))
    def run(args):
        result = subprocess.run(args, cwd=tmp_path, env=env, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=120)
        assert result.returncode == 0, result.stdout[-6000:]
        return result.stdout

    run([sys.executable, "-m", "pip", "wheel", str(build), "--no-deps", "--no-build-isolation",
         "--no-cache-dir", "-w", str(tmp_path / "wheels")])
    wheel = next((tmp_path / "wheels").glob("worker_placement-*.whl"))
    with zipfile.ZipFile(wheel) as package:
        files = package.namelist()
        assert not any(f.startswith(("desk/", "verticals/")) for f in files)
        assert "officekit/bundled_strategies/muni_dislocation/DECK.md" in files
        for doc in ("PRD.md", "ARCHITECTURE.md", "SCHEMAS.md", "OPERATING_CONTRACTS.md", "COMMITMENTS.md", "README.md"):
            assert "officekit/" + doc in files
        for asset in ("landing.html", "site.css", "site.js", "auth.js", "mark.svg"):
            assert "officekit/public/" + asset in files
        assert "officekit/AGENT_HANDOFF.md" not in files
        metadata = package.read(next(f for f in files if f.endswith(".dist-info/METADATA"))).decode()
        for dep in ("ib-insync", "robin-stocks", "pyotp"):
            assert dep in metadata.lower().replace("_", "-")
    target = tmp_path / "installed"
    run([sys.executable, "-m", "pip", "install", str(wheel), "--no-deps", "--no-compile",
         "--no-cache-dir", "--target", str(target)])
    script = r'''
import json, sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import officekit
import officekit.serve as serve
from officekit.render_landing import render_landing
from officekit_ai.intake_chat import _system
assert 'ASSETS ONLY' in _system('assets')
assert 'GOALS ONLY' in _system('goals')
assert "Give every<br>dollar" in render_landing()
from officekit.strategy_packs import load_packs
from officekit_signals import CAPABILITIES, runtime, run_capability
from officekit_research import SOURCES
generic_tape = SOURCES["tape"]
import officekit_signals.fleet
assert SOURCES["tape"] is generic_tape
folder = Path("second-household")
serve._discover_cached = lambda: []
serve._key_status = lambda _: None
serve._ai = lambda *a, **k: False
serve.build_office({"as_of": "2026-09-13", "profile": {}, "positions": {"rows": [
    {"symbol": "AAA", "value": 1000}]}, "goals": [
    {"kind": "spending", "label": "Education", "date": "2031-09-01", "amount": 500}]}, folder)
saved = json.loads((folder / "answers.json").read_text())
serve.build_office(saved, folder)
assert (folder / "pages" / "risk.html").is_file()
assert (folder / "pages" / "capital.html").is_file()
packs, problems = load_packs()
assert not problems and [p["id"] for p in packs] == ["muni_dislocation"]
unavailable = [n for n, r in runtime(folder).items() if r["health"] == "UNAVAILABLE"]
assert unavailable
try:
    run_capability(folder, unavailable[0], {})
except RuntimeError as error:
    assert "not installed" in str(error)
else:
    raise AssertionError("missing fleet implementation falsely reported runnable")
assert Path(officekit.__file__).is_relative_to(Path(sys.argv[1]))
print(json.dumps({"installed": True, "missing_capabilities": len(unavailable)}))
'''
    output = run([sys.executable, "-I", "-c", script, str(target)])
    assert json.loads(output.splitlines()[-1])["installed"]
