"""quality_wishlist tests — the five gate criteria, the DEGRADED outcome, each band trigger,
each of the four trap guards, and the inactive-mode degradation.

All offline: the gate and the band engine are pure functions over synthetic annuals and
synthetic weekly price series, so nothing here touches SEC or Yahoo.
"""
import datetime as dt
import json

import pytest

from verticals.generators import quality_wishlist as QW


# ---------------------------------------------------------------- synthetic fundamentals

def annuals(n=11, *, roic=0.25, rev0=1000.0, rev_growth=0.08, gm=0.60, gm_drift=0.0,
            nd_ebitda=0.5, share_drift=-0.01, ni_margin=0.15, ebit_margin=0.25,
            goodwill=100.0, start_fy=2015, shares0=100.0, ni_series=None,
            ebit_margin_series=None):
    """A well-behaved compounder unless a knob is turned. ROIC is set by solving equity from
    the target: invested = NOPAT/roic, equity = invested - net_debt."""
    out = []
    for i in range(n):
        fy = start_fy + i
        rev = rev0 * (1 + rev_growth) ** i
        m = ebit_margin if ebit_margin_series is None else ebit_margin_series[i]
        ebit = rev * m
        ebitda = ebit * 1.2
        nd = nd_ebitda * ebitda
        nopat = ebit * (1 - 0.21)
        invested = nopat / roic if roic else 1e9
        equity = invested - nd
        ni = rev * ni_margin if ni_series is None else ni_series[i]
        sh = shares0 * (1 + share_drift) ** i
        g = gm + gm_drift * i
        out.append({
            "fy": fy, "end": f"{fy}-12-31", "revenue": rev, "gross_profit": rev * g,
            "gross_margin": g, "ebit": ebit, "op_margin": m, "net_income": ni,
            "eps_diluted": ni / sh, "tax_rate": 0.21, "nopat": nopat, "equity": equity,
            "cash": 0.0, "debt": nd, "net_debt": nd, "invested_capital": invested,
            "ebitda": ebitda, "ebitda_is_ebit_proxy": False, "dil_sh": sh,
            "goodwill": goodwill, "roic": roic, "roic_flag": None,
        })
    return out


def weekly(pattern, *, end=dt.date(2026, 8, 13)):
    """Weekly (date, price) pairs ending today; `pattern` is a list of prices oldest-first."""
    return [(end - dt.timedelta(weeks=len(pattern) - 1 - i), p) for i, p in enumerate(pattern)]


def flat_then(px_hist, px_now, n=550):
    """A long flat history at px_hist with the final week at px_now."""
    return weekly([px_hist] * (n - 1) + [px_now])


# ================================================================= §3 the quality gate

def test_gate_passes_a_clean_compounder():
    g = QW.quality_gate(annuals())
    assert g["status"] == "PASS", g["reasons"]
    assert g["stats"]["roic_yrs"] >= 8 and g["stats"]["rev_up_yrs"] >= 8
    assert g["stats"]["nd_ebitda"] < QW.MAX_ND_EBITDA
    assert g["stats"]["share_chg_pct"] < 0


def test_gate_fails_low_roic():
    g = QW.quality_gate(annuals(roic=0.09))
    assert g["status"] == "FAIL"
    assert any("ROIC" in r for r in g["reasons"])


def test_gate_fails_flat_revenue():
    a = annuals(rev_growth=0.0)
    for i, y in enumerate(a):          # alternate up/down so only ~half the years grow
        y["revenue"] = 1000.0 + (10 if i % 2 else 0)
    g = QW.quality_gate(a)
    assert g["status"] == "FAIL"
    assert any("revenue rose" in r for r in g["reasons"])


def test_gate_fails_eroding_gross_margin():
    # -150bps/yr, and the latest sits well below the median -> both limbs of criterion 3 fail
    g = QW.quality_gate(annuals(gm=0.60, gm_drift=-0.015))
    assert g["status"] == "FAIL"
    assert any("gross margin eroding" in r for r in g["reasons"])


def test_gate_tolerates_a_wobble_within_300bps():
    a = annuals(gm=0.60, gm_drift=-0.002)      # -20bps/yr, latest ~200bps under the median
    g = QW.quality_gate(a)
    assert g["status"] == "PASS", g["reasons"]


