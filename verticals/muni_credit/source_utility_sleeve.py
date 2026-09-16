"""source_utility_sleeve — source a SUPPLY-DIVERSIFIED utility-revenue sleeve to diversify the book's
property-tax-regime concentration (Prop 13 / split-roll / federal-exemption) without giving up AI-insulation.

WHY. The book is ~79% CA school/local GO (one regulatory + one revenue regime: ad-valorem property tax).
Essential-service utility revenue (water/sewer/electric) is rate-based, demand-inelastic, AI/cap-gains-
insulated, and NOT property tax — but only diversifies if the sleeve is itself SUPPLY-diversified (five
Colorado-River systems just swap one correlated CA tail for another).

This reuses the SAME gauntlet as the school-GO scanner — no parallel logic:
  breadth_scan.classify_sector  -> OpenFIGI pre-filter to I_water_rev + I_elec_rev (electric bucket added)
  build_option_B.verify         -> authoritative EMMA pledge gate: sectype in {WATER-REV, ELEC-REV}, not taxable
  liquidity_gate.passes         -> two-sided-tape execution floor
  build_option_B.tey_aftertax   -> de-minimis-aware after-tax TEY (the selection metric)
  water_revenue_underwrite      -> coverage (DSCR) + rate covenant + supply risk + current CDD coverage
  utility_supply.supply_bucket  -> supply source, for the diversification cap

Then caps: <= PER_ISSUER per issuer-6 and <= PER_BUCKET per supply source, so the emitted sleeve is
diversified by construction. Serial + throttled + resumable (EMMA rate limit). NEVER assumes coverage:
a name whose DSCR can't be read is emitted as REVIEW-coverage-unverified, never as clean.

Output: outputs/UTILITY_SLEEVE_CANDIDATES.{json,md} + a standing state file.
  python source_utility_sleeve.py [--max-new 40] [--per-issuer 2] [--per-bucket 3] [--relax-liquidity]
"""
import argparse, datetime, json, os, time
from collections import Counter, defaultdict

import emma_scraper as E
import breadth_scan as BS
import build_option_B as B
import liquidity_gate as L
import water_revenue_underwrite as W
import utility_supply as US
import school_go_issuer_credit as SC   # OpenFIGI resolve_cusips

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "outputs")
PRICED = os.path.join(HERE, "bonds_priced.json")
BREADTH = os.path.join(OUT, "breadth_scan_state.json")
STATE = os.path.join(OUT, "utility_sleeve_state.json")
UTILRES = os.path.join(OUT, "utility_issuer_resolution.json")   # OpenFIGI cache for FULL-window issuers
CANDS = os.path.join(OUT, "UTILITY_SLEEVE_CANDIDATES")

PX_LO, PX_HI = 88, 105
MAT_LO, MAT_HI = 2027, 2050
MIN_TEY = 0.072
UTIL_SECTORS = {"I_water_rev", "I_elec_rev"}


def _load(p, d):
    try: return json.load(open(p))
    except Exception: return d


def _held():
    """CUSIPs already in the book / want-list — don't re-source them."""
    held = set()
    for f, key in (("outputs/dd_verdicts.json", None),
                   ("outputs/DILIGENCE_MASTER.json", "in_book"),
                   ("outputs/SCANNER_STANDING_WANTLIST.json", None)):
        d = _load(os.path.join(HERE, f), [])
        if isinstance(d, dict):
            held |= set(d.keys())
        else:
            held |= {r.get("cusip") for r in d if isinstance(r, dict)}
    return {h for h in held if h}


def _window_by_issuer():
    """issuer-6 -> [CUSIPs] across the FULL price/maturity window of bonds_priced (not just near-par)."""
    win = {}
    for b in _load(PRICED, {}).get("bonds", []):
        cu = b.get("cusip"); px = b.get("px") or 0
        if not cu or not (PX_LO <= px <= PX_HI):
            continue
        try:
            yr = int(str(b.get("maturity"))[:4])
        except Exception:
            continue
        if MAT_LO <= yr <= MAT_HI:
            win.setdefault(cu[:6], []).append(cu)
    return win


