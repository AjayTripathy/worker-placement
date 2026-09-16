"""broken_print_radar v2 — offline tests.

Everything here runs with NO network. The four things v2 added are exactly the four things
that can silently break it: the reaction thresholds (does an 8%/3x day fire and does an 8%
drift NOT), the degraded-loud accounting (does a half-priced universe say so), the session
windows (the ONON root cause — does the radar know a US break at 11am is worth looking at),
and international suffix handling (does a bare TSE code become 7122.T rather than a Yahoo
'possibly delisted').
"""
import datetime

import pytest

from desk.broken_print_radar import (
    INTRADAY_MIN_DROP, LEG_SHELVES, REACT_MOVE, REACT_VOLX, SHELVES,
    _cap_str, _clean_name, _fmt_cap, _ledger_status, _leverage_phrase, _shelf_leverage,
    _window_key, degraded_summary, legs_due, load_shelf, reaction_scan,
    us_session_phase, yahoo_symbol,
)


# ---------------------------------------------------------------- helpers

def _bars(closes, vols, start="2026-08-01"):
    d0 = datetime.date.fromisoformat(start)
    return {"dates": [(d0 + datetime.timedelta(days=i)).isoformat() for i in range(len(closes))],
            "close": list(closes), "volume": list(vols)}


def _flat(n=25, px=100.0, vol=1_000_000.0):
    return [px] * n, [vol] * n


# ---------------------------------------------------------------- reaction thresholds

def test_reaction_fires_on_8pct_with_3x_volume():
    c, v = _flat()
    c.append(91.0)          # -9.0%
    v.append(3_500_000.0)   # 3.5x
    rows = reaction_scan({"AAA.L": _bars(c, v)})
    assert len(rows) == 1
    r = rows[0]
    assert r["trigger"] == "REACTION" and r["volume_confirmed"] is True
    assert r["drop_pct"] == pytest.approx(-9.0, abs=0.05)
    assert r["vol_x_adv"] == pytest.approx(3.5, abs=0.05)


def test_8pct_on_normal_volume_does_not_fire():
    """The volume leg is the whole point — an 8% bar alone fires on every thin Helsinki line."""
    c, v = _flat()
    c.append(91.0)
    v.append(1_200_000.0)   # 1.2x — a drift, not a repricing
    assert reaction_scan({"AAA.L": _bars(c, v)}) == []


def test_high_volume_small_move_does_not_fire():
    c, v = _flat()
    c.append(97.0)          # -3%
    v.append(9_000_000.0)   # 9x volume, but nothing broke
    assert reaction_scan({"AAA.L": _bars(c, v)}) == []


def test_hard_drop_fires_without_volume_confirmation():
    """A -20% day is a question even on quiet turnover; it is labelled volume-unconfirmed,
    never dropped (DATA MISSING is not DATA CLEAN)."""
    c, v = _flat()
    c.append(80.0)
    v.append(1_100_000.0)
    rows = reaction_scan({"AAA.L": _bars(c, v)})
    assert len(rows) == 1 and rows[0]["trigger"] == "HARD"
    assert rows[0]["volume_confirmed"] is False


def test_both_triggers_label_union_not_blend():
    c, v = _flat()
    c.append(78.0)
    v.append(8_000_000.0)
    assert reaction_scan({"AAA.L": _bars(c, v)})[0]["trigger"] == "HARD+REACTION"


def test_thresholds_are_the_documented_pair():
    assert (REACT_MOVE, REACT_VOLX) == (-8.0, 3.0)
    assert INTRADAY_MIN_DROP == -12.0   # the ONON fix: a name at -14% must be visible


def test_backfill_index_scans_a_prior_session():
    """--backfill walks idx -1, -2, … — the break must be found on the day it happened, not
    smeared onto today."""
    c, v = _flat(25)
    c += [88.0, 88.5]          # break on the second-to-last bar
    v += [5_000_000.0, 900_000.0]
    b = {"AAA.L": _bars(c, v)}
    assert reaction_scan(b, idx=-1) == []
    hit = reaction_scan(b, idx=-2)
    assert len(hit) == 1 and hit[0]["session"] == b["AAA.L"]["dates"][-2]


def test_missing_or_short_history_is_skipped_not_fabricated():
    assert reaction_scan({"AAA.L": {"dates": [], "close": [], "volume": []}}) == []
    assert reaction_scan({"AAA.L": _bars([100.0], [1.0])}) == []
    # a zero/None previous close cannot produce a percentage — refuse rather than divide
    assert reaction_scan({"AAA.L": _bars([0.0, 50.0], [1.0, 9e9])}) == []


