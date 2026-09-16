"""assemble — stage the officekit OSS distribution (A0).

Copies the six officekit* packages out of the monorepo into build/, alongside
pyproject.toml and README.md, then (if pip can) builds a wheel into dist/.
The desk's own pyproject.toml at the repo root is untouched — the desk is
tenant #1, not the package.

    python3 officekit_dist/assemble.py            # stage + attempt wheel
    python3 officekit_dist/assemble.py --no-wheel # stage only

PUBLISH IS A SEPARATE, PRINCIPAL-GATED STEP: the public repo gets fresh git
history, and the license is chosen at publish time.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PACKAGES = ["officekit", "officekit_ai", "officekit_agents", "officekit_adapters",
            "officekit_research", "officekit_signals"]
# desk/tenant files that must never ship even if they appear inside a package dir
# The DESIGN references ship with the OSS (PRD, ARCHITECTURE, SCHEMAS,
# OPERATING_CONTRACTS) — contributors need them. Only genuinely internal docs stay
# out: the roadmap/intelligence doc (has private household + employer context), the
# LLM intake-agent prompt, and the agent-to-agent handoff (commit hashes, machine
# specifics). Private data has been scrubbed from the shipped docs (2026-09-13).
EXCLUDE = shutil.ignore_patterns("__pycache__", "*.pyc", "evals", "demo_recorder.py",
                                 "INTELLIGENCE.md", "INTAKE_AGENT.md", "AGENT_HANDOFF.md")


def stage(build_dir=None):
    build = Path(build_dir) if build_dir is not None else HERE / "build"
    if build.exists():
        shutil.rmtree(build)
    build.mkdir(parents=True)
    for pkg in PACKAGES:
        src = ROOT / pkg
        if not src.is_dir():
            sys.exit(f"[assemble] missing package {src}")
        shutil.copytree(src, build / pkg, ignore=EXCLUDE)
    # Audited example/template only; household thesis packs remain tenant data.
    bundled = build / "officekit" / "bundled_strategies"
    for pack in ("_template", "muni_dislocation"):
        shutil.copytree(ROOT / "strategies" / pack, bundled / pack)
    for f in ("pyproject.toml", "setup.cfg", "README.md"):
        shutil.copy2(HERE / f, build / f)
    n = sum(1 for _ in build.rglob("*.py"))
    print(f"[assemble] staged {len(PACKAGES)} packages ({n} .py files) -> {build}")
    return build


def wheel(build):
    dist = HERE / "dist"
    r = subprocess.run([sys.executable, "-m", "pip", "wheel", str(build),
                        "-w", str(dist), "--no-deps"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print("[assemble] wheel build failed (staging is still valid):")
        print((r.stderr or r.stdout)[-800:])
        return False
    whl = sorted(dist.glob("worker_placement-*.whl"))
    print(f"[assemble] wheel -> {whl[-1] if whl else dist}")
    return True


if __name__ == "__main__":
    b = stage()
    if "--no-wheel" not in sys.argv:
        wheel(b)
