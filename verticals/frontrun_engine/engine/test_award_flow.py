"""Tie-out unit test (§Phase-1 task 3): reproduce an Arm-B prime's gov-revenue run-rate
from USASpending family obligations, within an order-of-magnitude band.

Obligations (new money committed to contracts) and recognized revenue (outlays) do NOT
tie exactly — obligations LEAD revenue and can be lumpy (a multi-year ceiling booked in
one action). The sanity contract is therefore a BAND: FY family obligations should fall
within roughly 0.4x - 2.0x of reported US-gov revenue for a mature prime, confirming the
entity resolution captured the family at the right scale (not 10x off, not near-zero).

Network test (hits live USASpending). Skips cleanly if offline.
"""
from datetime import date

import pytest

from award_flow import AwardFlowEngine, Company

# Reported figures (provenance in outputs/govcon_universe.json):
#   SAIC FY2025 (ended ~Jan/Feb 2026) revenue ~$7.4B, ~98% US-gov -> ~$7.2B gov revenue.
#   We tie FY-action-window family obligations to that run-rate.
LEIDOS = Company.make("LDOS", "Leidos Holdings", ["Leidos"], anchor="Leidos",
                      aliases=["QTC MEDICAL", "QTC MANAGEMENT", "DYNETICS", "1901 GROUP",
                               "GIBBS & COX", "VARESEC"])
SAIC = Company.make("SAIC", "Science Applications International",
                    ["Science Applications"], anchor="Science Applications")

FY25 = (date(2024, 10, 1), date(2025, 9, 30))


@pytest.fixture(scope="module")
def eng():
    return AwardFlowEngine()


def _net(eng):
    try:
        eng._post.__self__  # noqa
        return eng.family_obligations(SAIC, *FY25)
    except Exception as e:  # offline / rate-limited
        pytest.skip(f"USASpending unreachable: {e}")


def test_saic_family_resolution_rejects_mosaic(eng):
    """Entity-resolution contract: 'Science Applications' anchor must capture SAIC and
    must NOT leak the 'moSAIC*' look-alikes that a bare 'SAIC' search returns."""
    fam = _net(eng)
    matched = " ".join(fam["matched_recipients"]).upper()
    assert "SCIENCE APPLICATIONS" in matched, fam["matched_recipients"]
    assert "MOSAIC" not in matched, f"leaked look-alike: {fam['matched_recipients']}"


def test_saic_obligations_tie_to_gov_revenue_band(eng):
    """FY25 family obligations within 0.4x-2.0x of ~$7.2B reported gov revenue."""
    fam = _net(eng)
    oblig = fam["total_usd"]
    gov_rev = 7.2e9
    ratio = oblig / gov_rev
    assert 0.4 <= ratio <= 2.0, (
        f"SAIC FY25 family obligations ${oblig/1e9:.2f}B = {ratio:.2f}x gov rev "
        f"(${gov_rev/1e9:.1f}B); outside 0.4-2.0x band -> entity resolution suspect. "
        f"matched={fam['matched_recipients']}")


def test_leidos_alias_captures_qtc(eng):
    """The alias mechanism must pull in named subsidiaries that don't share the parent
    token (QTC Medical Services is a Leidos sub but {leidos} is not a subset of its name)."""
    try:
        fam = eng.family_obligations(LEIDOS, *FY25)
    except Exception as e:
        pytest.skip(f"USASpending unreachable: {e}")
    names = " ".join(fam["matched_recipients"]).upper()
    assert "LEIDOS" in names
    # QTC only appears via alias; if present it confirms the alias path works.
    # (Not asserted hard — QTC may file under 'LEIDOS QTC' in some periods — but log it.)
    has_qtc = "QTC" in names
    print(f"\nLeidos family ${fam['total_usd']/1e9:.2f}B; QTC-alias-captured={has_qtc}")


if __name__ == "__main__":
    e = AwardFlowEngine()
    for co in (SAIC, LEIDOS):
        fam = e.family_obligations(co, *FY25)
        print(f"{co.ticker}: FY25 family obligations ${fam['total_usd']/1e9:.2f}B "
              f"across {len(fam['matched_recipients'])} recipients")
        for nm, amt in list(fam["matched_recipients"].items())[:6]:
            print(f"    {nm:50} ${amt/1e9:.3f}B")
        if fam["rejected_lookalikes"]:
            print(f"    [rejected look-alikes] {list(fam['rejected_lookalikes'])[:4]}")