def test_rows_sorted_worst_first():
    c1, v1 = _flat(); c1.append(80.0); v1.append(6e6)
    c2, v2 = _flat(); c2.append(70.0); v2.append(6e6)
    rows = reaction_scan({"AAA.L": _bars(c1, v1), "BBB.L": _bars(c2, v2)})
    assert [r["ticker"] for r in rows] == ["BBB.L", "AAA.L"]


# ---------------------------------------------------------------- degraded-loud

def test_degraded_counts_and_names_the_unpriced():
    req = [f"S{i}.T" for i in range(10)]
    bars = {s: _bars(*_flat(3)) for s in req[:3]}
    d = degraded_summary(req, bars)
    assert (d["requested"], d["priced"], d["unpriced"]) == (10, 3, 7)
    assert d["priced_pct"] == 30.0 and d["degraded"] is True
    assert set(d["unpriced_names"]) == set(req[3:])


def test_not_degraded_above_half_but_still_names_casualties():
    req = [f"S{i}.T" for i in range(10)]
    bars = {s: _bars(*_flat(3)) for s in req[:8]}
    d = degraded_summary(req, bars)
    assert d["degraded"] is False and d["unpriced"] == 2
    assert d["unpriced_names"] == ["S8.T", "S9.T"]


def test_unpriced_name_list_is_truncated_with_a_count():
    req = [f"S{i}.T" for i in range(100)]
    d = degraded_summary(req, {}, name_cap=5)
    assert len(d["unpriced_names"]) == 5 and d["unpriced_truncated"] == 95


def test_empty_close_series_counts_as_unpriced():
    """Yahoo returns a symbol with an empty frame on the 'possibly delisted' wave — that is
    NOT a priced name."""
    d = degraded_summary(["A.T"], {"A.T": {"dates": [], "close": [], "volume": []}})
    assert d["priced"] == 0 and d["unpriced"] == 1


# ---------------------------------------------------------------- session windows (the ONON fix)

def _et(h, m=0, day=11):
    return datetime.datetime(2026, 8, day, h, m)   # 2026-08-11 is a Tuesday


def test_us_session_phase_boundaries():
    assert us_session_phase(_et(7)) == "PRE"
    assert us_session_phase(_et(9, 29)) == "PRE"
    assert us_session_phase(_et(9, 30)) == "RTH"
    assert us_session_phase(_et(15, 59)) == "RTH"
    assert us_session_phase(_et(16, 0)) == "POST"
    assert us_session_phase(_et(21)) == "CLOSED"
    assert us_session_phase(datetime.datetime(2026, 8, 15, 11)) == "CLOSED"   # Saturday


def test_onon_break_hour_now_has_a_leg_due():
    """THE REGRESSION TEST FOR THE MISS. ONON printed pre-market 2026-08-11 and broke through
    the morning. v1 was cadence-'daily' and had run at 01:35 PT, so nothing looked again until
    the next small hours. At 11:00 ET a US leg must now be due, and it must be the INTRADAY one."""
    due = legs_due(_et(11))
    assert "us_intraday" in due and "us_settled" not in due


def test_settled_leg_owns_the_overnight_and_premarket_hours():
    assert legs_due(_et(1)) == ["us_settled"]
    assert "us_settled" in legs_due(_et(8))
    assert "us_settled" in legs_due(_et(17))
    assert "us_intraday" not in legs_due(_et(17))


def test_intraday_and_settled_are_mutually_exclusive():
    for h in range(0, 24):
        due = legs_due(_et(h, 30))
        assert not ("us_intraday" in due and "us_settled" in due)


def test_international_legs_gate_on_their_own_close_not_new_yorks():
    asia = legs_due(_et(3, 30))     # TSE 15:00 JST / KRX 15:30 KST already settled
    assert "asia" in asia and "europe" not in asia
    eu = legs_due(_et(12, 30))      # LSE 16:30 London / Euronext 17:30 CET already settled
    assert "europe" in eu and "asia" not in eu
    assert "europe" not in legs_due(_et(9))      # Europe still trading — nothing settled to read
    assert "asia" not in legs_due(_et(1))


def test_no_leg_is_due_on_a_weekend():
    assert legs_due(datetime.datetime(2026, 8, 15, 11)) == []    # Saturday
    assert legs_due(datetime.datetime(2026, 8, 16, 3, 30)) == []  # Sunday


