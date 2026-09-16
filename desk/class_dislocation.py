"""class_dislocation — pipeline 2's detector (PIPELINE_ARCHITECTURE §P2; PRD R2.x).

Detects CLASS-level de-rates: a whole cohort marked down together on one narrative
(saaspocalypse, muni-headline pattern) — the setup where dispersion INSIDE the class is
the alpha and refutability triage decides who's damage-absent. Complements the single-name
daily layers (broken_print_radar = whole-tape breaks; dislocation_sweep = known names).

Signal (one Gateway stats sweep, no history pulls):
  member drawdown  = px / 52w-high − 1        (gw_quotes.bulk_stats, tick 165)
  cohort fires when: median_dd <= FIRE_DD  AND  IQR <= FIRE_IQR (LOW dispersion =
  indiscriminate selling)  AND  median_dd − SPY_dd <= FIRE_RESID (the beta-bleed guard:
  a market selloff is not a class dislocation).

Cohorts: (sector × mcap-band) from the Nasdaq screener + CURATED narrative cohorts in
knowledge_graph/cohorts.json (versioned data — add one whenever a narrative names a class).

Events: desk/data/class_dislocation_events.json (S1 store, merge by cohort+window-month).
narrative_anchor starts UNEXPLAINED — never backfilled by the detector (hindsight-bias
rule R2.2); the triage step attaches the dated anchor or the flag stands. Refutability
triage + courts remain the conveyor/session lane. Every event carries grade_due (+90d,
cohort tag class_dislocation) — the detector earns its keep empirically or dies (MAUDE rule).

  python3 -m desk.class_dislocation            # daily after US close (registry)
  python3 -m desk.class_dislocation --dry-run  # compute, print, write nothing
"""
from __future__ import annotations

import argparse
import datetime
import json
import statistics
import sys
from pathlib import Path

from desk.store import Store

ROOT = Path(__file__).resolve().parents[1]
EVENTS = Store("desk/data/class_dislocation_events.json", list_path="events",
               key=lambda e: e["event_id"])
COHORT_FILE = ROOT / "knowledge_graph" / "cohorts.json"

FIRE_DD = -0.25
FIRE_IQR = 0.18
FIRE_RESID = -0.15
MIN_MEMBERS = 8
MIN_MCAP = 250e6          # cohort stats on liquid members only — microcap noise is not narrative


def cohort_stats(dds: list[float], spy_dd: float) -> dict:
    """Pure: the three gates from a list of member drawdowns (negative numbers)."""
    med = statistics.median(dds)
    qs = statistics.quantiles(dds, n=4) if len(dds) >= 4 else [min(dds), med, max(dds)]
    iqr = qs[2] - qs[0]
    resid = med - spy_dd
    return {"n": len(dds), "median_dd": round(med, 4), "iqr": round(iqr, 4),
            "resid": round(resid, 4),
            "fires": med <= FIRE_DD and iqr <= FIRE_IQR and resid <= FIRE_RESID}


def load_cohorts(universe: list[dict]) -> dict[str, list[str]]:
    """{cohort_name: [tickers]} — sector×band from the screener + curated narrative file."""
    out: dict[str, list[str]] = {}
    for u in universe:
        if not u.get("mcap") or u["mcap"] < MIN_MCAP or not u.get("sector"):
            continue
        band = "large" if u["mcap"] > 10e9 else "mid" if u["mcap"] > 2e9 else "small"
        out.setdefault(f"sector:{u['sector']}|{band}", []).append(u["ticker"])
    try:
        curated = json.loads(COHORT_FILE.read_text())
        for name, spec in curated.get("cohorts", {}).items():
            out[f"narrative:{name}"] = spec["members"]
    except Exception:
        pass
    return {k: v for k, v in out.items() if len(v) >= MIN_MEMBERS}


