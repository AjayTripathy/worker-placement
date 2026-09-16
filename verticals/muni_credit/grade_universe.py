"""grade_universe.py — run the full underwriting framework across the whole QUALIFIED universe and grade.

Universe = the standing want-list (every name that already passed the insulated-pledge + tax-exempt +
liquidity gates) UNION the live book. Each name is graded by all 11 screens (base fire/EQ/AI/cert +
extended flood/sgma/structure/av-conc/fiscal/water/litigation), then consolidated into DILIGENCE_MASTER.

It is TIERED + RESUMABLE + THROTTLED because the extended screens are network-bound (EMMA OS fetch,
EMMA security-details, USGS, CDE, RECAP/SEC) and EMMA rate-limits (403) on heavy passes:
  TIER 1 (cheap-ish, ALL names): base + flood + sgma + structure(call-risk). Fast first pass -> a
          COMPLETE grade of the universe in one sitting (the par-call / hazard / concentration-free view).
  TIER 2 (expensive, SURVIVORS only): av-concentration(OS parse) + fiscal(pension) + water + litigation,
          run only on names that are CLEAR/REVIEW after tier 1 (don't spend OS-parse on already-excluded).
Resumable: a name already carrying a tier's fields in the underwriting store is skipped. Re-run any time.

  python3 grade_universe.py --tier1            # tier-1 across the universe, then rebuild master
  python3 grade_universe.py --tier2            # tier-2 across tier-1 survivors, then rebuild master
  python3 grade_universe.py --tier1 --tier2    # both, in sequence (the full grade)
  python3 grade_universe.py --tier1 --limit 50 # cap names (testing)
"""
import json, os, sys, time, subprocess, datetime
import underwrite_candidates as U

TODAY = datetime.date.today().isoformat()

HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "outputs")
STORE = os.path.join(OUT, "underwriting_candidates.json")
CHUNK = 25            # GRF/cert reload happens per chunk; bigger chunk = less reload overhead
THROTTLE = 2.0       # seconds between chunks (be polite to EMMA)


def load_universe():
    wl = json.load(open(os.path.join(OUT, "SCANNER_STANDING_WANTLIST.json")))
    by = {r["cusip"]: r for r in wl}
    for b in json.load(open(os.path.join(HERE, "muni_etf_sleeve_blended.json"))).get("barbell", []):
        by.setdefault(b["cusip"], {"cusip": b["cusip"], "security": b.get("security"),
                                   "tey_aftertax": b.get("tey_ytw_aftertax")})
    return by


def meta_of(by, cusips):
    return {cu: {"pledge": ("water" if "water" in ((by.get(cu, {}).get("security") or "").lower()) else "school"),
                 "tey": by.get(cu, {}).get("tey_aftertax")} for cu in cusips}


def store():
    try: return {r["cusip"]: r for r in json.load(open(STORE))}
    except Exception: return {}


def save(recs):
    prior = store()
    for r in recs: prior[r["cusip"]] = r
    json.dump(list(prior.values()), open(STORE, "w"), indent=1, default=str)


def run_tier(name, screens, cusips, by, done_if):
    """done_if(rec)->bool marks a name already screened for this tier (resume/skip)."""
    have = store()
    todo = [cu for cu in cusips if not done_if(have.get(cu, {}))]
    print(f"[{name}] universe {len(cusips)} | already done {len(cusips)-len(todo)} | to do {len(todo)}", flush=True)
    for i in range(0, len(todo), CHUNK):
        batch = todo[i:i + CHUNK]
        try:
            recs = U.underwrite(batch, meta_of(by, batch), screens=screens)
            save(recs)
            nclear = sum(1 for r in recs if r["uw_verdict"] == "CLEAR")
            print(f"[{name}] {min(i+CHUNK,len(todo))}/{len(todo)}  (+{nclear} CLEAR this chunk)", flush=True)
        except Exception as e:
            print(f"[{name}] chunk @{i} FAILED: {e} — backoff 30s", flush=True); time.sleep(30)
        time.sleep(THROTTLE)


def rebuild_master():
    subprocess.run([sys.executable, os.path.join(HERE, "build_diligence_master.py")], cwd=HERE)


def main():
    args = sys.argv[1:]
    fresh = "--fresh" in args     # FULL FRESH: re-run every name through all screens (module caches must be
                                  # cleared beforehand to force re-fetch); resume on today's screened_asof.
    by = load_universe(); cusips = list(by)
    if "--limit" in args:
        cusips = cusips[:int(args[args.index("--limit") + 1])]
    print(f"=== GRADE UNIVERSE — {len(cusips)} qualified names{' [FULL FRESH]' if fresh else ''} ===", flush=True)
    fresh_done = lambda r: r.get("screened_asof") == TODAY

    if "--tier1" in args:
        run_tier("TIER1", U.TIER1_SCREENS, cusips, by,
                 done_if=(fresh_done if fresh else
                          (lambda r: r.get("call_risk") is not None or r.get("flood_score") is not None)))
        rebuild_master()

    if "--tier2" in args:
        if fresh:
            # FULL FRESH: deep-screen EVERY name (full coverage). Resume on the TIER-2-SPECIFIC stamp
            # (deep_asof) — NOT screened_asof, which tier-1 already set, or every name would be skipped.
            targets = cusips
            print(f"[TIER2] {len(targets)} names (FULL FRESH — all, not just survivors)", flush=True)
            run_tier("TIER2", U.ALL_SCREENS, targets, by, done_if=lambda r: r.get("deep_asof") == TODAY)
        else:
            # standard: only grade tier-1 survivors (don't OS-parse already-excluded names)
            m = {r["cusip"]: r for r in json.load(open(os.path.join(OUT, "DILIGENCE_MASTER.json")))}
            survivors = [cu for cu in cusips if m.get(cu, {}).get("uw_verdict") in ("CLEAR", "REVIEW")]
            print(f"[TIER2] {len(survivors)} tier-1 survivors (CLEAR/REVIEW) to deep-screen", flush=True)
            run_tier("TIER2", U.ALL_SCREENS, survivors, by,
                     done_if=lambda r: r.get("av_top1_share") is not None or r.get("issuer_litigation_flag") is not None)
        rebuild_master()

    # final grade summary
    from collections import Counter
    m = json.load(open(os.path.join(OUT, "DILIGENCE_MASTER.json")))
    inU = [r for r in m if r["cusip"] in set(cusips)]
    print(f"\n=== GRADED {len(inU)} of {len(cusips)} | verdicts {dict(Counter(r['uw_verdict'] for r in inU))} ===", flush=True)


if __name__ == "__main__":
    main()
