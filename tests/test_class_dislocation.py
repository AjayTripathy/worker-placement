"""Pipeline-2 detector tests: the three gates, beta-bleed suppression, event shape."""
import pytest

from desk.class_dislocation import FIRE_DD, cohort_stats, load_cohorts, scan


def _stats(dds, spy_dd=-0.02):
    """Synthetic gw stats: hi52=100, px = 100*(1+dd)."""
    out = {f"T{i}": {"px": 100 * (1 + d), "hi52": 100.0} for i, d in enumerate(dds)}
    out["SPY"] = {"px": 100 * (1 + spy_dd), "hi52": 100.0}
    return out


def _cohort(n):
    return {"narrative:test": [f"T{i}" for i in range(n)]}


def test_indiscriminate_class_derate_fires():
    dds = [-0.30, -0.32, -0.28, -0.35, -0.29, -0.31, -0.33, -0.30]   # tight, deep, vs flat SPY
    st = cohort_stats(dds, spy_dd=-0.02)
    assert st["fires"] is True
    events = scan(_stats(dds), _cohort(8))
    assert len(events) == 1
    e = events[0]
    assert e["narrative_anchor"] == "UNEXPLAINED"        # never backfilled by the detector
    assert e["cohort_tag"] == "class_dislocation" and e["grade_due"]
    assert e["members_by_dd"][0][1] <= e["members_by_dd"][-1][1]     # worst first


def test_beta_selloff_suppressed():
    # same drawdowns but the MARKET is down 28% — residual gate must hold (beta-bleed guard)
    dds = [-0.30, -0.32, -0.28, -0.35, -0.29, -0.31, -0.33, -0.30]
    st = cohort_stats(dds, spy_dd=-0.28)
    assert st["fires"] is False
    assert scan(_stats(dds, spy_dd=-0.28), _cohort(8)) == []


def test_high_dispersion_not_a_class_event():
    # deep median but WIDE dispersion = stock-picking, not an indiscriminate narrative
    dds = [-0.60, -0.05, -0.55, -0.02, -0.50, -0.08, -0.45, -0.30]
    st = cohort_stats(dds, spy_dd=-0.02)
    assert st["fires"] is False


def test_shallow_derate_not_fired():
    dds = [-0.10, -0.12, -0.08, -0.15, -0.09, -0.11, -0.13, -0.10]
    assert cohort_stats(dds, spy_dd=-0.02)["fires"] is False
    assert FIRE_DD == -0.25


def test_missing_spy_refuses_to_scan():
    stats = _stats([-0.3] * 8)
    del stats["SPY"]
    with pytest.raises(RuntimeError):
        scan(stats, _cohort(8))


def test_small_cohorts_skipped():
    dds = [-0.30] * 5                                    # under MIN_MEMBERS
    assert scan(_stats(dds), _cohort(5)) == []


def test_load_cohorts_sector_banding():
    uni = ([{"ticker": f"A{i}", "sector": "Tech", "mcap": 5e9} for i in range(9)]
           + [{"ticker": f"B{i}", "sector": "Tech", "mcap": 50e6} for i in range(9)])  # sub-floor
    cs = load_cohorts(uni)
    assert "sector:Tech|mid" in cs and len(cs["sector:Tech|mid"]) == 9
    assert not any("small" in k for k in cs if k.startswith("sector:Tech"))


# ---------- discovery leg ----------
def _dq(px, hi, d50, d200):
    return {"regularMarketPrice": px, "fiftyTwoWeekHigh": hi,
            "fiftyDayAverage": d50, "twoHundredDayAverage": d200}


def test_discovery_clusters_cross_sector_shapes():
    from desk.class_dislocation import discover_clusters
    # six names, three sectors, same shape (-40% dd, flat vs 50dma, -20% vs 200dma)
    quotes = {f"N{i}": _dq(60, 100, 60, 75) for i in range(6)}
    # plus shallow names and a deep-but-lone-sector cluster
    quotes.update({f"S{i}": _dq(95, 100, 94, 96) for i in range(6)})       # -5%: filtered
    meta = {f"N{i}": {"sector": ["Tech", "Industrials", "Health"][i % 3], "mcap": 1e9} for i in range(6)}
    meta.update({f"S{i}": {"sector": "Tech", "mcap": 1e9} for i in range(6)})
    out = discover_clusters(quotes, meta)
    assert len(out) == 1 and out[0]["n"] == 6 and len(out[0]["sectors"]) == 3
    assert out[0]["status"].startswith("UNNAMED")


def test_discovery_rejects_single_sector_cluster():
    from desk.class_dislocation import discover_clusters
    quotes = {f"N{i}": _dq(60, 100, 60, 75) for i in range(8)}
    meta = {f"N{i}": {"sector": "Tech", "mcap": 1e9} for i in range(8)}    # one sector = not a narrative
    assert discover_clusters(quotes, meta) == []


def test_discovery_smallcaps_cluster_but_need_liquid_anchors():
    from desk.class_dislocation import discover_clusters, shape_vector
    assert shape_vector(_dq(90, 100, 89, 92)) is None                      # -10% > threshold
    quotes = {f"N{i}": _dq(60, 100, 60, 75) for i in range(6)}
    # microcap-ONLY cluster: scans, clusters, but never QUALIFIES (promotion wreckage guard)
    meta = {f"N{i}": {"sector": ["A", "B", "C"][i % 3], "mcap": 60e6} for i in range(6)}
    assert discover_clusters(quotes, meta) == []
    # same cluster with 3 liquid anchors QUALIFIES — smallcaps ride along as members
    for i in range(3):
        meta[f"N{i}"]["mcap"] = 1e9
    out = discover_clusters(quotes, meta)
    assert len(out) == 1 and out[0]["n"] == 6                              # all six, smallcaps included