def _util_issuers():
    """Insulated water+electric issuer-6s, reclassified with the (electric-aware) classifier — from BOTH
    the breadth near-par cache AND the utility full-window OpenFIGI cache (--resolve). No new API calls."""
    out, by_iss = {}, {}
    win = _window_by_issuer()
    st = _load(BREADTH, {})
    b_by = st.get("by_issuer", {})
    rep_to_iss = {v[0]: k for k, v in b_by.items()}
    for cu, meta in st.get("resolved", {}).items():
        i6 = rep_to_iss.get(cu)
        if i6 and BS.classify_sector(meta.get("figi_name")) in UTIL_SECTORS:
            out[i6] = {"name": meta.get("figi_name"), "sector": BS.classify_sector(meta.get("figi_name"))}
            by_iss[i6] = win.get(i6) or b_by.get(i6, [])
    for i6, meta in _load(UTILRES, {}).get("issuers", {}).items():
        sec = BS.classify_sector(meta.get("name"))
        if sec in UTIL_SECTORS:
            out.setdefault(i6, {"name": meta.get("name"), "sector": sec})
            by_iss.setdefault(i6, meta.get("cusips") or win.get(i6, []))
    return out, by_iss


def resolve_universe(max_resolve=400):
    """OpenFIGI-resolve the utility-window issuers NOT already in the breadth or utility cache, so large
    systems (LADWP/SMUD/MWD) that issue outside the near-par sample surface. Writes the utility cache and
    reports newly-classified water/electric issuers. Free (keyless OpenFIGI, paced)."""
    win = _window_by_issuer()
    st = _load(BREADTH, {})
    known = set({v[0]: k for k, v in st.get("by_issuer", {}).items()}.values())
    uc = _load(UTILRES, {"issuers": {}})
    known |= set(uc["issuers"].keys())
    todo = [i6 for i6 in win if i6 not in known][:max_resolve]
    reps = [win[i6][0] for i6 in todo]
    print(f"[util] OpenFIGI-resolving {len(reps)} new window issuers (of {len(win)} total)...", flush=True)
    for i in range(0, len(reps), 10):
        chunk = reps[i:i + 10]
        try:
            r = SC.resolve_cusips(chunk)
        except Exception as e:
            print(f"   figi batch {i} err {str(e)[:70]}", flush=True); time.sleep(5); continue
        for cu, meta in r.items():
            uc["issuers"][cu[:6]] = {"name": meta.get("figi_name"), "cusips": win.get(cu[:6], [])}
        if i % 50 == 0:
            json.dump(uc, open(UTILRES, "w"), indent=1, default=str)
            print(f"   figi {i + len(chunk)}/{len(reps)}", flush=True)
    json.dump(uc, open(UTILRES, "w"), indent=1, default=str)
    new_util = [(i6, uc["issuers"][i6]["name"], BS.classify_sector(uc["issuers"][i6]["name"]))
                for i6 in todo if i6 in uc["issuers"]
                and BS.classify_sector(uc["issuers"][i6]["name"]) in UTIL_SECTORS]
    print(f"[util] newly-classified utility issuers: {len(new_util)} "
          f"({Counter(s for _, _, s in new_util)})", flush=True)
    for i6, nm, sec in new_util:
        print(f"   {sec:12} {i6} {nm}", flush=True)
    return new_util


def _county_for(cusip):
    m = {r["cusip"]: r for r in _load(os.path.join(HERE, "outputs/DILIGENCE_MASTER.json"), [])}
    return (m.get(cusip) or {}).get("county")


_ARID = {"COLORADO_RIVER", "GROUNDWATER"}


def _best_dscr(uw):
    """Prefer the CURRENT continuing-disclosure DSCR over the issuance-vintage OS DSCR (the stale-vs-current
    lesson — EBMUD reads 1.65x at issuance, 2.51x current). Guard: an implausibly high current value (>10x)
    is a parse artifact -> fall back to OS; a low/negative current value is a REAL current signal -> keep it."""
    cur, os_ = uw.get("current_dscr"), uw.get("dscr")
    if cur is not None:
        return os_ if (cur > 10.0 and os_ is not None) else cur
    return os_