def test_window_guard_key_lets_intraday_repeat_hourly_but_pins_the_rest():
    assert _window_key("us_intraday", _et(10)) != _window_key("us_intraday", _et(11))
    assert _window_key("europe", _et(12)) == _window_key("europe", _et(13))


def test_settled_key_is_the_session_it_reports_not_the_wall_date():
    """The post-close run and the next pre-open run report the SAME session, so they share a
    key and the second is skipped. Keyed on the wall date instead, the 03:30 ET run consumes
    the day's slot and the post-close scan never happens — v1's one-day lag."""
    assert _window_key("us_settled", _et(20)) == _window_key("us_settled", _et(2, day=12))
    assert _window_key("us_settled", _et(20)) != _window_key("us_settled", _et(2))


# ---------------------------------------------------------------- international symbols

def test_bare_tse_code_gets_the_t_suffix():
    assert yahoo_symbol("7122", "EDINET_JP") == "7122.T"
    assert yahoo_symbol(7122, "EDINET_JP") == "7122.T"
    assert yahoo_symbol("135A", "EDINET_JP") == "135A.T"      # post-2024 alphanumeric TSE codes


def test_existing_suffix_is_never_rewritten():
    assert yahoo_symbol("7122.T", "EDINET_JP") == "7122.T"
    assert yahoo_symbol("052790.KQ", "KRX") == "052790.KQ"    # KOSDAQ line stays KOSDAQ
    assert yahoo_symbol("EOLU-B.ST", "EURONEXT") == "EOLU-B.ST"


def test_korea_six_digit_defaults_to_kospi():
    assert yahoo_symbol("052790", "KRX") == "052790.KS"
    assert yahoo_symbol("5279", "KRX") is None                # not a KRX code — refuse, don't guess


def test_lse_tidm_gets_the_l_suffix():
    assert yahoo_symbol("AVON", "LSE") == "AVON.L"
    assert yahoo_symbol("avon", "LSE") == "AVON.L"


def test_euronext_uses_the_venue_when_the_symbol_is_bare():
    assert yahoo_symbol("SFPI", "EURONEXT", venue="PAR") == "SFPI.PA"
    assert yahoo_symbol("AD", "EURONEXT", venue="AMS") == "AD.AS"
    # no suffix and no venue is UNRESOLVED — a bare symbol sent to Yahoo returns
    # 'possibly delisted', which is indistinguishable from a real delisting
    assert yahoo_symbol("SFPI", "EURONEXT") is None


def test_malformed_symbols_return_none_not_a_guess():
    for bad in (None, "", "   ", "."):
        assert yahoo_symbol(bad, "EDINET_JP") is None


def test_shelves_are_wired_and_load_a_real_universe():
    """Offline: the shelf files ship with the repo. A shelf that silently resolves to nothing is
    the failure mode this guards — an empty universe reports 'quiet tape' and is wrong."""
    assert set(LEG_SHELVES["asia"]) | set(LEG_SHELVES["europe"]) == set(SHELVES)
    for key in SHELVES:
        syms, meta, unresolved = load_shelf(key)
        assert len(syms) > 100, f"{key} shelf resolved only {len(syms)} symbols"
        assert all(s == s.upper() and "." in s for s in syms[:50])
        assert all(meta[s]["shelf"] == key for s in syms[:50])


def test_shelf_cap_truncates_the_broad_universe_not_the_shortlist():
    """File order is priority order: the researched shortlist is read first, so a cap eats the
    tail (the price-cache universe), never the names we already care about."""
    full, _, _ = load_shelf("EDINET_JP")
    capped, _, _ = load_shelf("EDINET_JP", cap=50)
    assert len(capped) == 50 and capped == full[:50]


# ---------------------------------------------------------------- ledger tagging

# ---------------------------------------------------------------- units and the shelf fallback

def test_money_carries_its_currency():
    """A JPY balance sheet behind a '$' is off by ~150x AND perfectly plausible-looking, which
    is what makes it dangerous."""
    assert _fmt_cap(2.5e9) == "$2.5B"
    assert _fmt_cap(2.5e9, "JPY") == "¥2.5B"
    assert _fmt_cap(5e8, "KRW") == "₩500M"
    assert _fmt_cap(None) == "market cap unknown"


def test_cap_string_prefers_usd_then_names_the_local_unit():
    assert _cap_str({"market_cap": 3e9}) == "$3.0B"
    assert _cap_str({"market_cap_local": 3e9, "market_cap_ccy": "JPY"}) == "¥3.0B"
    assert _cap_str({}) == "market cap unknown"