def test_gate_fails_leverage():
    g = QW.quality_gate(annuals(nd_ebitda=2.6))
    assert g["status"] == "FAIL"
    assert any("net debt/EBITDA" in r for r in g["reasons"])


def test_gate_fails_serial_diluter():
    g = QW.quality_gate(annuals(share_drift=+0.04))
    assert g["status"] == "FAIL"
    assert any("diluted shares" in r for r in g["reasons"])


def test_missing_leverage_is_never_clean():
    a = annuals()
    a[-1]["net_debt"] = None
    g = QW.quality_gate(a)
    assert g["status"] == "FAIL"
    assert any("UNKNOWN" in r for r in g["reasons"])


def test_short_history_is_degraded_not_passed_or_failed():
    g = QW.quality_gate(annuals(n=6))
    assert g["status"] == "DEGRADED"
    assert "INSUFFICIENT-HISTORY" in g["reasons"][0]
    assert g["stats"]["usable_years"] == 6


def test_unusable_years_do_not_count_toward_history():
    a = annuals(n=11)
    for y in a[:5]:
        y["dil_sh"] = None            # five years without a share count = five unusable years
    g = QW.quality_gate(a)
    assert g["status"] == "DEGRADED"


def test_gross_margin_unavailable_is_waived_loudly_not_silently():
    a = annuals()
    for y in a:
        y["gross_margin"] = y["gross_profit"] = None
    g = QW.quality_gate(a)
    assert g["status"] == "PASS"
    assert any("GM-UNAVAILABLE-WAIVED" in f for f in g["flags"])


def test_unbounded_roic_counts_but_is_flagged():
    a = annuals()
    for y in a:
        y["roic"], y["roic_flag"] = float("inf"), "ROIC_UNBOUNDED"
    g = QW.quality_gate(a)
    assert g["status"] == "PASS"
    assert any("ROIC_UNBOUNDED" in f for f in g["flags"])


# ================================================================= §4 the bands

def test_percentile_rank():
    assert QW.pct_rank([1, 2, 3, 4], 2) == 50.0
    assert QW.pct_rank([1, 2, 3, 4], 4) == 100.0
    assert QW.pct_rank([], 1) is None


def _band_series(hi_px, lo_px, now_px, n=550):
    """History that spends half its life at hi_px and half at lo_px, ending at now_px."""
    half = (n - 1) // 2
    return weekly([hi_px] * half + [lo_px] * (n - 1 - half) + [now_px])


def test_fair_band_fires_tranche_one():
    a = annuals()
    wk = _band_series(200.0, 100.0, 140.0)     # ~in the middle of its own range
    res = QW.evaluate_name("TEST", a, wk, today=dt.date(2026, 8, 13))
    assert res["status"] == "FIRE"
    assert res["band"] == "FAIR" and res["sizing_label"] == "tranche-1"
    assert res["severity"] == "LOW"
    assert res["sleeve"]["aggregate_cap_pct"] == 8.0


def test_cheap_band_fires_starter():
    a = annuals()
    wk = _band_series(200.0, 100.0, 60.0)      # below everything it has ever traded at
    res = QW.evaluate_name("TEST", a, wk, today=dt.date(2026, 8, 13))
    assert res["status"] == "FIRE"
    assert res["band"] == "CHEAP" and res["sizing_label"] == "starter"
    assert res["pct"] <= QW.CHEAP_PCT


def test_expensive_name_does_not_fire():
    a = annuals()
    wk = _band_series(200.0, 100.0, 400.0)
    res = QW.evaluate_name("TEST", a, wk, today=dt.date(2026, 8, 13))
    assert res["status"] == "NO_FIRE" and res["band"] is None


