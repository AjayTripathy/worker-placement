"""bond_scanner.py — standing scanner that surfaces NEWLY-qualifying insulated CA munis to grow the book.

Re-run this whenever the universe refreshes (new IBKR scan dropped into bonds_priced.json, or a
--universe file). It diffs against everything already seen + already held, runs only the NEW names
through the validated screen, and emits execution-ready candidates (with limits) for the resting-bid
want-list. Incremental by design: expensive steps (OpenFIGI, EMMA) touch only genuinely new CUSIPs.

FUNNEL (each new CUSIP):
  1. dedup        — skip if already held or already evaluated (state)
  2. feasible     — near-par/discount px in range, intermediate maturity
  3. pre-filter   — OpenFIGI sector ∈ insulated (cached from breadth_scan; OpenFIGI only new issuers)
  4. AUTH gate    — build_option_B.verify(): EMMA issue-title sectype ∈ {SCHOOL-GO, WATER-REV, ELEC-REV}
                    AND not federally taxable  (catches COP/CFD/judgment/taxable the pre-filter misses)
  5. liquidity    — liquidity_gate floor (≤90d since trade, ≥12 tr/yr, ≥1 two-sided day)
  6. after-tax    — tey_aftertax (de-minimis aware) = the selection metric
  7. fit-to-need  — ladder-rung gap + new-issuer diversification (book-growth, not just finding)
Output: outputs/new_candidates_<date>.{json,md}. Deep credit/zone/fire DD stays at promotion time
(school_go_issuer_credit + build_sleeve_blend) — the scanner FINDS, the build VETS.

State: outputs/scanner_state.json  — seed it once from breadth_scan_state.json (889 issuers pre-classified).
"""
import json, os, re, sys, time, datetime, argparse
from collections import Counter, defaultdict

import liquidity_gate as L
import breadth_scan as BS
import build_option_B as B
import school_go_issuer_credit as SC   # OpenFIGI resolve_cusips
import emma_scraper as E

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "outputs")
STATE = os.path.join(OUT, "scanner_state.json")
BOOK = os.path.join(HERE, "muni_etf_sleeve_blended.json")
UNIVERSE_DEFAULT = os.path.join(HERE, "bonds_priced.json")
PX_LO, PX_HI = 74.0, 103.5          # feasible dollar-price band (discount 3s .. near-par 4-5s)
MAT_LO, MAT_HI = 2034, 2046         # ladder zone
MIN_TEY = 0.060                     # after-tax TEY floor — below this it can't compete with the
                                    # ~8.2% book (premium callable bonds with negative yield-to-worst
                                    # pass the pledge/liquidity gates but are uninvestable)
RETEST = ("liquidity", "low_tey", "fetch_blocked", "verify_err")  # transient -> re-test next run

def load_json(p, default):
    try: return json.load(open(p))
    except Exception: return default
def save_json(p, obj):
    json.dump(obj, open(p, "w"), indent=1, default=str)

def load_state():
    s = load_json(STATE, None)
    if s: return s
    # seed from the breadth scan: reuse the 889 issuer→sector classifications (free OpenFIGI cache)
    bs = load_json(os.path.join(OUT, "breadth_scan_state.json"), {})
    sectors = {iss6: v["sector"] for iss6, v in bs.get("sectors", {}).items()}
    return {"seen": {}, "issuer_sector": sectors, "emitted": [], "runs": []}

def load_held():
    bk = load_json(BOOK, {})
    held = [x["cusip"] for x in bk.get("barbell", [])]
    held_iss = {c[:6] for c in held}
    held_yr = Counter(int(x["maturity"][:4]) for x in bk.get("barbell", []) if x.get("maturity"))
    return set(held), held_iss, held_yr

def issuer_sector(iss6, state, new_issuers):
    """Cached sector for an issuer-6; queue unknowns for a batch OpenFIGI resolve."""
    s = state["issuer_sector"].get(iss6)
    if s is None:
        new_issuers.add(iss6)
    return s

