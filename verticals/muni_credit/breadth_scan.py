"""CA muni breadth scan — measure the FEASIBLE insulated universe to size true capacity.

Phase A: classify every near-par issuer (CUSIP6) in the cached IBKR CA universe by PLEDGE
         sector via OpenFIGI issuer name (insulated school/CCD GO + essential-service revenue
         vs. excluded state-GO / RDA / COP / land-secured / etc.).
Phase B: sample EMMA tape across the insulated issuers -> liquidity-PASSABLE rate (the real
         acquirability gate; the IBKR feed is close-only so its two_sided flags are useless).
Phase C: capacity curve = insulated issuers x pass-rate x per-issuer clip.

Resumable: writes outputs/breadth_scan_state.json after each phase so a restart re-uses work.
"""
import json, os, re, time, random
import school_go_issuer_credit as SC   # resolve_cusips (OpenFIGI)
import liquidity_gate as L

HERE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(HERE, "outputs", "breadth_scan_state.json")
PRICED = os.path.join(HERE, "bonds_priced.json")

def load_state():
    try: return json.load(open(STATE))
    except Exception: return {}
def save_state(s):
    json.dump(s, open(STATE, "w"), indent=1, default=str)

# ---------------- pledge-sector classifier (on OpenFIGI issuer name) ----------------
def classify_sector(name: str) -> str:
    """Pledge-sector from an abbreviated OpenFIGI muni-ticker name. Structure (COP/lease) is
    judged BEFORE sector: a water/school COP is a lease/appropriation obligation, NOT the
    insulated GO / net-revenue pledge, so it is excluded regardless of the underlying entity."""
    n = (name or "").upper()
    if not n: return "UNKNOWN"
    # --- structure overrides: explicit lease / appropriation paper is excluded outright ---
    if re.search(r"\bCOPS?\b|\bCTFS?\b|CERTIF|\bLEASE\b|LEASE REV|INSTALLMENT", n): return "X_cop_lease"
    # --- excluded sectors ---
    if re.search(r"\bCALIF(ORNIA)? ST\b|STATE OF CALIF|\bCA ST\b|CA PUB WKS|PUBLIC WKS|CA INFRAST|CA STWD|CA STATEWIDE|STATE PUB", n): return "X_state_go"
    if re.search(r"SUCCESSOR|REDEV|\bRDA\b|CMNTY REDEV|COMMUNITY REDEV|\bRA\b|PROJ AREA", n): return "X_rda"
    if re.search(r"TOBACCO", n): return "X_tobacco"
    if re.search(r"PENSION|\bPOB\b|PENS OBLIG", n): return "X_pob"
    if re.search(r"\bCFD\b|CMNTY FACIL|COMMUNITY FACIL|MELLO|\bSPL TAX\b|SPECIAL TAX|ASSESSMENT|REASSESS|\bAD\b|IMPROVEMENT BD|IMPROVEMENT BOND|\bID\b NO", n): return "X_landsecured"
    if re.search(r"AIRPORT|\bARPT\b|PORT\b|HARBOR|TOLL|TRANS CORRIDOR|TRANSN CORRIDOR|\bTRANS\b|TRANSP|TRANSPTRN|JOAQUIN HILLS|BRIDGE|TRANSIT|\bRAIL\b|HI SPD", n): return "X_transport"
    if re.search(r"HOSPITAL|\bHLTH\b|HEALTH|HOSP\b|MEDICAL|\bHOSP", n): return "X_health"
    if re.search(r"\bHSG\b|HOUSING|MULTIFAMILY|MULTIFAM|MORTGAGE|MTG REV", n): return "X_housing"
    # --- insulated core (abbreviation-aware) ---
    if re.search(r"CMNTY COLL|COMMUNITY COLL|CMNTY CLG|\bCLG\b|\bCCD\b", n): return "I_ccd_go"
    if re.search(r"\bUSD\b|\bUHSD\b|\bHSD\b|\bESD\b|\bUSDB?\b|UNIF\b|UNIFIED|\bSD\b|SCH DIST|SCHOOL DIST|\bSCHS?\b|\bELEM\b|ELEMENTARY|HIGH SCH|UN HIGH|UNION HIGH|BRD ED|BOARD OF ED|JT UN", n): return "I_school_go"
    if re.search(r"REGENTS|UNIV(ERSITY)? CALIF|UNIV OF CALIF|\bUC\b|\bCSU\b|STATE UNIV|TRS? STATE", n): return "I_univ_rev"
    if re.search(r"\bWTR\b|\bWT\b|WATER|\bSWR\b|SEWER|WASTEWATER|\bWST\b|\bIRR\b|IRRIG|RECLAMATION|\bMWD\b|\bMUD\b|\bPUD\b|\bCSD\b|MUNI UTIL|MUN UTIL|PUBLIC UTIL|UTIL\b|UTILITY|SANITAT|SANITARY|\bSAN DIST", n): return "I_water_rev"
    # --- electric/power enterprise revenue (essential service, rate-based, AI/cap-gains-insulated,
    #     NOT property tax). Tested AFTER water so a combined water-&-power system (e.g. LADWP "WTR & PWR")
    #     lands in water (it carries water supply anyway); pure power (SCPPA/NCPA/"PUB PWR") lands here. ---
    if re.search(r"\bELEC\b|ELECTRIC|\bPWR\b|\bPOWER\b|PUB(LIC)? PWR|PUB(LIC)? POWER|MUNI(CIPAL)? ELEC|ELEC SYS|POWER AGY|POWER AGENCY", n): return "I_elec_rev"
    # --- borderline (ad-valorem but general-government / financing conduit -> per-OS pledge read) ---
    if re.search(r"\bCITY OF\b|\bCOUNTY\b|\bCO\b|\bTOWN OF\b|\bCITY\b", n): return "B_city_county_go"
    if re.search(r"FIN(ANC)?(E|ING)? AUTH|FING AUTH|PUB FIN|PUBLIC FIN|FINANCE AUTH|JT PWRS|JOINT POWERS|\bJPA\b|MUNI FIN|\bPFA\b|JT PWR|FACS FING", n): return "B_fin_auth"
    return "UNKNOWN"

