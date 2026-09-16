"""Unit contract for verticals/public_co/detectors/concentration_instability.

Pins the pure text classifier classify() — no network — on the synthetic cases
distilled from the live cohort back-test (VRRM / Skyworks / Marqeta / Cirrus /
Fabrinet / Lockheed). The cohort calibration that these cases encode:

  * The detector is HIGH-PRECISION / NARROW. It fires ONLY on the *prospective*
    instability tell (short-term extension pending renewal / active renegotiation /
    expired-unrenewed) paired with a >10% customer. Generic "we sell on short-term
    purchase orders / no long-term contracts" boilerplate is NON-discriminating
    (controls Cirrus/Fabrinet carry it and retained the customer) and must NOT fire.
  * Concentration parsing must survive multi-year %-lists ("71%, 69% and 70% of
    net revenue") and verb variants ("generated/derived ... of revenue from"),
    must NOT count negated no-concentration disclosures ("no customer ... >10%"),
    and must NOT count segment / gross-margin / product-mix percentages.

Run: python3 tests/test_concentration_instability.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from verticals.public_co.detectors import concentration_instability as ci

# Verbatim-style at-risk disclosure (the VRRM tell): >10% customer + prospective
# instability (short-term extension + active renewal negotiations).
VRRM_TELL = (
    "Commercial Services Customer Contracts. We are currently operating under a "
    "short-term contract extension and are engaged in contract negotiations with one "
    "of our significant Commercial Services customers which represented over 10% of "
    "our total revenue for the period.")

# Concentration WITHOUT the prospective tell (Marqeta-style retrospective reprice).
MARQETA_STABLE = (
    "Our largest customer, Block, accounted for 71%, 69% and 70% of our net revenue, "
    "respectively. In August 2023 we amended the agreement on different terms.")

# Concentration described as locked-in / boilerplate-only (Skyworks/Cirrus control).
BOILERPLATE = (
    "We had one end customer, Apple Inc., representing a significant portion of "
    "revenue. Sales are made primarily pursuant to short-term purchase orders and "
    "not under long-term supply arrangements.")


def test_fires_on_prospective_tell():
    c = ci.classify(VRRM_TELL)
    assert c["fires"] is True
    assert c["category"] == "CONCENTRATION_INSTABILITY"
    assert "short_term_extension" in c["instability_markers"]
    assert "renewal_negotiations" in c["instability_markers"]


def test_evaluate_headlines_conservative_floor():
    # at-risk customer disclosed via bare ">10%" -> headline ">10%", never a higher
    # (possibly segment-level) run figure.
    out = ci.evaluate("Verra Mobility", {"filing_text": VRRM_TELL})
    assert out["fires"] is True and out["signal"] == "ELEVATE"
    assert ">10%" in out["finding"]["R"]
    assert "~37" not in out["finding"]["R"] and "~95" not in out["finding"]["R"]


def test_concentration_without_tell_does_not_fire():
    c = ci.classify(MARQETA_STABLE)
    assert c["category"] == "CONCENTRATION_STABLE"   # concentration SEEN...
    assert c["fires"] is False                       # ...but no prospective tell
    assert c["top_customer_pct"] == 71.0             # multi-year list parsed


def test_boilerplate_only_does_not_fire():
    c = ci.classify(BOILERPLATE)
    assert c["fires"] is False                        # generic boilerplate != tell


def test_multi_year_and_verb_variants_parse():
    assert ci.classify("We generated 72% and 69% of our net revenue from our largest "
                        "customer, Block.")["top_customer_pct"] == 72.0
    assert ci.classify("We derived 24% of our net revenue from one customer."
                        )["top_customer_pct"] == 24.0
    assert ci.classify("One customer represented 28% of total revenue."
                        )["top_customer_pct"] == 28.0


def test_negation_is_not_concentration():
    for neg in ("No customer accounted for more than 10% of our revenue.",
                "No single customer represented more than 10% of net revenue in any period."):
        c = ci.classify(neg)
        assert c["category"] == "NO_CONCENTRATION", neg
        assert c["top_customer_pct"] is None, neg


def test_segment_and_margin_pcts_excluded():
    # gross-margin and product-mix percentages must not register as customer concentration
    assert ci.classify("Gross margin increased to 53.8% on higher revenue."
                        )["category"] == "NO_CONCENTRATION"
    assert ci.classify("Data communication products were 75.4% of our revenues."
                        )["category"] == "NO_CONCENTRATION"


def test_long_appositive_curly_apostrophe_run_parses():
    # SWKS Note 14 regression (surfaced by the escalation loop): customer name sits ~200
    # chars before the verb behind a long appositive, the %s render as inline-XBRL "69 %"
    # with a curly apostrophe in "Company's", and the run reads "69 %, 66 %, and 58 %".
    swks = ("During fiscal 2024, fiscal 2023, and fiscal 2022, Apple, through sales to "
            "multiple distributors, contract manufacturers, and direct sales for multiple "
            "applications including smartphones, tablets, desktop, and notebook computers, "
            "watches and other devices, in the aggregate accounted for 69 %, 66 %, and 58 % "
            "of the Company’s net revenue, respectively.")
    c = ci.classify(swks)
    assert c["top_customer_pct"] == 69.0          # concentration now SEEN...
    assert c["category"] == "CONCENTRATION_STABLE"  # ...and correctly no-fire (boilerplate)
    # the fix must NOT re-admit segment/product percentages
    assert ci.classify("The segment represented 95.4% of segment revenue."
                       )["category"] == "NO_CONCENTRATION"


def test_concentration_alone_is_stable_not_fire():
    # A locked-in big customer with NO instability markers is CONCENTRATION_STABLE.
    c = ci.classify("Our largest customer, NVIDIA Inc., represented 28% of total revenue "
                    "under a three-year supply agreement with automatic renewals.")
    assert c["category"] == "CONCENTRATION_STABLE" and c["fires"] is False


def main() -> None:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print(f"  ok  {t.__name__}")
    print(f"\n{len(tests)} passed")


if __name__ == "__main__":
    main()
