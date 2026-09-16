"""CDS legs of the AI-break tripwires: DTCC file discovery/parse/diff and the FRED weekly anchor. No network."""
import json
from pathlib import Path

import pytest

from desk import cds_activity_watch as CW
from desk import weekly_dashboard as WD


def test_list_files_parses_escaped_dtcc_page():
    page = ('{"href":"\\/\\/files.dtcc.com\\/download\\/assets\\/Final-Single-Name-Q3-2025_A1.xlsx\\/f9fa"}'
            '{"href":"//files.dtcc.com/download/assets/Final-Single-Name-Q2-2025_41.xlsx/f7d2"}'
            '{"href":"//files.dtcc.com/download/assets/Final-Index-Q3-2025_0F.xlsx/f59a"}')
    files = CW.list_files(page)
    assert [f["name"] for f in files] == ["2025Q3", "2025Q2"]              # newest first, index file excluded
    assert files[0]["url"].startswith("https://files.dtcc.com/")


def test_diff_fires_canary_and_activity():
    prev = {"ORCL": {"entity": "ORACLE CORPORATION", "dealers": 8, "notional_per_day": 75e6, "canary": False}}
    cur = {"ORCL": {"entity": "ORACLE CORPORATION", "dealers": 12, "notional_per_day": 120e6, "canary": False},
           "CRWV": {"entity": "COREWEAVE INC", "dealers": 3, "notional_per_day": 10e6, "canary": True}}
    fires = CW.diff(prev, cur)
    assert any(f.startswith("CANARY-LISTED CRWV") for f in fires)
    assert any(f.startswith("AI-ACTIVITY-UP ORCL") and "+60%" in f for f in fires)
    assert CW.diff(cur, cur) == []                                          # no change, no fire
    assert CW.diff(None, {"ORCL": cur["ORCL"]}) == []                       # first file, non-canary: baseline only


def test_watched_maps_entities_to_tickers():
    rows = [{"entity": "ORACLE CORPORATION", "dealers": 8}, {"entity": "COREWEAVE INC", "dealers": 1},
            {"entity": "ABBOTT LABORATORIES", "dealers": 0}]
    w = CW.watched(rows)
    assert set(w) == {"ORCL", "CRWV"} and w["CRWV"]["canary"] and not w["ORCL"]["canary"]


@pytest.mark.skipif(not (Path(CW.DATA) / "single_name_2025Q3.xlsx").exists(), reason="DTCC file not fetched")
def test_parse_real_q3_2025_file():
    rows = CW.parse_file(Path(CW.DATA) / "single_name_2025Q3.xlsx")
    w = CW.watched(rows)
    assert w["ORCL"]["dealers"] == 8 and w["ORCL"]["notional_per_day"] == 75e6
    assert "CRWV" not in w                                                  # the canary is absent in Q3-2025


def test_fred_weekly_anchors_to_friday(monkeypatch):
    daily = {"2026-09-07": 100.0, "2026-09-08": 101.0, "2026-09-09": 102.0, "2026-09-10": 103.0,
             "2026-09-11": 104.0, "2026-09-14": 110.0}
    monkeypatch.setattr(WD, "fred_csv", lambda sid: daily)
    w = WD.fred_weekly("X")
    assert w == {"2026-09-11": 104.0, "2026-09-18": 110.0}                 # last obs of each week, Friday key