INSULATED = {"I_school_go", "I_ccd_go", "I_univ_rev", "I_water_rev", "I_elec_rev"}

# ---------------- Phase A ----------------
def phase_a(state):
    b = json.load(open(PRICED))["bonds"]
    nearpar = [x for x in b if 90 <= (x.get("px") or 0) <= 103 and x.get("cusip")]
    by_iss = {}
    for x in nearpar:
        by_iss.setdefault(x["cusip"][:6], []).append(x["cusip"])
    issuers = sorted(by_iss)
    state["n_nearpar_names"] = len(nearpar)
    state["n_issuers"] = len(issuers)
    state["by_issuer"] = {k: v for k, v in by_iss.items()}
    # one representative CUSIP per issuer for OpenFIGI
    reps = [v[0] for v in by_iss.values()]
    resolved = state.get("resolved", {})
    todo = [c for c in reps if c not in resolved]
    print(f"[A] near-par names={len(nearpar)} issuers={len(issuers)} | OpenFIGI todo={len(todo)}", flush=True)
    for i in range(0, len(todo), 10):
        chunk = todo[i:i+10]
        try:
            r = SC.resolve_cusips(chunk)            # handles its own 2.6s pacing
            resolved.update(r)
        except Exception as e:
            print(f"   figi batch {i} err {str(e)[:80]}", flush=True)
            time.sleep(5)
        if i % 100 == 0:
            state["resolved"] = resolved; save_state(state)
            print(f"   figi {i+len(chunk)}/{len(todo)}", flush=True)
    state["resolved"] = resolved
    # classify per issuer (map rep cusip -> issuer6)
    rep_to_iss = {v[0]: k for k, v in by_iss.items()}
    sectors = {}
    for cu, meta in resolved.items():
        iss6 = rep_to_iss.get(cu)
        if iss6:
            sectors[iss6] = {"name": meta.get("figi_name"), "sector": classify_sector(meta.get("figi_name")),
                             "n_cusips": len(by_iss[iss6])}
    state["sectors"] = sectors
    save_state(state)
    return state

# ---------------- Phase B ----------------
def phase_b(state, sample_n=110, seed=42):
    sectors = state["sectors"]; by_iss = state["by_issuer"]
    insulated_cusips = []
    for iss6, s in sectors.items():
        if s["sector"] in INSULATED:
            insulated_cusips += by_iss[iss6]
    state["n_insulated_cusips"] = len(insulated_cusips)
    rng = random.Random(seed)
    sample = rng.sample(insulated_cusips, min(sample_n, len(insulated_cusips)))
    done = state.get("liq", {})
    todo = [c for c in sample if c not in done]
    print(f"[B] insulated CUSIPs={len(insulated_cusips)} | tape sample todo={len(todo)}", flush=True)
    sess = L.E._session()
    for j, cu in enumerate(todo):
        try:
            m = L.tape_metrics(cu, sess)
            ok, why = L.passes(m)
            done[cu] = {**{k: m.get(k) for k in ("n365","two_sided_days","days_since_trade","med_block","max_block")},
                        "pass": ok, "reasons": why}
        except Exception as e:
            done[cu] = {"err": str(e)[:60], "pass": False}
        if j % 15 == 0:
            state["liq"] = done; save_state(state)
            print(f"   tape {j+1}/{len(todo)}", flush=True)
        time.sleep(0.4)
    state["liq"] = done
    save_state(state)
    return state

if __name__ == "__main__":
    import sys
    st = load_state()
    phase = sys.argv[1] if len(sys.argv) > 1 else "all"
    if phase in ("a", "all"):
        st = phase_a(st)
    if phase in ("b", "all"):
        st = phase_b(st)
    print("DONE phase", phase, flush=True)
