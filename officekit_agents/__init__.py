"""officekit_agents — the shipped agent directives (U0: plane 1 of the memory model).

The unified-agent-layer ruling (2026-09-04) made the desk's agents the product:
ONE architecture, the desk as flagship tenant, end users bringing their own
models. This package is the plane-1 corpus — the directives themselves,
versioned like code — extracted from the desk's live agent definitions and
court doctrine.

Three-plane discipline, enforced here:
  plane 1  the directives in directives/ — generic doctrine, leak-tested:
           no principal names, employers, household holdings, or account
           identifiers, ever. Public-company case law STAYS (the ICFI/JJSF/
           MLTX-class lessons are research history, not personal data — the
           glass-box thesis made literal).
  plane 2  NEVER shipped as content, ALWAYS consumed as structure: compose()
           refuses without a personal-context document (contract #9), and the
           rendered context is injected under a mandatory heading every
           directive is written to honor.
  plane 3  the tenant's own accumulated memory — not this package's concern.

Model names inside historical doctrine ("Opus" benches, "Fable" adjudication)
are CAPABILITY TIERS, not vendor bindings — the preamble maps them to the
tenant's models.json slots (contract #10): volume tier -> bench, strong tier
-> adjudicate/verify. The invariants travel with the mapping: benches evenly
matched, the adjudicator never weaker than the bench, adjudication never
rubber-stamps.
"""
from __future__ import annotations

import json
from pathlib import Path

DIR = Path(__file__).resolve().parent / "directives"

# directive -> the models.json slots it exercises (contract #10)
SLOTS = {
    "court": ("bench", "adjudicate"),
    "diligence": ("bench", "verify"),
    "watch": ("classify", "verify"),
}
DEFAULT_SLOTS = ("verify",)

PREAMBLE = """<!-- officekit_agents preamble: binds this directive to the tenant -->
## Binding (read first)

1. **Personal context is mandatory.** Your tenant's personal-context document
   (exclusions, doctrine rulings, jurisdictions, coordination surfaces) is
   injected below under "Tenant personal context". You must argue within it,
   cite doctrine ids when a ruling shapes an answer, and treat exclusions as
   absolute. If that section is missing, REFUSE to advise.
2. **Model tiers are slots.** Historical names in this doctrine ("Opus" =
   volume/bench tier, "Fable" = strong/adjudication tier) bind to the
   tenant's model slots, not to vendors. Invariants: benches evenly matched;
   the adjudicator is never weaker than the bench; adjudication never
   rubber-stamps — every decisive bench number is re-verified at adjudication.
3. **Reference implementation.** File paths (desk/*.py, court_*.py) name the
   flagship deployment's tooling. Where your deployment lacks a tool, say so
   and degrade loudly — never silently skip a verification step.
4. **Case law is history.** Tickers in this doctrine are public-company
   research precedents, cited for their failure patterns — they are not
   recommendations and not the tenant's holdings.
"""


def list_directives():
    return sorted(p.stem for p in DIR.glob("*.md"))


def load(name):
    """The raw shipped directive (plane 1). Raises KeyError on unknown names."""
    p = DIR / f"{name}.md"
    if not p.exists():
        raise KeyError(f"officekit_agents: no directive {name!r} (have: {', '.join(list_directives())})")
    return p.read_text()


def slots_for(name):
    return SLOTS.get(name, DEFAULT_SLOTS)


def render_personal_context(pc):
    """Plane 2, rendered for injection — structured, not prose, so the
    directive can cite exclusions and doctrine ids exactly."""
    return "\n## Tenant personal context (plane 2 — binding)\n\n```json\n" + \
        json.dumps({k: pc.get(k) for k in
                    ("exclusions", "doctrine", "jurisdictions", "external", "notes")
                    if pc.get(k)}, indent=1) + "\n```\n"


def compose(name, personal_context):
    """directive + binding preamble + the tenant's plane-2 context = the
    system prompt. REFUSES without personal context (empty-but-asserted
    passes; absent does not) — the plane-2 gate, same as every shipped agent."""
    from officekit.personal_context import require
    pc = require(personal_context, f"run directive {name!r}")
    return PREAMBLE + render_personal_context(pc) + "\n---\n\n" + load(name)
