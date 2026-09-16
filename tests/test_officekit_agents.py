"""officekit_agents — the plane-1 corpus gates (U0/U1 of the unified layer).

The leak test here is a CI BLOCKER by ruling: the shipped directives may carry
public-company case law, but never the principal's plane-2 content — names,
employer, household holdings, account identifiers, contact details. If a new
directive trips this, the fix is to move the personal fact into
personal_context.json, never to weaken the list.
"""
import re

import pytest

# plane-2 strings that must NEVER appear in shipped directives. Word-boundary
# regexes where substrings are risky (google_trends must not trip GOOGL).
PERSONAL = [
    r"\bAjay\b", r"\bTripathy\b", r"4tripathy", r"\bIBM\b",
    r"\bParametric\b", r"\bGOOGL\b", r"\bVCLAX\b", r"038CAG",
    r"\bVTSAX\b",                       # household ballast holdings
    r"Ajays-MacBook",
]


def _corpus():
    import officekit_agents as ag
    return {name: ag.load(name) for name in ag.list_directives()}


class TestPlaneOneCorpus:
    DOCTRINE = ["court", "verification", "honesty-forensics", "microstructure-artifacts",
                "valuation-sizing", "portfolio-doctrine", "research-operations",
                "muni-underwriting", "connectors-altdata"]

    def test_corpus_exists_and_covers_the_suite(self):
        import officekit_agents as ag
        names = ag.list_directives()
        assert "court" in names and "diligence" in names and "watch" in names
        for d in self.DOCTRINE:          # the distilled memory corpus (U0 second tranche)
            assert d in names, f"missing doctrine directive {d}"
        assert len(names) >= 21          # suite agents + doctrine corpus

    def test_doctrine_directives_are_substantive(self):
        import officekit_agents as ag
        for d in self.DOCTRINE:
            text = ag.load(d)
            assert len(text.splitlines()) >= 40, f"{d} suspiciously thin"
            assert text.count("## ") >= 5, f"{d} lacks doctrine sections"

    def test_portfolio_doctrine_is_condition_framed(self):
        """Portfolio rulings are tenant-conditional, never universal — the scope
        note must say so and rules must carry CONDITION lines."""
        import officekit_agents as ag
        text = ag.load("portfolio-doctrine")
        assert "CONDITIONAL rulings" in text
        assert text.count("CONDITION:") >= 10

    def test_no_personal_strings_ever(self):
        hits = []
        for name, text in _corpus().items():
            for pat in PERSONAL:
                for m in re.finditer(pat, text, re.I):
                    hits.append(f"{name}.md: {pat} -> …{text[max(0, m.start()-30):m.end()+30]!r}…")
        assert not hits, "plane-2 content in the shipped corpus:\n" + "\n".join(hits)

    def test_preamble_never_leaks_either(self):
        import officekit_agents as ag
        for pat in PERSONAL:
            assert not re.search(pat, ag.PREAMBLE, re.I)

    def test_court_carries_the_ratified_invariants(self):
        text = _corpus()["court"]
        assert "rubber-stamp" in text            # adjudication never rubber-stamps
        assert "evenly matched" in text          # bench symmetry
        assert "§TIER-STRUCTURE" in text

    def test_slots_reference_real_model_slots(self):
        import officekit_agents as ag
        from officekit_ai.models import SLOTS as MODEL_SLOTS
        for name in ag.list_directives():
            for slot in ag.slots_for(name):
                assert slot in MODEL_SLOTS, f"{name}: unknown slot {slot!r}"


class TestPlaneTwoGate:
    def test_compose_refuses_without_personal_context(self):
        import officekit_agents as ag
        with pytest.raises(RuntimeError, match="personal context required"):
            ag.compose("court", None)

    def test_compose_injects_the_tenant_context(self):
        import officekit_agents as ag
        from officekit.personal_context import empty
        pc = empty("a11e0f5e-9e1c-4f6d-8c2a-000000000001")
        pc["exclusions"].append({"scope": "issuer", "value": "ACME", "reason": "employer"})
        pc["doctrine"].append({"id": "no_leverage", "rule": "Never use margin."})
        out = ag.compose("court", pc)
        assert out.index("Binding (read first)") < out.index("Tenant personal context") \
            < out.index("Court Doctrine")
        assert '"ACME"' in out and "no_leverage" in out
        # empty-but-asserted also passes (the tenant said: no constraints)
        assert "Court Doctrine" in ag.compose("court", empty())

    def test_desk_instance_composes_cleanly(self):
        """The flagship tenant's own personal context composes with every
        directive — the desk is just tenant #1 of the unified layer."""
        import json
        from pathlib import Path
        import officekit_agents as ag
        pc = json.loads(Path("desk/data/personal_context.json").read_text())
        out = ag.compose("diligence", pc)
        assert "IBM" in out              # plane 2 carries it INTO the session…
        assert "IBM" not in ag.load("diligence")   # …the shipped plane never does