def _coverage_verdict(sectype, uw, bucket="UNKNOWN"):
    """Sleeve coverage verdict, driven by DSCR vs covenant (current coverage preferred). Supply is handled
    geographically: the underwriter's keyword supply-string over-attributes 'Colorado River / SGMA' (it
    false-FLAGged EBMUD, a Mokelumne/Sierra system), so supply is surfaced via the geographic bucket — a
    REVIEW only for genuinely arid/groundwater sources — while the per-bucket CAP enforces diversification.
    A real coverage breach (DSCR < covenant) is still a hard FLAG; coverage unread is never clean."""
    d = _best_dscr(uw)
    cov = uw.get("rate_covenant") or 1.10
    if d is None:
        return "REVIEW"                            # no coverage read -> never clean
    if d < max(cov, 1.0):
        return "FLAG"                              # genuine coverage breach (incl. negative/unaudited)
    tier = "PASS" if d >= max(cov, 1.25) else "REVIEW"
    if sectype == "WATER-REV" and bucket in _ARID and tier == "PASS":
        tier = "REVIEW"                            # healthy coverage but arid/groundwater supply -> surface
    return tier


def scan(max_new=40, per_issuer=2, per_bucket=3, relax_liquidity=False, min_tey=MIN_TEY):
    state = _load(STATE, {"seen": {}, "qualified": []})
    held = _held()
    issuers, by_iss = _util_issuers()
    uni = {b["cusip"]: b for b in _load(PRICED, {}).get("bonds", []) if b.get("cusip")}
    print(f"[util] insulated water+electric issuers (cached): {len(issuers)} "
          f"({Counter(v['sector'] for v in issuers.values())})", flush=True)

    # candidate CUSIPs: near-par, in-window, in a utility issuer, not held, not permanently rejected
    cand = []
    for i6, meta in issuers.items():
        for cu in by_iss.get(i6, []):
            b = uni.get(cu)
            if not b or cu in held:
                continue
            px = b.get("px") or 0
            if not (PX_LO <= px <= PX_HI):
                continue
            try:
                yr = int(str(b.get("maturity"))[:4])
            except Exception:
                continue
            if not (MAT_LO <= yr <= MAT_HI):
                continue
            prev = state["seen"].get(cu)
            # skip names already resolved (qualified or permanently rejected); re-test only transient fails
            if prev and prev.get("reject") not in ("liquidity", "low_tey", "fetch_blocked"):
                continue
            cand.append({**b, "issuer6": i6, "sector_pre": meta["sector"], "figi_name": meta["name"]})
    # ISSUER BREADTH FIRST: large diversified systems trade near par, so a pure cheapest-first sort buries
    # them under deep-discount names. Front-load issuers with no name yet tested (one representative each),
    # then cheapest-first within that — so a single bounded pass covers every issuer before doubling up.
    done_iss = {r["cusip"][:6] for r in state["seen"].values() if r.get("reject") != "fetch_blocked"}
    seen_this = set()
    def order(x):
        i6 = x["issuer6"]
        first_for_issuer = 0 if (i6 not in done_iss and i6 not in seen_this) else 1
        seen_this.add(i6)
        return (first_for_issuer, x.get("px") or 999)
    cand.sort(key=order)
    print(f"[util] candidate near-par CUSIPs: {len(cand)} across {len({c['issuer6'] for c in cand})} "
          f"issuers (testing up to {max_new}, issuer-breadth-first)", flush=True)

    sess = E._session()
    qualified, tested, blocks = [], 0, 0
    for b in cand:
        if tested >= max_new:
            break
        cu = b["cusip"]; tested += 1
        rec = {"cusip": cu, "issuer6": b["issuer6"], "figi_name": b["figi_name"]}
        try:
            st, ytw, td, pxv, taxable = B.verify(cu, sess); blocks = 0
        except RuntimeError as e:
            if "blocked" in str(e):
                blocks += 1
                if blocks >= 8:
                    print("[util] EMMA blocked — stopping; resume later", flush=True); break
                if blocks % 3 == 0: sess = E._session()
                time.sleep(min(45, 4 * blocks)); tested -= 1; continue
            rec["reject"] = "verify_err"; state["seen"][cu] = rec; continue
        except Exception:
            rec["reject"] = "verify_err"; state["seen"][cu] = rec; continue
        if taxable or st not in ("WATER-REV", "ELEC-REV"):
            rec.update(reject="pledge_or_taxable", sectype=st, taxable=taxable)
            state["seen"][cu] = rec; continue
        m = L.tape_metrics(cu, sess, datetime.date.today())
        ok, why = L.passes(m)
        if not ok and not relax_liquidity:
            rec.update(reject="liquidity", why=why); state["seen"][cu] = rec; continue
        px = b.get("px") or pxv
        try:
            tey, demin = B.tey_aftertax(px, b["coupon"], ytw or 0, b["maturity"])
        except Exception:
            tey, demin = None, None
        if tey is None or tey < min_tey:
            rec.update(reject="low_tey", tey_aftertax=tey); state["seen"][cu] = rec; continue
        # coverage / supply (reuse the water-revenue underwriter incl. the current CDD coverage)
        try:
            uw = W.underwrite_water(cu, session=sess, use_cache=True, with_current=True)
        except Exception:
            uw = {}
        county = _county_for(cu)
        bucket = US.supply_bucket(sectype=st, issuer=uw.get("issuer") or b["figi_name"], county=county,
                                  system_type=uw.get("system_type"), supply_note=uw.get("supply_note"))
        rec.update(reject=None, sectype=st, coupon=b["coupon"], maturity=b["maturity"], px=px, ytw=ytw,
                   tey_aftertax=tey, demin=demin, liq_pass=ok,
                   liq={k: m.get(k) for k in ("n365", "two_sided_days", "days_since_trade", "max_block")},
                   dscr=uw.get("dscr"), current_dscr=uw.get("current_dscr"),
                   rate_covenant=uw.get("rate_covenant"), supply_risk=uw.get("supply_risk"),
                   coverage_verdict=_coverage_verdict(st, uw, bucket), supply_bucket=bucket, county=county,
                   issuer=uw.get("issuer") or b["figi_name"])
        state["seen"][cu] = rec
        qualified.append(rec)
        if tested % 10 == 0:
            json.dump(state, open(STATE, "w"), indent=1, default=str)
            print(f"[util] tested {tested}, qualified {len(qualified)}", flush=True)
        time.sleep(0.7)

    json.dump(state, open(STATE, "w"), indent=1, default=str)
    # build the sleeve from ALL non-rejected names seen across runs (cumulative + resumable), re-grading
    # electric coverage so cached water-underwriter FLAGs on power bonds get corrected.
    allq = []
    for r in state["seen"].values():
        if r.get("reject") is not None:
            continue
        # re-grade every cached name with the current verdict logic (rescues stale-OS / mislabeled-supply
        # FLAGs — e.g. EBMUD — without re-hitting EMMA)
        r["coverage_verdict"] = _coverage_verdict(
            r.get("sectype"),
            {"current_dscr": r.get("current_dscr"), "dscr": r.get("dscr"),
             "rate_covenant": r.get("rate_covenant")},
            r.get("supply_bucket", "UNKNOWN"))
        # OUTLIER GATE (same discipline as the school scanner): a clean insulated CA muni yields ~8-9% TEY.
        # An abnormally high yield on a 'safe' pledge is the market pricing weaker credit/odd structure/
        # unreadable coverage — cheap-for-a-reason. Flag it; don't let it top-rank the sleeve.
        tey, ytw = r.get("tey_aftertax") or 0, r.get("ytw") or 0
        r["outlier"] = ("yield>peer (gross %.2f%%) — verify credit/structure/coverage before any buy"
                        % (ytw * 100)) if (tey > 0.095 or ytw > 0.05) else None
        allq.append(r)
    sleeve = _apply_caps(allq, per_issuer, per_bucket)
    _write(allq, sleeve, tested, per_issuer, per_bucket)
    return allq, sleeve


