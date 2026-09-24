"""OSS publish policy: the DESIGN references ship; internal docs don't; and no
shipping doc leaks an account number (principal-directed 2026-09-13 — ship the
design, scrub the private data). Fast (no wheel build)."""
import re
from pathlib import Path

import officekit_dist.assemble as assemble

ROOT = Path(__file__).resolve().parents[1]
SHIP = ["PRD.md", "ARCHITECTURE.md", "SCHEMAS.md", "OPERATING_CONTRACTS.md", "INTAKE_AGENT.md"]
KEEP_OUT = ["INTELLIGENCE.md", "AGENT_HANDOFF.md"]


def _ignored(name):
    return name in assemble.EXCLUDE("officekit", SHIP + KEEP_OUT + ["serve.py"])


def test_design_docs_ship_and_internal_docs_do_not():
    for d in SHIP:
        assert not _ignored(d), f"{d} is a design reference and must ship in the OSS wheel"
    for d in KEEP_OUT:
        assert _ignored(d), f"{d} is internal (roadmap/agent/handoff) and must NOT ship"


def test_no_account_number_in_shipping_docs():
    acct = re.compile(r"\bU\d{8}\b")            # IBKR account-number shape
    for d in SHIP:
        p = ROOT / "officekit" / d
        if p.exists():
            hits = acct.findall(p.read_text())
            assert not hits, f"{d} leaks an account number: {hits}"
