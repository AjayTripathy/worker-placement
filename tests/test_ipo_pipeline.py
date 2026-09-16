"""Unit contract for the PURE logic in verticals/buyside_dd/ipo_pipeline.py.

The end-to-end queue can't be golden-mastered: build_queue() makes live EDGAR
network calls, uses a date.today()-relative window, and stamps generated_at.
But the filtering / classification / dedupe / summary logic is pure and is what
actually encodes the SignalOS routing decisions — so pin it directly on
synthetic filings.

Run: python3 tests/test_ipo_pipeline.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from verticals.buyside_dd.ipo_pipeline import (
    SIC_TO_DETECTORS,
    classify_for_signalos,
    filter_and_dedupe,
    is_fund,
    is_shell,
    is_spac,
    summarize_queue,
)


def _hit(name, cik, file_date="2026-05-01", forms=("S-1",), acc=None):
    return {
        "_id": acc or f"acc-{cik}-{file_date}",
        "_source": {
            "display_names": [name] if name is not None else [],
            "ciks": [cik] if cik is not None else [],
            "file_date": file_date,
            "forms": list(forms),
        },
    }


def test_spac_fund_shell_predicates():
    assert is_spac("Pine Tree Acquisition Corp") is True
    assert is_spac("Blue Water Biotech Inc") is True          # BLUE WATER
    assert is_spac("Acme Robotics Inc") is False
    assert is_fund("Grayscale Bitcoin Trust") is True         # GRAYSCALE / TRUST
    assert is_fund("iShares Core S&P 500 ETF") is True
    assert is_fund("Acme Robotics Inc") is False
    assert is_shell("XYZ Shell Co") is True
    assert is_shell("Acme Robotics Inc") is False
    # Empty / None must not raise and must not match.
    assert is_spac("") is False and is_fund(None) is False and is_shell(None) is False


def test_classify_known_default_and_whitespace():
    biotech = classify_for_signalos({"sic": "2836", "sicDescription": "Pharma"})
    assert biotech["suggested_signalos_detectors"] == SIC_TO_DETECTORS["2836"]
    assert biotech["sic"] == "2836" and biotech["sic_description"] == "Pharma"
    # Unknown SIC falls back to the cross-cutting default.
    unknown = classify_for_signalos({"sic": "9999"})
    assert unknown["suggested_signalos_detectors"] == SIC_TO_DETECTORS["_default"]
    # Missing SIC -> "" -> default; surrounding whitespace is stripped.
    assert classify_for_signalos({})["sic"] == ""
    assert classify_for_signalos({})["suggested_signalos_detectors"] == SIC_TO_DETECTORS["_default"]
    assert classify_for_signalos({"sic": "  2836 "})["suggested_signalos_detectors"] == SIC_TO_DETECTORS["2836"]


def test_filter_drops_spac_fund_shell_and_no_cik():
    filings = [
        _hit("Pine Tree Acquisition Corp", "100"),   # spac
        _hit("Grayscale Bitcoin Trust", "200"),      # fund
        _hit("XYZ Shell Co", "300"),                 # shell
        _hit("Headless Co", None),                   # no_cik
        _hit("Acme Robotics Inc", "400"),            # keep
    ]
    operating, skipped = filter_and_dedupe(filings)
    assert skipped == {"spac": 1, "fund": 1, "shell": 1, "no_cik": 1}
    assert [c["company_name"] for c in operating] == ["Acme Robotics Inc"]
    assert operating[0]["cik"] == "400" and operating[0]["_accession"] == "acc-400-2026-05-01"


def test_dedupe_keeps_most_recent_filing_per_cik():
    filings = [
        _hit("Acme Robotics Inc", "400", file_date="2026-03-01", forms=("S-1",), acc="old"),
        _hit("Acme Robotics Inc", "400", file_date="2026-05-15", forms=("S-1/A",), acc="new"),
    ]
    operating, skipped = filter_and_dedupe(filings)
    assert len(operating) == 1
    assert operating[0]["file_date"] == "2026-05-15"
    assert operating[0]["_accession"] == "new"
    assert operating[0]["forms"] == ["S-1/A"]


def test_missing_names_are_silently_skipped_not_counted():
    filings = [_hit(None, "500"), _hit("Acme Robotics Inc", "400")]
    operating, skipped = filter_and_dedupe(filings)
    assert [c["cik"] for c in operating] == ["400"]
    # No display_name -> `continue` before any skipped[...] bucket is touched.
    assert sum(skipped.values()) == 0


def test_summarize_queue_groups_by_sector():
    queue = {
        "generated_at": "2026-05-29",
        "days_back": 30,
        "raw_filings_count": 2,
        "operating_company_count": 2,
        "skipped": {"spac": 1, "fund": 0, "shell": 0, "no_cik": 0},
        "companies": [
            {
                "cik": "400", "company_name": "Acme Robotics Inc",
                "file_date": "2026-05-15", "forms": ["S-1"],
                "metadata": {"tickers": ["ACME"]},
                "signalos_classification": {
                    "sic": "3812", "sic_description": "Aerospace",
                    "suggested_signalos_detectors": SIC_TO_DETECTORS["3812"],
                },
            },
            {
                "cik": "401", "company_name": "Beacon Bio Inc",
                "file_date": "2026-05-10", "forms": ["F-1"],
                "metadata": {"tickers": []},
                "signalos_classification": {
                    "sic": "2836", "sic_description": "Pharma",
                    "suggested_signalos_detectors": SIC_TO_DETECTORS["2836"],
                },
            },
        ],
    }
    md = summarize_queue(queue)
    assert md.startswith("# Signal OS IPO Pipeline Queue")
    assert "**Generated**: 2026-05-29" in md
    assert "### 3812 - Aerospace (1 companies)" in md
    assert "### 2836 - Pharma (1 companies)" in md
    assert "ACME" in md and "Acme Robotics Inc" in md
    # Empty ticker list renders the em-dash placeholder.
    assert "| — |" in md


def main() -> None:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print(f"  ok  {t.__name__}")
    print(f"\n{len(tests)} passed")


if __name__ == "__main__":
    main()