def scan(stats: dict, cohorts: dict[str, list[str]]) -> list[dict]:
    spy = stats.get("SPY")
    if not spy or not spy.get("hi52"):
        raise RuntimeError("SPY stats missing — residual gate impossible; refusing to scan "
                           "(a detector without its beta guard mistakes selloffs for dislocations)")
    spy_dd = spy["px"] / spy["hi52"] - 1
    month = datetime.date.today().strftime("%Y-%m")
    fired = []
    for name, members in cohorts.items():
        dds = []
        for t in members:
            q = stats.get(t)
            if q and q.get("hi52"):
                dds.append(q["px"] / q["hi52"] - 1)
        if len(dds) < MIN_MEMBERS:
            continue
        st = cohort_stats(dds, spy_dd)
        if st["fires"]:
            ranked = sorted(((t, round(stats[t]["px"] / stats[t]["hi52"] - 1, 3))
                             for t in members if stats.get(t, {}).get("hi52")),
                            key=lambda x: x[1])
            fired.append({
                "event_id": f"{name}|{month}",
                "cohort": name, "detected": datetime.date.today().isoformat(),
                "spy_dd": round(spy_dd, 4), **{k: st[k] for k in ("n", "median_dd", "iqr", "resid")},
                "members_by_dd": ranked[:20],
                "narrative_anchor": "UNEXPLAINED",     # triage attaches a DATED anchor or this stands
                "triaged_utc": None,
                "grade_due": (datetime.date.today() + datetime.timedelta(days=90)).isoformat(),
                "cohort_tag": "class_dislocation",
            })
    return fired


# ---------------- DISCOVERY LEG (added 2026-08-06 after the DDOG/GTLB challenge) ----------------
# The curated+sector cohorts are CONFIRMATORY — they can only re-find what someone named.
# Discovery clusters the tape bottom-up on drawdown SHAPE (how deep × how recent), keeps only
# clusters that CROSS sector lines (a narrative's signature — sector selling is already covered
# by the sector cohorts), and emits candidates for NAMING by a session/triage — never auto-named
# (R2.2: anchors are attached by evidence, not by the detector that would benefit).

DISC_MIN_DD = -0.20          # materially drawn-down names only
DISC_MIN_MCAP = 50e6         # scan the WHOLE tape (user rule: floors tier, never exclude)
DISC_ANCHORS = (3, 250e6)    # ...but a QUALIFYING cluster needs >=3 members >=$250M (liquid anchors — microcap-only clusters are promotion wreckage, not narrative)
DISC_MIN_MEMBERS = 6
DISC_MIN_SECTORS = 3         # fewer = probably just a sector, already covered


def shape_vector(q: dict) -> tuple | None:
    """(dd52, vs50dma, vs200dma) rounded into buckets — names sold on one narrative share
    depth AND recency; a single scalar would cluster every -30% name together."""
    px, hi = q.get("regularMarketPrice"), q.get("fiftyTwoWeekHigh")
    d50, d200 = q.get("fiftyDayAverage"), q.get("twoHundredDayAverage")
    if not (px and hi and d50 and d200):
        return None
    dd52 = px / hi - 1
    if dd52 > DISC_MIN_DD:
        return None
    # INTEGER grid indices — float bucket values broke neighbor equality (the blind
    # self-test still failed until keys became ints)
    return (round(dd52 / 0.10), round((px / d50 - 1) / 0.05), round((px / d200 - 1) / 0.10))