def _standstill_case(n=550, end=dt.date(2026, 8, 13)):
    """The SPGI class, built by construction. Net debt and share count are held constant so the
    multiple is exactly price/earnings, which lets the fixture DICTATE the multiple path: nine
    years oscillating across the name's whole range, then a price that goes dead flat for the
    final 52 weeks while earnings keep compounding. Not one down week in the series."""
    a = annuals(n=11, nd_ebitda=0.0, share_drift=0.0, start_fy=2016)
    for i, y in enumerate(a):
        y["end"] = f"{y['fy']}-06-30"                   # June year-end: the latest print is recent
        boost = 1.0 if i < 10 else 1.35                 # +35% EBIT in the final reported year
        y["ebit"] = y["revenue"] * 0.25 * boost
        y["op_margin"] = 0.25 * boost
        y["net_income"] = y["ebit"] * 0.75
        y["eps_diluted"] = y["net_income"] / y["dil_sh"]
        y["ebitda"] = y["ebit"] * 1.2
        y["net_debt"] = y["debt"] = 0.0
    febit, fsh = QW._interp(a, "ebit"), QW._interp(a, "dil_sh")
    dates = [end - dt.timedelta(weeks=n - 1 - i) for i in range(n)]
    px, flat = [], None
    for i, d in enumerate(dates):
        if i < n - 53:
            target = 15 + 15 * ((i % 100) / 100.0)      # uniform over its own historical range
            px.append(target * febit(d) / fsh(d))
        else:
            if flat is None:
                flat = 22.5 * febit(d) / fsh(d)         # mid-range on the day the price stopped
            px.append(flat)                             # ...and then nothing happens for a year
    return a, list(zip(dates, px))


def test_standstill_fires_without_a_drawdown():
    a, wk = _standstill_case()
    assert wk[-1][1] == wk[-53][1]                      # the price genuinely did not move
    res = QW.evaluate_name("TEST", a, wk, today=dt.date(2026, 8, 13))
    assert res["standstill"] is True, (res["pct"], res["pct_1y_ago"])
    assert res["status"] == "FIRE"
    assert res["pct_1y_ago"] - res["pct"] >= QW.STANDSTILL_DROP_PTS


def test_standstill_requires_rising_eps():
    """Same percentile slide but EPS FALLING is not a standstill — it is a de-rate."""
    a = annuals(n=11)
    for i, y in enumerate(a):
        if i >= 9:
            y["eps_diluted"] = a[8]["eps_diluted"] * 0.5
    assert QW.standstill_trigger(10.0, 80.0, a) is False
    assert QW.standstill_trigger(10.0, 80.0, annuals(n=11)) is True


def test_thin_band_history_is_degraded_never_silent():
    res = QW.evaluate_name("TEST", annuals(), weekly([100.0] * 50), today=dt.date(2026, 8, 13))
    assert res["status"] == "DEGRADED"
    assert "THIN-BAND-HISTORY" in res["reason"]


def test_quiet_period_suppresses_a_repeat_but_not_a_deepening():
    a = annuals()
    wk = _band_series(200.0, 100.0, 60.0)      # CHEAP
    today = dt.date(2026, 8, 13)
    prior_same = {"band": "CHEAP", "fired": (today - dt.timedelta(days=5)).isoformat()}
    assert QW.evaluate_name("T", a, wk, today=today, prior=prior_same)["status"] == "NO_FIRE"
    prior_fair = {"band": "FAIR", "fired": (today - dt.timedelta(days=5)).isoformat()}
    assert QW.evaluate_name("T", a, wk, today=today, prior=prior_fair)["status"] == "FIRE"
    prior_old = {"band": "CHEAP", "fired": (today - dt.timedelta(days=90)).isoformat()}
    assert QW.evaluate_name("T", a, wk, today=today, prior=prior_old)["status"] == "FIRE"


# ================================================================= §5 the four trap guards

def test_guard1_peak_earnings_downgrades_to_review():
    a = annuals(ebit_margin_series=[0.20] * 10 + [0.34])     # latest margin above its own p90
    assert QW.guard_peak_earnings(a) is not None
    wk = _band_series(200.0, 100.0, 60.0)
    res = QW.evaluate_name("TEST", a, wk, today=dt.date(2026, 8, 13))
    assert res["status"] == "FIRE" and res["severity"] == "REVIEW"
    assert any("PEAK-EARNINGS" in g for g in res["guards"])
    assert "normalize" in res["route"]


def test_guard1_does_not_fire_on_a_normal_year():
    assert QW.guard_peak_earnings(annuals()) is None


def test_guard2_crash_cheapness_routes_to_the_dislocation_pipeline():
    a = annuals()
    wk = _band_series(200.0, 100.0, 60.0)
    res = QW.evaluate_name("TEST", a, wk, today=dt.date(2026, 8, 13),
                           dislocated="dislocation_sweep HIGH")
    assert res["status"] == "FIRE" and res["severity"] == "REVIEW"
    assert res["route"].startswith("dislocation_pipeline")
    assert any("CRASH-CHEAPNESS" in g for g in res["guards"])