def resolve_new_issuers(reps, state):
    """Batch-OpenFIGI the representative CUSIPs of unseen issuers; cache the sector."""
    if not reps: return
    res = SC.resolve_cusips(list(reps.values()))
    for iss6, cu in reps.items():
        nm = (res.get(cu) or {}).get("figi_name")
        state["issuer_sector"][iss6] = BS.classify_sector(nm)

def fit_note(cusip, mat_yr, held_iss, held_yr):
    notes, score = [], 0
    if held_yr.get(mat_yr, 0) < 2:
        notes.append(f"fills {mat_yr} rung"); score += 2
    if cusip[:6] not in held_iss:
        notes.append("new issuer"); score += 1
    return score, "; ".join(notes) or "ladder OK"

def limit_from_tape(pxv, sectype):
    """Resting-bid limit = last customer-buy + a small tolerance (tighter on discounts)."""
    if pxv is None: return None
    tol = 0.25 if pxv >= 95 else 0.40
    return round(pxv + tol, 2)

def scan(universe_path, max_new=60, relax_liquidity=False):
    state = load_state()
    held, held_iss, held_yr = load_held()
    uni = load_json(universe_path, {}).get("bonds", [])
    sess = E._session()
    today = datetime.date.today()
    run_id = today.isoformat()

    # 1-2. candidate set: feasible, not held, not already emitted, not already evaluated
    #       (unless prior fail was liquidity-only — those get a monthly re-test)
    emitted = set(state.get("emitted", []))
    cand = []
    for b in uni:
        cu = b.get("cusip"); px = b.get("px") or 0
        if not cu or cu in held or cu in emitted: continue
        if not (PX_LO <= px <= PX_HI): continue
        try: yr = int(str(b.get("maturity"))[:4])
        except Exception: continue
        if not (MAT_LO <= yr <= MAT_HI): continue
        prev = state["seen"].get(cu)
        if prev and prev.get("reject") not in (None,) + RETEST:    # permanent rejects: skip
            continue
        if prev and prev.get("reject") in RETEST and (today - datetime.date.fromisoformat(prev["last"])).days < 30:
            continue  # re-test yield/liquidity rejects only monthly (price/tape can flip them)
        cand.append(b)

    # 3. pre-filter to insulated sectors (OpenFIGI, cached). Resolve unseen issuers in one batch.
    new_issuers, reps = set(), {}
    for b in cand:
        iss6 = b["cusip"][:6]
        if issuer_sector(iss6, state, new_issuers) is None and iss6 not in reps:
            reps[iss6] = b["cusip"]
    if reps:
        print(f"[scan] OpenFIGI resolving {len(reps)} new issuers...", flush=True)
        resolve_new_issuers(reps, state)
    pre = [b for b in cand if (state["issuer_sector"].get(b["cusip"][:6]) or "") in BS.INSULATED]
    print(f"[scan] universe new&feasible={len(cand)} → insulated pre-filter={len(pre)}", flush=True)

    # 4-7. authoritative EMMA gate + liquidity + after-tax TEY + fit, bounded to max_new EMMA pulls
    out, tested, blocks = [], 0, 0
    # test cheapest-first: discounts/par carry the best after-tax TEY and avoid the premium-callable
    # junk (high YTM-to-maturity but negative YTW-to-call) that would otherwise burn the EMMA budget
    for b in sorted(pre, key=lambda x: (x.get("px") or 999)):
        if tested >= max_new: break
        cu = b["cusip"]; tested += 1
        rec = {"cusip": cu, "last": run_id}
        try:
            st, ytw, td, pxv, taxable = B.verify(cu, sess)
            blocks = 0
        except RuntimeError as e:                # EMMA rate-limit / block -> back off, mark retryable
            if "blocked" in str(e):
                blocks += 1
                rec["reject"] = "fetch_blocked"; state["seen"][cu] = rec
                save_json(STATE, state)
                if blocks >= 8:                  # sustained block -> stop, let next run resume
                    print(f"[scan] EMMA blocked x{blocks}; stopping run to resume later", flush=True); break
                if blocks % 3 == 0: sess = E._session()          # refresh session
                time.sleep(min(45, 4 * blocks)); continue
            rec["reject"] = "verify_err"; state["seen"][cu] = rec; continue
        except Exception:
            rec["reject"] = "verify_err"; state["seen"][cu] = rec; continue
        if taxable or st not in B.INCLUDE:
            rec["reject"] = "pledge_or_taxable"; rec["sectype"] = st; rec["taxable"] = taxable
            state["seen"][cu] = rec; continue
        m = L.tape_metrics(cu, sess, today)
        ok, why = L.passes(m)
        if not ok and not relax_liquidity:
            rec["reject"] = "liquidity"; rec["why"] = why; state["seen"][cu] = rec; continue
        px = b.get("px") or pxv
        tey, demin = (None, None)
        try: tey, demin = B.tey_aftertax(px, b["coupon"], ytw or 0, b["maturity"])
        except Exception: pass
        if tey is None or tey < MIN_TEY:   # premium-callable / negative-YTW etc. — re-testable
            rec["reject"] = "low_tey"; rec["tey_aftertax"] = tey; state["seen"][cu] = rec; continue
        yr = int(str(b["maturity"])[:4])
        fscore, fnote = fit_note(cu, yr, held_iss, held_yr)
        ch, label, lbl2 = (B.MAP.get(st) or ("", "", st))
        # OUTLIER GATE: a clean insulated CA muni yields ~4.0-4.6% gross (~8.0-9.2% after-tax TEY).
        # Abnormally high yield on a 'safe' pledge = the market pricing in something (weaker credit,
        # long duration, odd/uncovered structure, stale px). Flag for priority DD; do NOT treat the
        # high TEY as a clean find — same cheap-for-a-reason trap as the deep-value/GARP finders.
        outlier = None
        if (ytw or 0) > 0.05 or (tey or 0) > 0.095:
            outlier = f"yield>peer (gross {ytw*100:.2f}%) — verify credit/duration/structure"
        rec.update(reject=None, sectype=st, security=lbl2, coupon=b["coupon"], maturity=b["maturity"],
                   px=px, ytw=ytw, tey_aftertax=tey, demin=demin, limit=limit_from_tape(pxv, st),
                   last_print=pxv, last_trade=td, outlier=outlier, liq={k: m.get(k) for k in
                   ("n365","two_sided_days","days_since_trade","med_block","max_block")},
                   liq_pass=ok, fit_score=fscore, fit_note=fnote)
        state["seen"][cu] = rec
        out.append(rec)
        if tested % 25 == 0:                     # incremental persist — survive a mid-pass EMMA failure
            save_json(STATE, state); print(f"[scan] tested {tested}, qualified {len(out)}...", flush=True)
        time.sleep(0.7)                          # throttle: 2 EMMA hits/name, stay under the rate limit

    # rank: fit-adjusted after-tax TEY; emit
    out.sort(key=lambda r: ((r.get("tey_aftertax") or 0) + 0.0015 * r.get("fit_score", 0)), reverse=True)
    new_ids = [r["cusip"] for r in out if r["cusip"] not in state["emitted"]]
    state["emitted"] = sorted(set(state["emitted"]) | set(new_ids))
    state["runs"].append({"run": run_id, "tested": tested, "qualified": len(out),
                          "new": len(new_ids), "universe": os.path.basename(universe_path)})
    save_json(STATE, state)
    write_candidates(out, run_id, tested, len(cand))
    return out