def discover_clusters(quotes: dict, meta: dict, persist_blob: bool = False) -> list[dict]:
    """v2 (the null-was-an-artifact fix, 2026-08-06): single-linkage over NEIGHBORING shape
    buckets — exact-bucket matching fragmented the known saaspocalypse into 13 pieces
    (largest=2), a fatal recall failure caught by the blind self-test. A cluster qualifies if
    EITHER it crosses >=DISC_MIN_SECTORS sectors, OR it is a SUB-SECTOR class: concentrated
    in 1-2 sectors but with median drawdown >=15pp worse than its own sector's median (the
    saaspocalypse is all-Technology; the cross-sector gate alone would reject the one true
    positive we possess). Names missing dma fields are COUNTED as uncovered, never dropped
    silently."""
    buckets: dict[tuple, list[str]] = {}
    sector_dds: dict[str, list[float]] = {}
    uncovered = 0
    for t, q in quotes.items():
        m = meta.get(t) or {}
        if not q or (m.get("mcap") or 0) < DISC_MIN_MCAP:
            continue
        px, hi = q.get("regularMarketPrice"), q.get("fiftyTwoWeekHigh")
        if px and hi and m.get("sector"):
            sector_dds.setdefault(m["sector"], []).append(px / hi - 1)
        v = shape_vector(q)
        if v:
            buckets.setdefault(v, []).append(t)
        elif px and hi and px / hi - 1 <= DISC_MIN_DD:
            uncovered += 1                      # deep name we couldn't shape — counted
    # DBSCAN-flavored union-find (v3 — the 1,349-name percolation fix): CORE buckets hold
    # >=2 names; only cores LINK (via face-neighbors, not the full 26-cell shell); singleton
    # buckets may ATTACH to one adjacent core but never bridge two. Single-linkage over all
    # neighbors chained a third of the tape into one blob — breadth regime, not a narrative.
    keys = list(buckets)
    cores = {k for k in keys if len(buckets[k]) >= 2}
    parent = {k: k for k in keys}

    def find(k):
        while parent[k] != k:
            parent[k] = parent[parent[k]]
            k = parent[k]
        return k

    # full 26-shell linkage but CORE-TO-CORE only (narratives step diagonally: depth and
    # trend deteriorate together); singletons attach to one core, never bridge
    SHELL = [(a, b, c) for a in (-1, 0, 1) for b in (-1, 0, 1) for c in (-1, 0, 1)
             if (a, b, c) != (0, 0, 0)]
    for k in cores:
        for d in SHELL:
            nb = (k[0] + d[0], k[1] + d[1], k[2] + d[2])
            if nb in cores:
                ra, rb = find(k), find(nb)
                if ra != rb:
                    parent[ra] = rb
    for k in keys:
        if k in cores:
            continue
        for d in SHELL:                       # singleton attaches to the FIRST adjacent core
            nb = (k[0] + d[0], k[1] + d[1], k[2] + d[2])
            if nb in cores:
                parent[find(k)] = find(nb)
                break
    comps: dict[tuple, list[str]] = {}
    for k in keys:
        comps.setdefault(find(k), []).extend(buckets[k])
    total_shaped = sum(len(v) for v in buckets.values())
    sector_median = {s: statistics.median(v) for s, v in sector_dds.items() if len(v) >= 5}
    out = []
    for root, members in sorted(comps.items(), key=lambda kv: -len(kv[1])):
        if len(members) < DISC_MIN_MEMBERS:
            continue
        if total_shaped >= 50 and len(members) > 0.15 * total_shaped:
            print(f"  [discovery] REJECTED {len(members)}-name component "
                  f"({len(members)/total_shaped:.0%} of the drawn-down tape) — breadth regime, "
                  f"not a narrative; a narrative is a minority of the tape")
            # BLOB AUTOPSY (2026-08-07, principal: "why not run them all down?"): rejecting the
            # component as ONE cohort must not discard its members — real sub-classes drown in
            # breadth (measured cost: FLUT/SRAD/DKNG, defect DISC-BLOB-MISS-FLUT). Industry
            # grouping is deterministic and free; each pocket faces the SAME excess-vs-sector
            # and liquid-anchor gates as any cluster. Cross-industry narratives hiding in the
            # blob remain v4's job (return-series co-movement).
            if persist_blob:
                # persist the rejected component so blob_sweep can drip it into the Opus
                # triage conveyor (principal 2026-08-07: the blob was never written anywhere
                # a triage could pick it up — rejection was a silent discard)
                (ROOT / "desk" / "data" / "discovery_blob.json").write_text(json.dumps({
                    "date": datetime.date.today().isoformat(), "n": len(members),
                    "sector_median_dd": {s: round(v, 3) for s, v in sector_median.items()},
                    "members": [{"ticker": t,
                                 "dd52": round(quotes[t]["regularMarketPrice"] / quotes[t]["fiftyTwoWeekHigh"] - 1, 3),
                                 "sector": meta.get(t, {}).get("sector"),
                                 "industry": meta.get(t, {}).get("industry"),
                                 "mcap": meta.get(t, {}).get("mcap")} for t in members]}, indent=1))
            by_ind: dict[str, list[str]] = {}
            for t in members:
                ind = meta.get(t, {}).get("industry")
                if ind:
                    by_ind.setdefault(ind, []).append(t)
            for ind, its in sorted(by_ind.items(), key=lambda kv: -len(kv[1])):
                if len(its) < DISC_MIN_MEMBERS:
                    continue
                if sum(1 for t in its if (meta.get(t, {}).get("mcap") or 0) >= DISC_ANCHORS[1]) < DISC_ANCHORS[0]:
                    continue
                dds_i = [quotes[t]["regularMarketPrice"] / quotes[t]["fiftyTwoWeekHigh"] - 1 for t in its]
                med_i = statistics.median(dds_i)
                secs_i = {meta.get(t, {}).get("sector") for t in its} - {None}
                base_i = statistics.median([sector_median.get(s, 0.0) for s in secs_i]) if secs_i else 0.0
                if (med_i - base_i) <= -0.15:
                    out.append({"shape": {"median_dd": round(med_i, 3)},
                                "excess_vs_sector": round(med_i - base_i, 3),
                                "members": sorted(its), "n": len(its),
                                "sectors": sorted(secs_i), "industry": ind,
                                "qualified_by": "blob_autopsy_industry_excess",
                                "uncovered_deep_names": uncovered,
                                "status": "UNNAMED — session names the narrative or discards (R2.2)"})
            # cap autopsy emissions to the deepest-excess pockets: the 2026-08-07 e2e produced
            # 49 pockets (204-name pharma, 95-name crypto-finance...) — real industry derates,
            # but as NAMING candidates that floods the session; the blob drip covers members
            # individually regardless. KNOWN LIMIT (e2e-falsified): screener labels split the
            # OSB trio across two sectors — cross-label narratives need v4 co-movement.
            autop = [o for o in out if o["qualified_by"] == "blob_autopsy_industry_excess"]
            if len(autop) > 12:
                keep = set(id(o) for o in sorted(autop, key=lambda o: o["excess_vs_sector"])[:12])
                out = [o for o in out if o["qualified_by"] != "blob_autopsy_industry_excess" or id(o) in keep]
            continue
        sectors = {meta.get(t, {}).get("sector") for t in members} - {None}
        dds = [quotes[t]["regularMarketPrice"] / quotes[t]["fiftyTwoWeekHigh"] - 1 for t in members]
        med = statistics.median(dds)
        anchors = sum(1 for t in members if (meta.get(t, {}).get("mcap") or 0) >= DISC_ANCHORS[1])
        if anchors < DISC_ANCHORS[0]:
            continue                       # no liquid anchors = not a tradeable narrative
        cross_sector = len(sectors) >= DISC_MIN_SECTORS
        subsector = False
        if not cross_sector:
            base = statistics.median([sector_median.get(s, 0.0) for s in sectors]) if sectors else 0.0
            subsector = (med - base) <= -0.15
        if cross_sector or subsector:
            out.append({"shape": {"median_dd": round(med, 3)},
                        "members": sorted(members), "n": len(members),
                        "sectors": sorted(sectors),
                        "qualified_by": "cross_sector" if cross_sector else "sub_sector_excess",
                        "uncovered_deep_names": uncovered,
                        "status": "UNNAMED — session names the narrative or discards (R2.2)"})
    return out


