"""Unit contract for verticals/public_co/sec_tables — the generic concentration ingestor.

Pins the table + qualitative extraction on synthetic fixtures distilled from the real
filings it was validated against (Fabrinet named-row + AR split, Universal Display /
Photronics coded rows, Cirrus qualitative sole-customer), plus the negatives it must
stay silent on (stock-comp volatility / margin tables). Pure-text, no network.

Run: python3 tests/test_sec_tables.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from verticals.public_co import sec_tables as st


def _by_entity(recs):
    return {r["entity"]: r for r in recs}


def test_named_rows_with_split_percent_cells():
    # "12.0 | %" — number and % in adjacent flattened cells (Fabrinet/UDC shape)
    text = ("Significant customers Total revenues, by percentage, from individual "
            "customers representing 10% or more of total revenues\n"
            "NVIDIA Corporation | 35.1 | % | 28.0 | %\n"
            "Cisco Systems, Inc. | 18.2 | % | 13.4 | %\n")
    recs = st.extract_concentration_records(text)
    ents = _by_entity(recs)
    assert "NVIDIA Corporation" in ents and ents["NVIDIA Corporation"]["pct"] == 35.1
    assert "Cisco Systems, Inc" in ents or "Cisco Systems, Inc." in ents
    assert all(r["source"] == "table" for r in recs)


def test_accounts_receivable_denominator_split():
    # a revenue table followed by an AR table — same shape, different denominator
    text = ("Significant customers from individual customers representing 10% of total revenues\n"
            "Lumentum Operations LLC | 15.4 | %\n"
            "Accounts receivable from individual customers representing 10% or more\n"
            "Nokia Corporation | 12.0 | % | 19.3 | %\n")
    recs = st.extract_concentration_records(text)
    ents = _by_entity(recs)
    assert ents["Lumentum Operations LLC"]["denominator"] == "revenue"
    assert "receivable" in ents["Nokia Corporation"]["denominator"]


def test_coded_rows_with_customer_context():
    text = ("Customers accounting for 10% or more of our consolidated revenues:\n"
            "A | 43 | % | 23 | %\n"
            "B | 21 | % | 18 | %\n")
    recs = st.extract_concentration_records(text)
    pcts = sorted(r["pct"] for r in recs)
    assert 43.0 in pcts and 21.0 in pcts


def test_footnote_resolves_only_generic_codes():
    # "(1)" on a generic code resolves; "(1)" on a NAMED company never overrides the name
    text = ("Significant customers representing 10% of total revenues\n"
            "Customer A (1) | 30 | %\n"
            "Nokia Corporation (2) | 12 | %\n"
            "(1) Customer A consists of NVIDIA Corporation.\n"
            "(2) Includes Infinera Corporation as of June 2025.\n")
    ents = _by_entity(st.extract_concentration_records(text))
    assert "NVIDIA Corporation" in ents          # code resolved
    assert any("Nokia" in e for e in ents)        # named company kept, NOT renamed to Infinera
    assert "Infinera Corporation" not in ents


def test_qualitative_sole_customer():
    rec = [r for r in st.extract_concentration_records(
        "For fiscal years 2025, 2024, and 2023, we had one end customer, Apple Inc.")
        if r["source"] == "qualitative"]
    assert rec and rec[0]["entity"] == "Apple Inc"   # bounded, not "Apple Inc. Our ..."


def test_qualitative_negation_not_caught():
    recs = st.extract_concentration_records(
        "We did not have any single customer that accounted for more than 10% of revenue.")
    assert not any(r["source"] == "qualitative" for r in recs)


def test_volatility_and_margin_tables_are_silent():
    for neg in (
        "Expected stock price volatility | 35.70 | % | 34.53 | %\nRisk-free interest rate | 4.33 | %",
        "Gross margin | 45.2 | % | 43.1 | %\nOperating margin | 12.0 | %",
        "Effective tax rate | 21.0 | % | 19.5 | %",
    ):
        assert st.extract_concentration_records(neg) == [], neg


def test_below_threshold_excluded():
    text = ("Customers representing 10% or more of revenues\n"
            "Customer A | 14.6 | %\nCustomer C | 8 | %\n")
    ents = _by_entity(st.extract_concentration_records(text))
    assert "Customer A" in ents and "Customer C" not in ents


def main() -> None:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print(f"  ok  {t.__name__}")
    print(f"\n{len(tests)} passed")


if __name__ == "__main__":
    main()