def test_discovery_linkage_joins_adjacent_buckets():
    from desk.class_dislocation import discover_clusters
    # members spread across NEIGHBORING depth buckets (-28..-42%) must form ONE cluster —
    # exact-bucket matching fragmented the real saaspocalypse into 13 pieces (the caught bug)
    quotes = {f"N{i}": _dq(100 - 28 - 2 * i, 100, 100 - 28 - 2 * i + 1, 90) for i in range(8)}
    meta = {f"N{i}": {"sector": ["Tech", "Ind", "Health"][i % 3], "mcap": 1e9} for i in range(8)}
    out = discover_clusters(quotes, meta)
    assert len(out) == 1 and out[0]["n"] == 8


def test_discovery_subsector_excess_qualifies():
    from desk.class_dislocation import discover_clusters
    # single-sector cluster deep below a HEALTHY sector baseline = a narrative inside a sector
    quotes = {f"D{i}": _dq(64 - i, 100, 64 - i + 2, 80) for i in range(6)}
    quotes.update({f"H{i}": _dq(95, 100, 94, 92) for i in range(10)})       # healthy base
    meta = {t: {"sector": "Tech", "mcap": 1e9} for t in quotes}
    out = discover_clusters(quotes, meta)
    assert len(out) == 1 and out[0]["qualified_by"] == "sub_sector_excess"
    assert all(t.startswith("D") for t in out[0]["members"])


# ---------- velocity leg ----------
def test_velocity_1d_fires_without_history(tmp_path, monkeypatch):
    import desk.class_dislocation as CD
    monkeypatch.setattr(CD, "VEL_DIR", tmp_path / "snaps")
    uni = [{"ticker": "PRNT", "mcap": 5e9, "sector": "Tech", "lastsale": 80.0, "pctchange": -0.19},
           {"ticker": "OK", "mcap": 5e9, "sector": "Tech", "lastsale": 100.0, "pctchange": -0.02},
           {"ticker": "TINY", "mcap": 50e6, "sector": "Tech", "lastsale": 10.0, "pctchange": -0.30},
           {"ticker": "DUST", "mcap": 5e6, "sector": "Tech", "lastsale": 1.0, "pctchange": -0.40}]
    hits = CD.velocity_scan(uni, spy_px=500.0)
    assert [h["ticker"] for h in hits] == ["TINY", "PRNT"]  # $30M+ scans (TINY in); sub-$30M dust floored
    assert any("1d -19%" in t for t in hits[-1]["triggers"])


def test_velocity_week_excess_from_snapshots(tmp_path, monkeypatch):
    import desk.class_dislocation as CD
    import json as _j
    snaps = tmp_path / "snaps"; snaps.mkdir()
    monkeypatch.setattr(CD, "VEL_DIR", snaps)
    # six prior snapshots: name at 100, SPY flat at 500
    for i in range(6):
        (snaps / f"2026-07-{20+i:02d}.json").write_text(_j.dumps({"BLEED": 100.0, "SPY": 500.0}))
    uni = [{"ticker": "BLEED", "mcap": 5e9, "sector": "X", "lastsale": 80.0, "pctchange": -0.03}]
    hits = CD.velocity_scan(uni, spy_px=500.0)              # -20% over the week, SPY flat, no big day
    assert hits and any("5d-excess" in t for t in hits[0]["triggers"])


def test_velocity_spy_excess_suppresses_market_moves(tmp_path, monkeypatch):
    import desk.class_dislocation as CD
    import json as _j
    snaps = tmp_path / "snaps"; snaps.mkdir()
    monkeypatch.setattr(CD, "VEL_DIR", snaps)
    for i in range(6):   # market itself fell 20% — the name just tracked it
        (snaps / f"2026-07-{20+i:02d}.json").write_text(_j.dumps({"BETA": 100.0, "SPY": 500.0}))
    uni = [{"ticker": "BETA", "mcap": 5e9, "sector": "X", "lastsale": 80.0, "pctchange": -0.03}]
    hits = CD.velocity_scan(uni, spy_px=400.0)
    assert hits == []

def test_blob_autopsy_extracts_industry_pocket_from_rejected_component():
    """Breadth-gate rejection must not discard members (DISC-BLOB-MISS-FLUT): an industry
    pocket inside the rejected blob with real excess-vs-sector and liquid anchors is emitted."""
    from desk.class_dislocation import discover_clusters
    quotes = {f"M{i}": _dq(60, 100, 60, 75) for i in range(48)}       # dd -40%, bucket -4
    quotes.update({f"B{i}": _dq(50, 100, 50, 62.5) for i in range(2)})  # dd -50%, bridge bucket -5
    quotes.update({f"O{i}": _dq(40, 100, 40, 50) for i in range(6)})    # dd -60%, bucket -6
    meta = {f"M{i}": {"sector": "Gambling", "industry": "Casinos", "mcap": 1e9} for i in range(48)}
    meta.update({f"B{i}": {"sector": "Gambling", "industry": "Casinos", "mcap": 1e9} for i in range(2)})
    meta.update({f"O{i}": {"sector": "Gambling", "industry": "OSB", "mcap": 1e9} for i in range(6)})
    out = discover_clusters(quotes, meta)
    # the 56-name chained component is 100% of the shaped tape -> rejected as ONE cohort,
    # but the OSB pocket (median -60 vs sector median -40 = -20pp excess) must surface
    assert len(out) == 1
    assert out[0]["qualified_by"] == "blob_autopsy_industry_excess"
    assert out[0]["industry"] == "OSB" and out[0]["n"] == 6
    assert out[0]["shape"]["median_dd"] == -0.6
    # the Casinos pocket (zero excess vs its own sector) must NOT ride along
    assert all(o["industry"] == "OSB" for o in out)