# ---------------- VELOCITY LEG (2026-08-06, user challenge: "-20% isn't regime-ordinary —
# look at everything that drops that much in a day or week") ----------------
# Layer gap it closes: broken_print_radar = single-day whole-tape but runs 01:30 (a print-day
# break like DDOG -19% is invisible until the NEXT morning); dislocation_sweep = week-scale but
# known-universe only. This leg: whole tape, 1d from the screener's own pctchange (zero extra
# fetches, same-run coverage), 5d/21d from accumulated daily px snapshots (the premarket cron
# builds the history for free).

VEL_DIR = ROOT / "desk" / "data" / "px_snapshots"
VEL_1D = -0.15
VEL_5D = -0.15          # excess vs SPY
VEL_21D = -0.25         # excess vs SPY
VEL_MIN_MCAP = 30e6          # orphan-screen floor: scan everything; ROUTING tiers by size


def snapshot_tape(uni: list[dict], spy_px: float | None):
    VEL_DIR.mkdir(parents=True, exist_ok=True)
    snap = {u["ticker"]: u.get("lastsale") for u in uni if u.get("lastsale")}
    if spy_px:
        snap["SPY"] = spy_px
    (VEL_DIR / f"{datetime.date.today().isoformat()}.json").write_text(json.dumps(snap))
    return snap


def _load_snap_ago(trading_days: int) -> dict | None:
    files = sorted(VEL_DIR.glob("*.json"))
    if len(files) > trading_days:
        return json.loads(files[-1 - trading_days].read_text())
    return None