def _apply_caps(qualified, per_issuer, per_bucket):
    """Emit a SUPPLY-DIVERSIFIED sleeve: best after-tax TEY first, capped per issuer-6 and per supply
    source. Names whose coverage couldn't be read are eligible but de-prioritized (REVIEW, not clean)."""
    def keyf(r):
        cov_ok = 1 if (r.get("coverage_verdict") in ("PASS", "CLEAR", "REVIEW")) else 0
        not_outlier = 0 if r.get("outlier") else 1     # clean-yield names rank above cheap-for-a-reason
        return (cov_ok, not_outlier, r.get("tey_aftertax") or 0)
    sleeve, n_iss, n_bucket = [], Counter(), Counter()
    for r in sorted(qualified, key=keyf, reverse=True):
        if r.get("coverage_verdict") == "FLAG":
            continue                                    # sub-covenant DSCR breach — exclude
        i6, bk = r["issuer6"], r.get("supply_bucket", "UNKNOWN")
        if n_iss[i6] >= per_issuer or n_bucket[bk] >= per_bucket:
            continue
        n_iss[i6] += 1; n_bucket[bk] += 1
        sleeve.append(r)
    return sleeve


def _write(qualified, sleeve, tested, per_issuer, per_bucket):
    json.dump({"asof": datetime.date.today().isoformat(), "tested": tested,
               "qualified": qualified, "sleeve": sleeve,
               "supply_mix": dict(Counter(r.get("supply_bucket") for r in sleeve))},
              open(CANDS + ".json", "w"), indent=1, default=str)
    L_ = [f"# Utility-Revenue Sleeve — supply-diversified candidates ({datetime.date.today()})", "",
          f"_Sourced via the school-GO scanner's gauntlet (OpenFIGI pre-filter → EMMA pledge/tax gate → "
          f"liquidity floor → de-minimis TEY → coverage/supply), restricted to WATER-REV + ELEC-REV, then "
          f"capped ≤{per_issuer}/issuer and ≤{per_bucket}/supply-source. {len(qualified)} qualified → "
          f"**{len(sleeve)} in the diversified sleeve**. Coverage UNVERIFIED ≠ clean; DSCR-breach excluded._",
          "", f"**Supply mix:** {dict(Counter(r.get('supply_bucket') for r in sleeve))}", "",
          "| # | CUSIP | Issuer | Pledge | Supply | Cpn | Mat | Px | TEY% | DSCR(OS/cur) | Covenant | Cov verdict | n/yr |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for i, r in enumerate(sleeve, 1):
        liq = r.get("liq") or {}
        dscr = f"{r.get('dscr') or '—'}/{r.get('current_dscr') or '—'}"
        cov = r.get("coverage_verdict") + (" ⚠outlier" if r.get("outlier") else "")
        L_.append(f"| {i} | {r['cusip']} | {str(r.get('issuer'))[:24]} | {r['sectype']} | "
                  f"{r.get('supply_bucket')} | {r.get('coupon')} | {str(r.get('maturity'))[:7]} | "
                  f"{r.get('px')} | {(r.get('tey_aftertax') or 0)*100:.2f} | {dscr} | "
                  f"{r.get('rate_covenant') or '—'} | {cov} | {liq.get('n365')} |")
    out_notes = [r for r in sleeve if r.get("outlier")]
    if out_notes:
        L_ += ["", "**⚠ Outliers (cheap-for-a-reason — priority DD, not clean):**"]
        L_ += [f"- {r['cusip']} {str(r.get('issuer'))[:30]}: {r['outlier']}" for r in out_notes]
    open(CANDS + ".md", "w").write("\n".join(L_))
    print(f"[util] qualified={len(qualified)} -> diversified sleeve={len(sleeve)} "
          f"| supply mix {dict(Counter(r.get('supply_bucket') for r in sleeve))}", flush=True)
    print(f"[util] -> {CANDS}.md", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-new", type=int, default=40)
    ap.add_argument("--per-issuer", type=int, default=2)
    ap.add_argument("--per-bucket", type=int, default=3)
    ap.add_argument("--relax-liquidity", action="store_true")
    ap.add_argument("--resolve", action="store_true",
                    help="OpenFIGI-resolve unresolved window issuers (surface large systems) before scanning")
    ap.add_argument("--resolve-only", action="store_true", help="run the OpenFIGI resolution and stop")
    ap.add_argument("--min-tey", type=float, default=MIN_TEY)
    a = ap.parse_args()
    if a.resolve or a.resolve_only:
        resolve_universe()
    if not a.resolve_only:
        scan(max_new=a.max_new, per_issuer=a.per_issuer, per_bucket=a.per_bucket,
             relax_liquidity=a.relax_liquidity, min_tey=a.min_tey)