STANDING = os.path.join(OUT, "SCANNER_STANDING_WANTLIST")
def append_standing(out):
    """Maintain a cumulative, deduped standing want-list of PROMOTE-READY finds (non-outliers).
    This is the running 'names to add' list the cron appends to and you work as resting bids."""
    book = load_json(STANDING + ".json", [])
    have = {r["cusip"] for r in book}
    added = [r for r in out if not r.get("outlier") and r.get("cusip") not in have]
    book += added
    book.sort(key=lambda r: -(r.get("tey_aftertax") or 0))
    save_json(STANDING + ".json", book)
    md = ["# Scanner Standing Want-List — promote-ready insulated candidates",
          f"\n_Cumulative, deduped. Each is credit/zone/fire DD-pending before promotion. "
          f"‡ = de-minimis (limit is a hard tax ceiling). Limits are resting-bid levels._\n",
          "| CUSIP | Security | Cpn/Mat | After-tax TEY | Px | **Limit** | n365 | 2sd | Found | Fit |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for r in book:
        liq = r.get("liq") or {}; dm = "‡" if r.get("demin") else ""
        tey = f"{r['tey_aftertax']*100:.2f}%" if r.get("tey_aftertax") else "—"
        md.append(f"| {r['cusip']} | {r.get('security','')}{dm} | {r['coupon']}s {r['maturity'][:7]} "
                  f"| {tey} | {r.get('px')} | **{r.get('limit')}** | {liq.get('n365')} "
                  f"| {liq.get('two_sided_days')} | {r.get('last','')} | {r.get('fit_note','')} |")
    open(STANDING + ".md", "w").write("\n".join(md))
    return added

def write_candidates(out, run_id, tested, n_feasible):
    save_json(os.path.join(OUT, f"new_candidates_{run_id}.json"), out)
    L_ = []
    L_.append(f"# New Bond Candidates — {run_id}")
    L_.append(f"\n_Scanner pass: {n_feasible} new&feasible names → {tested} EMMA-tested → "
              f"**{len(out)} qualified** (insulated pledge + not taxable + liquidity floor passed). "
              f"Ranked by de-minimis-aware after-tax TEY. ‡ = de-minimis. Limits are resting-bid levels "
              f"(last customer-buy + tolerance). Credit/zone/fire DD pending before promotion._\n")
    clean = [r for r in out if not r.get("outlier")]
    flagged = [r for r in out if r.get("outlier")]
    def tbl(rows):
        s = ["| CUSIP | Security | Cpn/Mat | After-tax TEY | Px | **Limit** | n365 | 2sd | Fit |",
             "|---|---|---|---|---|---|---|---|---|"]
        for r in rows:
            liq = r.get("liq") or {}; dm = "‡" if r.get("demin") else ""
            tey = f"{r['tey_aftertax']*100:.2f}%" if r.get("tey_aftertax") else "—"
            s.append(f"| {r['cusip']} | {r.get('security','')}{dm} | {r['coupon']}s {r['maturity'][:7]} "
                     f"| {tey} | {r.get('px')} | **{r.get('limit')}** | {liq.get('n365')} "
                     f"| {liq.get('two_sided_days')} | {r.get('fit_note')} |")
        return s
    L_.append(f"## Promote-ready ({len(clean)}) — peer-range yield, DD then add\n")
    L_ += tbl(clean) if clean else ["| _none this pass_ | | | | | | | | |"]
    if flagged:
        L_.append(f"\n## Outliers ({len(flagged)}) — cheap for a reason? PRIORITY DD before trusting the TEY\n")
        L_ += tbl(flagged)
        for r in flagged:
            L_.append(f"- **{r['cusip']}** — {r['outlier']}")
    open(os.path.join(OUT, f"new_candidates_{run_id}.md"), "w").write("\n".join(L_))
    print("\n".join(L_))

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--universe", default=UNIVERSE_DEFAULT, help="bonds_priced.json-shaped feed")
    ap.add_argument("--max-new", type=int, default=60, help="cap EMMA pulls per run")
    ap.add_argument("--relax-liquidity", action="store_true", help="emit even if liquidity floor fails")
    ap.add_argument("--append-wantlist", action="store_true",
                    help="append new promote-ready finds to the cumulative standing want-list")
    a = ap.parse_args()
    out = scan(a.universe, max_new=a.max_new, relax_liquidity=a.relax_liquidity)
    if a.append_wantlist:
        added = append_standing(out)
        print(f"\n[standing want-list] +{len(added)} new promote-ready → {STANDING}.md")