def velocity_scan(uni: list[dict], spy_px: float | None) -> list[dict]:
    today = snapshot_tape(uni, spy_px)
    hits = []
    s5, s21 = _load_snap_ago(5), _load_snap_ago(21)
    spy5 = (spy_px / s5["SPY"] - 1) if (spy_px and s5 and s5.get("SPY")) else 0.0
    spy21 = (spy_px / s21["SPY"] - 1) if (spy_px and s21 and s21.get("SPY")) else 0.0
    for u in uni:
        if (u.get("mcap") or 0) < VEL_MIN_MCAP or not u.get("lastsale"):
            continue
        t, px = u["ticker"], u["lastsale"]
        d1 = u.get("pctchange")
        r5 = (px / s5[t] - 1 - spy5) if (s5 and s5.get(t)) else None
        r21 = (px / s21[t] - 1 - spy21) if (s21 and s21.get(t)) else None
        trig = []
        if d1 is not None and d1 <= VEL_1D:
            trig.append(f"1d {d1:.0%}")
        if r5 is not None and r5 <= VEL_5D:
            trig.append(f"5d-excess {r5:.0%}")
        if r21 is not None and r21 <= VEL_21D:
            trig.append(f"21d-excess {r21:.0%}")
        if trig:
            hits.append({"ticker": t, "mcap": u["mcap"], "sector": u.get("sector"),
                         "d1": d1, "excess_5d": r5, "excess_21d": r21,
                         "triggers": trig, "date": datetime.date.today().isoformat()})
    return sorted(hits, key=lambda h: (h["d1"] if h["d1"] is not None else 0))