def test_guard2_absent_when_the_name_is_not_falling():
    assert QW.guard_crash_cheapness("TEST", False) is None
    res = QW.evaluate_name("TEST", annuals(), _band_series(200.0, 100.0, 60.0),
                           today=dt.date(2026, 8, 13), dislocated=None)
    assert res["route"].startswith("court:")


def test_guard3_acquisition_stepup_suppresses_the_pe_percentile():
    a = annuals()
    a[-1]["dil_sh"] = a[-2]["dil_sh"] * 1.25            # equity-funded acquisition
    a[-1]["goodwill"] = a[-2]["goodwill"] * 1.9
    assert QW.guard_acq_stepup(a) is not None
    res = QW.evaluate_name("TEST", a, _band_series(200.0, 100.0, 60.0), today=dt.date(2026, 8, 13))
    assert res["pe_suppressed"] is True
    assert res["pct_pe"] is None and res["pct_ev_ebit"] is not None
    assert res["pct"] == res["pct_ev_ebit"]
    assert any("ACQ-STEP-UP" in g for g in res["guards"])


def test_guard3_ignores_organic_years():
    assert QW.guard_acq_stepup(annuals()) is None


def test_guard4_value_trap_decay_surfaces_after_twelve_months():
    today = dt.date(2026, 8, 13)
    assert QW.guard_value_trap_decay({"cheap_since": (today - dt.timedelta(days=200)).isoformat()},
                                     today) is None
    msg = QW.guard_value_trap_decay({"cheap_since": (today - dt.timedelta(days=400)).isoformat()},
                                    today)
    assert msg and "MANDATORY RE-GATE" in msg
    res = QW.evaluate_name("TEST", annuals(), _band_series(200.0, 100.0, 60.0), today=today,
                           prior={"cheap_since": (today - dt.timedelta(days=400)).isoformat()})
    assert res.get("value_trap_decay") is True


# ================================================================= §6 wash-sale flag

def test_parametric_name_carries_the_wash_sale_check():
    res = QW.evaluate_name("GOOGL", annuals(), _band_series(200.0, 100.0, 60.0),
                           today=dt.date(2026, 8, 13), parametric={"GOOGL"})
    assert res["wash_sale_check"] is True
    assert any("WASH-SALE-CHECK" in g for g in res["guards"])


def test_non_parametric_name_is_not_flagged():
    res = QW.evaluate_name("XYZ", annuals(), _band_series(200.0, 100.0, 60.0),
                           today=dt.date(2026, 8, 13), parametric={"GOOGL"})
    assert res["wash_sale_check"] is False


def test_parametric_file_is_created_with_googl(tmp_path, monkeypatch):
    p = tmp_path / "parametric_holdings.txt"
    monkeypatch.setattr(QW, "PARAMETRIC", p)
    held = QW.parametric_holdings()
    assert "GOOGL" in held
    assert "manually maintained" in p.read_text().lower()


# ================================================================= §2 inactive-mode degradation