def test_leverage_phrase_never_prints_dollars_for_a_yen_balance_sheet():
    r = {"leverage_read": "LOW", "net_debt": 1.2e10, "net_debt_ebitda": 1.4,
         "fin_ccy": "JPY", "leverage_metric": "trailing EBIT (shelf filing data — EBITDA not reported)",
         "leverage_basis": "EDINET_JP filing as of 2026-03-31"}
    p = _leverage_phrase(r)
    assert "$" not in p and "¥12.0B" in p
    assert "EBIT" in p and "x trailing EBITDA" not in p     # says which line it divided by
    assert "EDINET_JP filing as of 2026-03-31" in p          # and where the number came from


def test_shelf_leverage_labels_ebit_and_handles_net_cash():
    lev = _shelf_leverage({"shelf_cash": 2e9, "shelf_debt": 5e8, "shelf_ebit": 3e8,
                           "shelf": "EDINET_JP", "shelf_asof": "2026-03-31"})
    assert lev["leverage_read"] == "NET_CASH" and lev["net_debt"] == -1.5e9
    assert "EBIT" in lev["leverage_metric"] and "EBITDA not reported" in lev["leverage_metric"]
    # same LOW/MODERATE/HIGH bands as the US leg (<=2.5x, <=4x, above) so one sheet reads as one
    lev2 = _shelf_leverage({"shelf_cash": 1e8, "shelf_debt": 9e8, "shelf_ebit": 2e8})
    assert lev2["net_debt_ebitda"] == 4.0 and lev2["leverage_read"] == "MODERATE"
    lev3 = _shelf_leverage({"shelf_cash": 1e8, "shelf_debt": 1.3e9, "shelf_ebit": 2e8})
    assert lev3["leverage_read"] == "HIGH" and lev3["balance_sheet_intact"] is False


def test_shelf_leverage_with_no_filing_data_returns_nothing_not_zero():
    """DATA MISSING never becomes DATA CLEAN: an absent balance sheet must leave the row's
    UNKNOWN in place rather than writing a confident zero."""
    assert _shelf_leverage({"shelf_cash": None, "shelf_debt": None}) == {}


def test_local_currency_caps_never_land_in_the_usd_slot():
    """The Japan/Korea caches hold market cap in JPY/KRW. If those land in the USD field the
    sheet prints a ¥434B mid-cap as '$434.0B' — a mega-cap that does not exist."""
    for key in ("EDINET_JP", "KRX"):
        _, meta, _ = load_shelf(key, cap=200)
        locals_seen = 0
        for m in meta.values():
            assert m["shelf_mcap_usd"] is None, f"{key} put a local-currency cap in the USD slot"
            if m.get("shelf_mcap_local"):
                locals_seen += 1
                assert m["shelf_ccy"] in ("JPY", "KRW")
        assert locals_seen > 50
    # the Western shelves DO carry a converted USD cap, and that one is allowed in the USD slot
    _, eu, _ = load_shelf("EURONEXT", cap=200)
    assert sum(1 for m in eu.values() if m["shelf_mcap_usd"]) > 50


def test_html_escapes_never_reach_a_fire_line():
    assert _clean_name("YAGI &amp; CO.,LTD.") == "YAGI & CO.,LTD."
    assert _clean_name(None) is None and _clean_name("  ") is None


def test_japan_and_korea_names_and_balance_sheets_come_from_the_filing_offline():
    """The rate-limit lesson: Yahoo enrichment dies right after a bulk history sweep, so the
    shelf must already know the name and the capital structure without a network call."""
    for key, sample in (("EDINET_JP", "7122.T"), ("KRX", "052790.KQ")):
        _, meta, _ = load_shelf(key)
        m = meta[sample]
        assert m["name"] and m["name"] != sample
        assert m["shelf_facts_source"] in ("EDINET", "DART")
        assert m["shelf_cash"] is not None
        assert m["shelf_ccy"] in ("JPY", "KRW")


def test_ledger_status_distinguishes_unresearched_from_a_standing_view():
    assert _ledger_status({}) == "UNRESEARCHED"
    assert _ledger_status({"ledger_verdict": None}) == "UNRESEARCHED"
    assert _ledger_status({"held": True}) == "HELD"
    assert _ledger_status({"ledger_verdict": "STARTER"}).startswith("LEDGER:")
    # holding it outranks the ledger line — a break in a held name is a re-underwrite
    assert _ledger_status({"held": True, "ledger_verdict": "STARTER"}) == "HELD"