def run(dry_run=False):
    sys.path.insert(0, str(ROOT / "verticals" / "deep_value"))
    from universe import _get, NASDAQ_URL, NASDAQ_HDRS
    raw = _get(NASDAQ_URL, NASDAQ_HDRS)["data"]["rows"]
    uni = []
    for r in raw:
        t = r["symbol"].strip()
        if "^" in t or "/" in t or " " in t:
            continue
        try:
            mc = float(str(r.get("marketCap", "")).replace("$", "").replace(",", "") or 0)
        except ValueError:
            mc = 0
        def _num(x):
            try:
                return float(str(x).replace("$", "").replace(",", "").replace("%", ""))
            except (ValueError, TypeError):
                return None
        uni.append({"ticker": t, "sector": r.get("sector"), "industry": r.get("industry"), "mcap": mc,
                    "lastsale": _num(r.get("lastsale")),
                    "pctchange": (_num(r.get("pctchange")) or 0) / 100 if r.get("pctchange") else None})
    cohorts = load_cohorts(uni)
    members = sorted({t for v in cohorts.values() for t in v} | {"SPY"})
    print(f"class_dislocation: {len(cohorts)} cohorts, {len(members)} members to sweep")
    from desk.gw_quotes import bulk_stats
    stats = bulk_stats(members)
    if "SPY" not in stats or not stats.get("SPY", {}).get("hi52"):
        # the beta baseline must exist, but ANY good source satisfies it — a missing ETF in
        # the gateway sweep must not kill the whole scan (2026-08-06: SPY hole aborted
        # velocity+discovery behind the guard)
        try:
            import sys as _s2
            _s2.path.insert(0, str(ROOT / "verticals" / "deep_value" / "global"))
            from screen_korea import _yahoo_quotes as _yq
            q = (_yq(["SPY"]) or {}).get("SPY") or {}
            if q.get("regularMarketPrice") and q.get("fiftyTwoWeekHigh"):
                stats["SPY"] = {"px": q["regularMarketPrice"], "hi52": q["fiftyTwoWeekHigh"]}
                print("SPY baseline recovered via yahoo (gateway sweep missed it)")
        except Exception:
            pass
    if len(stats) < 0.6 * len(members):
        # LOUD fallback, never silent: gateway wedged (Error-1100 class) -> yahoo v7 carries
        # px + fiftyTwoWeekHigh in the same bulk call. Basis recorded in the event rows.
        print(f"gateway returned {len(stats)}/{len(members)} — FALLING BACK to yahoo v7 (loud)")
        import sys as _s
        _s.path.insert(0, str(ROOT / "verticals" / "deep_value" / "global"))
        from screen_korea import _yahoo_quotes
        yq = _yahoo_quotes(members)
        stats = {t: {"px": q["regularMarketPrice"], "hi52": q.get("fiftyTwoWeekHigh")}
                 for t, q in yq.items()
                 if q and q.get("regularMarketPrice") and q.get("fiftyTwoWeekHigh")}
    if len(stats) < 0.6 * len(members):
        print(f"FAIL-LOUD: only {len(stats)}/{len(members)} priced on BOTH transports — "
              f"partial-tape scan would misfire; aborting")
        return []
    fired = scan(stats, cohorts)
    print(f"swept {len(stats)} | fired: {len(fired)}")
    for e in fired:
        print(f"  {e['cohort']}: median {e['median_dd']:.0%} (n={e['n']}, iqr {e['iqr']:.0%}, "
              f"resid {e['resid']:.0%}) worst: {e['members_by_dd'][:5]}")
    if fired and not dry_run:
        counts = EVENTS.upsert(fired, generated_by="class_dislocation")
        print(f"events store: {counts}")
        # R2.4: members route to RESEARCH automatically — refutability stage on the conveyor
        # (allow_ledger: a class de-rate makes KNOWN names re-triageable)
        try:
            from desk.court_queue import enqueue_candidates
            for e in fired:
                members = [{"ticker": t, "cohort": e["cohort"], "member_dd": dd,
                            "event_id": e["event_id"]} for t, dd in e["members_by_dd"]]
                c = enqueue_candidates(members, source=f"class_dislocation/{e['event_id']}",
                                       stage="REFUTABILITY", allow_ledger=True)
                print(f"  {e['cohort']}: {c['added']} members -> REFUTABILITY queue")
        except Exception as ex:
            print(f"  conveyor enqueue failed (event store unaffected): {type(ex).__name__}: {ex}")
    # ---- velocity leg: whole-tape day/week breaks (the DDOG-class blind window) ----
    try:
        spy_px = (stats.get("SPY") or {}).get("px")
        vhits = velocity_scan(uni, spy_px)
        (ROOT / "desk" / "data" / "velocity_dislocations.json").write_text(json.dumps(
            {"asof": datetime.date.today().isoformat(), "hits": vhits}, indent=1))
        print(f"velocity: {len(vhits)} names past the day/week thresholds "
              f"(snapshots {len(list(VEL_DIR.glob('*.json')))} days deep — 5d/21d live once history accrues)")
        for h in vhits[:10]:
            print(f"  {h['ticker']:6s} mc${h['mcap']/1e6:7.0f}M {h['sector'] or '?':22s} {', '.join(h['triggers'])}")
        if vhits and not dry_run:
            from desk.court_queue import enqueue_candidates
            top = [h for h in vhits if h["mcap"] >= 1e9][:8]
            c = enqueue_candidates([{**h, "context": "velocity dislocation — cause-check FIRST "
                                     "(print? news? beta?), then refutability"} for h in top],
                                    source=f"velocity_dislocation/{datetime.date.today().isoformat()}",
                                    stage="REFUTABILITY", allow_ledger=True)
            print(f"  -> {c['added']} enqueued for cause-check/triage")
    except Exception as ex:
        print(f"velocity leg failed (other legs unaffected): {type(ex).__name__}: {ex}")
    # ---- discovery leg: full drawn-down tape, not just known cohorts ----
    try:
        import sys as _s
        _s.path.insert(0, str(ROOT / "verticals" / "deep_value" / "global"))
        from screen_korea import _yahoo_quotes
        big = [u["ticker"] for u in uni if (u.get("mcap") or 0) >= DISC_MIN_MCAP]
        meta = {u["ticker"]: u for u in uni}
        dq = _yahoo_quotes(big)
        cands = discover_clusters(dq, meta, persist_blob=not dry_run)
        known = {t for v in cohorts.values() for t in v}
        for c in cands:
            c["novel_members"] = [t for t in c["members"] if t not in known]
        cands = [c for c in cands if len(c["novel_members"]) >= 3]   # news, not echoes
        if cands and not dry_run:
            (ROOT / "knowledge_graph" / "cohort_candidates.json").write_text(
                json.dumps({"asof": datetime.date.today().isoformat(), "candidates": cands},
                           indent=1))
        print(f"discovery: {len(cands)} unnamed cross-sector clusters "
              f"-> knowledge_graph/cohort_candidates.json (session names or discards)")
        for c in cands[:5]:
            print(f"  median {c['shape']['median_dd']:.0%} ({c['qualified_by']}): n={c['n']} across "
                  f"{len(c['sectors'])} sectors; novel: {c['novel_members'][:8]}")
    except Exception as ex:
        print(f"discovery leg failed (confirmatory scan unaffected): {type(ex).__name__}: {ex}")
    # ---- blob drip: ranked slice of the breadth-rejected component -> Opus triage ----
    if not dry_run:
        try:
            from desk.blob_sweep import sweep
            print(f"blob_sweep: {sweep()}")
        except Exception as ex:
            print(f"blob_sweep failed (detector legs unaffected): {type(ex).__name__}: {ex}")
    return fired


if __name__ == "__main__":
    run(dry_run="--dry-run" in sys.argv)