def test_watch_is_inactive_and_fires_nothing_before_the_cull(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(QW, "ACTIVE", tmp_path / "quality_wishlist_active.json")
    monkeypatch.setattr(QW, "CANDIDATES", tmp_path / "cands.json")

    def _boom(*a, **k):                      # watch must not touch the network when inactive
        raise AssertionError("inactive watch mode must not price anything")
    monkeypatch.setattr(QW, "weekly_prices", _boom)

    res = QW.run_watch()
    assert res == {"active": False, "fires": [], "watched": 0}
    out = capsys.readouterr().out
    assert "INACTIVE" in out and "DEGRADED-LOUD" in out
    assert "NO BAND-FIRE IS POSSIBLE" in out
    assert "DETFIRE" not in out


def test_watch_stays_inactive_on_an_empty_or_corrupt_active_file(tmp_path, monkeypatch):
    p = tmp_path / "active.json"
    monkeypatch.setattr(QW, "ACTIVE", p)
    monkeypatch.setattr(QW, "CANDIDATES", tmp_path / "cands.json")
    p.write_text("{not json")
    assert QW.load_active() is None
    p.write_text(json.dumps({"asof": "2026-08-13", "tickers": []}))
    assert QW.load_active() is None
    p.write_text(json.dumps({"asof": "2026-08-13", "tickers": ["aapl", "MSFT"]}))
    assert QW.load_active() == ["AAPL", "MSFT"]


# ================================================================= plumbing

def test_financial_sic_exclusion():
    assert QW.is_financial(6021) and QW.is_financial(6311) and QW.is_financial(6798)
    assert not QW.is_financial(7372) and not QW.is_financial(2844) and not QW.is_financial(None)
    assert not QW.is_financial(6500)          # 65xx real estate is NOT in the excluded ranges


def test_fiscal_year_labelling():
    assert QW._fy_of("2025-12-31") == 2025
    assert QW._fy_of("2026-01-31") == 2025     # Jan year-end belongs to the prior fiscal label
    assert QW._fy_of("2025-06-30") == 2025


def test_annuals_from_companyfacts_shape():
    facts = {"entityName": "Test Co", "facts": {"us-gaap": {
        "Revenues": {"units": {"USD": [
            {"start": "2024-01-01", "end": "2024-12-31", "val": 1000, "form": "10-K", "filed": "2025-02-01"},
            {"start": "2023-01-01", "end": "2023-12-31", "val": 900, "form": "10-K", "filed": "2025-02-01"},
            {"start": "2024-01-01", "end": "2024-03-31", "val": 250, "form": "10-Q", "filed": "2024-04-20"},
        ]}},
        "OperatingIncomeLoss": {"units": {"USD": [
            {"start": "2024-01-01", "end": "2024-12-31", "val": 250, "form": "10-K", "filed": "2025-02-01"}]}},
        "StockholdersEquity": {"units": {"USD": [
            {"end": "2024-12-31", "val": 500, "form": "10-K", "filed": "2025-02-01"}]}},
        "LongTermDebtNoncurrent": {"units": {"USD": [
            {"end": "2024-12-31", "val": 300, "form": "10-K", "filed": "2025-02-01"}]}},
        "CashAndCashEquivalentsAtCarryingValue": {"units": {"USD": [
            {"end": "2024-12-31", "val": 100, "form": "10-K", "filed": "2025-02-01"}]}},
        "WeightedAverageNumberOfDilutedSharesOutstanding": {"units": {"shares": [
            {"start": "2024-01-01", "end": "2024-12-31", "val": 50, "form": "10-K", "filed": "2025-02-01"}]}},
    }}}
    a = QW.annuals_from_facts(facts)
    y = {r["fy"]: r for r in a}
    assert set(y) == {2023, 2024}                     # the 10-Q quarter is not an annual period
    assert y[2024]["revenue"] == 1000 and y[2024]["net_debt"] == 200
    assert y[2024]["invested_capital"] == 700
    assert y[2024]["roic"] == pytest.approx(250 * 0.79 / 700)
    assert y[2023]["ebit"] is None                    # honest hole, not a fabricated zero


def test_share_counts_are_chain_linked_across_a_stock_split():
    """The AAPL bug. FY2018-20 are reported pre-split in the FY2020 10-K; FY2020-22 are reported
    post-4:1 in the FY2022 10-K. A naive latest-filed-wins series shows the share count RISING
    ~3x and the owner-alignment gate then rejects a company that BOUGHT BACK stock."""
    def ent(fy, val, accn, filed):
        return {"start": f"{fy}-01-01", "end": f"{fy}-12-31", "val": val, "form": "10-K",
                "accn": accn, "filed": filed}
    facts = {"facts": {"us-gaap": {
        "WeightedAverageNumberOfDilutedSharesOutstanding": {"units": {"shares": [
            ent(2018, 1000, "A", "2019-02-01"), ent(2019, 950, "A", "2019-02-01"),
            ent(2019, 950, "B", "2021-02-01"), ent(2020, 900, "B", "2021-02-01"),
            # the split: the next 10-K restates FY2020 at 4x and reports FY2021/22 on that basis
            ent(2020, 3600, "C", "2023-02-01"), ent(2021, 3480, "C", "2023-02-01"),
            ent(2022, 3400, "C", "2023-02-01"),
        ]}}}}}
    ch = QW.chained_shares(facts)
    got = {fy: round(v[0]) for fy, v in ch.items()}
    assert got == {2018: 4000, 2019: 3800, 2020: 3600, 2021: 3480, 2022: 3400}
    # ...and the gate now sees a 15% SHRINK rather than a 240% increase
    a = QW.annuals_from_facts(facts)
    assert a[-1]["dil_sh"] / a[0]["dil_sh"] - 1 == pytest.approx(-0.15)


def test_ebit_falls_back_to_pretax_plus_interest_and_says_so():
    facts = {"facts": {"us-gaap": {
        "Revenues": {"units": {"USD": [
            {"start": "2024-01-01", "end": "2024-12-31", "val": 1000, "form": "10-K", "filed": "2025-02-01"}]}},
        "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest":
            {"units": {"USD": [
                {"start": "2024-01-01", "end": "2024-12-31", "val": 200, "form": "10-K", "filed": "2025-02-01"}]}},
        "InterestExpense": {"units": {"USD": [
            {"start": "2024-01-01", "end": "2024-12-31", "val": 30, "form": "10-K", "filed": "2025-02-01"}]}},
    }}}
    y = QW.annuals_from_facts(facts)[0]
    assert y["ebit"] == 230 and y["ebit_from_pretax"] is True
    g = QW.quality_gate(annuals()[:1] * 0 + [dict(x, ebit_from_pretax=True) for x in annuals()])
    assert any("EBIT-FROM-PRETAX" in f for f in g["flags"])


def test_a_filer_with_no_debt_concept_is_debt_free_not_unknown():
    facts = {"facts": {"us-gaap": {
        "OperatingIncomeLoss": {"units": {"USD": [
            {"start": "2024-01-01", "end": "2024-12-31", "val": 250, "form": "10-K", "filed": "2025-02-01"}]}},
        "StockholdersEquity": {"units": {"USD": [
            {"end": "2024-12-31", "val": 500, "form": "10-K", "filed": "2025-02-01"}]}},
        "CashAndCashEquivalentsAtCarryingValue": {"units": {"USD": [
            {"end": "2024-12-31", "val": 100, "form": "10-K", "filed": "2025-02-01"}]}},
    }}}
    y = QW.annuals_from_facts(facts)[0]
    assert y["debt"] == 0.0 and y["net_debt"] == -100.0


def test_too_few_computable_roic_years_is_degraded_not_a_fail():
    a = annuals(n=11)
    for y in a[:4]:
        y["roic"] = None                  # missing balance-sheet tags in four of the ten years
    g = QW.quality_gate(a)
    assert g["status"] == "DEGRADED"
    assert "computable ROIC years" in g["reasons"][0]


def test_restatement_prefers_the_latest_filing():
    facts = {"facts": {"us-gaap": {"Revenues": {"units": {"USD": [
        {"start": "2024-01-01", "end": "2024-12-31", "val": 1000, "form": "10-K", "filed": "2025-02-01"},
        {"start": "2024-01-01", "end": "2024-12-31", "val": 950, "form": "10-K", "filed": "2026-02-01"},
    ]}}}}}
    assert QW.annuals_from_facts(facts)[0]["revenue"] == 950


def test_multiple_series_drops_loss_years_rather_than_going_negative():
    a = annuals(n=11)
    for y in a:
        y["ebit"], y["net_income"] = -10.0, -10.0
    ms = QW.multiple_series(weekly([100.0] * 300), a)
    assert ms["ev_ebit"] == [] and ms["pe"] == []


def test_combined_percentile_is_the_conservative_max():
    a = annuals()
    res = QW.assess_bands(a, _band_series(200.0, 100.0, 60.0))
    assert res["pct"] == max(res["pct_ev_ebit"], res["pct_pe"])


def test_fire_log_preregistration_header_states_the_n20_gate():
    hdr = json.loads(QW.FIRES.read_text()) if QW.FIRES.exists() else None
    if hdr is None:
        pytest.skip("fire log not yet created (created on first watch run)")
    assert "N>=20" in hdr["_tina_test"]
    assert "SPY" in hdr["_counterfactual"]


def test_debt_free_filer_and_interpolated_debt_gaps():
    inst = {"debt_total": {}, "debt_lt": {}, "debt_cur": {}}
    out, flag = QW._debt_series(inst, [2020, 2021, 2022])
    assert out == {2020: 0.0, 2021: 0.0, 2022: 0.0} and "NO-DEBT-TAG" in flag

    inst = {"debt_total": {}, "debt_cur": {},
            "debt_lt": {2020: (100.0, "2020-12-31", ""), 2023: (400.0, "2023-12-31", "")}}
    out, flag = QW._debt_series(inst, [2019, 2020, 2021, 2022, 2023, 2024])
    # asymmetric by design: nothing before the first reported year (the META bug), flat after
    assert out[2019] == 0.0 and out[2024] == 400.0
    assert out[2021] == pytest.approx(200.0) and out[2022] == pytest.approx(300.0)
    assert "DEBT-PARTIAL" in flag and "2 interior" in flag and "1 year(s) before" in flag


# ================================================================= watch-mode wiring (offline)

def test_active_watch_fires_logs_and_grades_offline(tmp_path, monkeypatch, capsys):
    """End-to-end watch mode with the network stubbed: an active list, cached fundamentals, a
    synthetic price series -> a DETFIRE line, a state entry, and a pre-registered fire row that
    carries the SPY-same-window counterfactual fields."""
    today = dt.date.today()
    a, _ = _standstill_case(end=today)
    wk_cheap = _band_series(200.0, 100.0, 60.0, n=550)
    wk_cheap = [(today - dt.timedelta(weeks=len(wk_cheap) - 1 - i), p)
                for i, (_, p) in enumerate(wk_cheap)]

    monkeypatch.setattr(QW, "ACTIVE", tmp_path / "active.json")
    monkeypatch.setattr(QW, "CANDIDATES", tmp_path / "cands.json")
    monkeypatch.setattr(QW, "STATE", tmp_path / "state.json")
    monkeypatch.setattr(QW, "FACTS", tmp_path / "facts.json")
    monkeypatch.setattr(QW, "PARAMETRIC", tmp_path / "parametric.txt")
    fires_rel = "verticals/generators/data/_test_fires.json"
    monkeypatch.setattr(QW, "FIRES_REL", fires_rel)
    monkeypatch.setattr(QW, "FIRES", QW.ROOT / fires_rel)
    monkeypatch.setattr(QW, "dislocation_hits", lambda **k: {})
    monkeypatch.setattr(QW, "cohort_tags", lambda **k: {"ZZTOP": "narrative:test (MED de-rate)"})

    QW.ACTIVE.write_text(json.dumps({"asof": today.isoformat(), "tickers": ["ZZTOP"]}))
    QW.FACTS.write_text(json.dumps({"asof": today.isoformat(), "names": {
        "ZZTOP": {"cik": 1, "entity": "ZZ Top Industries", "fetched": today.isoformat(),
                  "extract_version": QW.EXTRACT_VERSION, "annuals": a}}}))
    monkeypatch.setattr(QW, "weekly_prices",
                        lambda ts, **k: {"ZZTOP": wk_cheap,
                                         "SPY": [(d, 500.0) for d, _ in wk_cheap]})
    try:
        res = QW.run_watch(enqueue=False)
        out = capsys.readouterr().out
        assert res["active"] is True and len(res["fires"]) == 1
        assert "DETFIRE|quality_wishlist|ZZTOP|" in out
        assert "PROPOSES ONLY" in out and "sleeve cap 8%" in out

        rows = json.loads(QW.FIRES.read_text())["fires"]
        assert len(rows) == 1
        r = rows[0]
        assert r["ticker"] == "ZZTOP" and r["band"] in ("CHEAP", "FAIR")
        assert r["px_at_fire"] > 0 and r["spy_at_fire"] == 500.0
        assert set(r["grade_due"]) == {"90", "180", "365"}
        assert r["outcomes"] == {"90": None, "180": None, "365": None}
        assert r["sleeve"]["aggregate_cap_pct"] == 8.0
        assert r["cohort_tag"] == "narrative:test (MED de-rate)"   # §7 cohort inheritance
        assert "COHORT narrative:test" in out

        st = json.loads(QW.STATE.read_text())
        assert st["ZZTOP"]["fired"] == today.isoformat()
        if st["ZZTOP"].get("band") == "CHEAP":
            assert st["ZZTOP"]["cheap_since"] == today.isoformat()

        # a same-day re-run must not double-fire (quiet period), and must not double-log
        QW.run_watch(enqueue=False)
        assert len(json.loads(QW.FIRES.read_text())["fires"]) == 1
    finally:
        QW.FIRES.unlink(missing_ok=True)
