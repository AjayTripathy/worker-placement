"""new_issue_watch — alert on UPCOMING CA muni new issues that FIT our hold-to-maturity book, so we can
buy the retail order period at par (cleaner pricing + better after-tax than seasoned secondary).

THE ENGINE (the durable value): given a list of upcoming deals (issuer, type, $ amount, sale date), it
  1. classifies the sector (reuses cdiac_draws.sector + direct keyword detection)
  2. routes to one of three dispositions:
       FIT   — the INSULATED CORE: CA school/CC-district GO + essential-service water/utility revenue
               (AI-insulated, money-good to par) — buy the retail order period.
       REACH — the VALIDATED CREDIT-SPREAD sectors from the gauntlet (DD-pending, tagged by tier):
               RPTTF-residential tax-allocation · Cal-Mortgage-insured CCRC · system hospital ·
               cleared-CMO charter · university general revenue. These need per-name DD before funding,
               but a NEW ISSUE is the place to catch the concession (esp. Cal-Mortgage CCRC, which has
               essentially no secondary market — see the Sequoia Living 2025A lesson).
       EXCLUDE/SKIP — the traps: tobacco, COP/lease, CFD/Mello-Roos, POB, State GO (uncompensated AI),
               uninsured single-site CCRC/charter.
  3. cross-references our VETTED issuer universe (DD'd book + scanner want-list) for instant confidence
  4. pre-vets: AI-insulation by pledge; for utility, runs the first-principles supply authority.

CALENDAR SOURCE (pluggable): --calendar FILE (broker CA muni new-issue calendar CSV/JSON), or the
  EMMA New Issue Calendar scraped to data/ca_newissue_calendar.csv (see scrape_emma_newissues.py).

Output: outputs/NEW_ISSUE_ALERTS.{md,json}.  Cron-able; never trades.
  python new_issue_watch.py [--calendar deals.csv|deals.json] [--days 45]
"""
import csv, datetime, json, os, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "outputs"
TODAY = datetime.date(2026, 6, 23)

try:
    import cdiac_draws as CD          # reuse the sector classifier
    SECTOR = CD.sector
except Exception:
    def SECTOR(iss, name, proj):
        s = " ".join(x or "" for x in (iss, name, proj)).lower()
        if re.search(r"cfd|mello|facilities district|assessment", s): return "Land-secured (CFD/Mello-Roos/AD)"
        if re.search(r"school|unified|elementary|high school|usd\b|college", s): return "School/education"
        if re.search(r"water|irrigation|utilit|sewer|power|electric", s): return "Water/utility"
        if re.search(r"redevelop|tax alloc|successor", s): return "RDA/TAB"
        if re.search(r"state of california", s): return "State GO"
        return "Other/revenue"

INSULATED = {"School/education", "Water/utility"}
# structure words that ALWAYS disqualify (uncompensated / wrong pledge). NOTE: tax-allocation/successor
# is NO LONGER here — the gauntlet validated residential RPTTF as the cleanest credit-spread reach, so it
# routes to REACH-RPTTF instead. Bare "certificates" dropped too (would false-exclude CHFFA insured rev).
_HARD_EXCLUDE = re.compile(r"(\bcops?\b|certificates?\s+of\s+particip\w*|lease\s*rev(?:enue)?|"
                           r"installment\s+sale|mello|\bcfd\b|community\s+facilit|"
                           r"assessment\s+(?:dist|bond|rev)|pension\s+oblig|\bpob\b|tobacco)", re.I)
_CAB = re.compile(r"capital\s+appreciation|\bcabs?\b", re.I)   # accreting/zero-coupon — wrong for an income ladder
_STATE = re.compile(r"state of california|\bca st\b|public works board", re.I)

# --- REACH-tier detection (this session's validated credit-spread sectors) ---
_RPTTF   = re.compile(r"tax\s+alloc|successor\s+agenc|redevelop|tax\s+increment|\brda\b", re.I)
_CCRC    = re.compile(r"continuing\s+care|retirement\s+(?:community|residence|housing)|senior\s+living|"
                      r"life\s*care|\bccrc\b|congregational\s+home|elder\s*care", re.I)
_CALMORT = re.compile(r"cal[-\s]?mortgage|cal[-\s]?mtg|\bhcai\b|insured", re.I)  # the wrap signal
_CHFFA   = re.compile(r"\bchffa\b|health\s+facilities\s+financing", re.I)        # the CCRC/health conduit
_HOSP    = re.compile(r"hospital|health\s*care|healthcare|health\s+system|medical\s+center|"
                      r"health\s+facilit", re.I)
_SYSHOSP = re.compile(r"\bsystem\b|sutter|kaiser|stanford|el\s+camino|cedars|providence|dignity|"
                      r"scripps|sharp|memorialcare|ucsf|uc\s+\w+\s+health|adventist|cottage", re.I)
_CHARTER = re.compile(r"charter|academ(?:y|ies)", re.I)
_CMO     = re.compile(r"aspire|\bkipp\b|summit\s+public|classical\s+academ|green\s+dot|"
                      r"alliance\s+college|river\s+springs|ross\s+valley|rocketship", re.I)
_UNIV    = re.compile(r"\bregents\b|university of calif|california state univ|\bcsu\b|\bcsus\b|"
                      r"trustees\s+of\s+the\s+california", re.I)


def _vetted_universe():
    """Issuer names we've already cleared (DD'd book + scanner want-list) -> a new series from one is high-
    confidence. Returns {normalized_issuer_token_set}."""
    names = set()
    for f in ("outputs/DILIGENCE_MASTER.json", "outputs/SCANNER_STANDING_WANTLIST.json"):
        try:
            for r in json.load(open(HERE / f)):
                n = r.get("issuer") or r.get("district") or ""
                if n:
                    names.add(n)
        except Exception:
            pass
    return names


def _tok(s):
    # strip generic entity words AND bond-deal words, leaving the distinctive PLACE name
    stop = {"city", "of", "the", "district", "districts", "unified", "school", "elementary", "high", "union",
            "joint", "water", "municipal", "authority", "ccd", "college", "community", "and", "county",
            "general", "obligation", "refunding", "bonds", "bond", "series", "election", "revenue",
            "certificates", "participation", "capital", "appreciation", "interest", "current", "taxable",
            "exempt", "notes", "note", "improvement", "financing", "project", "various", "purpose",
            "services", "service", "facilities", "anticipation", "refunding"}
    return set(t for t in re.findall(r"[a-z]+", (s or "").lower()) if t not in stop and len(t) > 2)


def fetch_cdiac_proposed(days=60):
    """Best-effort: pull CDIAC proposed/upcoming sales from DebtWatch. The open API currently exports only
    the 'draws' dataset; proposed-debt sits behind the portal SPA query. Returns ([], status) when the
    forward feed isn't reachable — the caller then relies on --calendar. NEVER fabricates a calendar."""
    import urllib.request as u
    UA = {"User-Agent": "Mozilla/5.0 Chrome/124.0", "Accept": "application/json"}
    for ds in ("proposeddebt", "proposed", "proposed-sales", "issuance"):
        try:
            r = u.urlopen(u.Request(f"https://debtwatch.treasurer.ca.gov/api/dataset/{ds}/export/tabular",
                                    headers=UA), timeout=60)
            rows = json.loads(r.read()).get("rows", [])
            if rows:
                return rows, f"CDIAC DebtWatch '{ds}' ({len(rows)} rows)"
        except Exception:
            continue
    return [], ("CDIAC forward feed not openly exported (only 'draws'); use --calendar with your broker's "
                "CA muni new-issue calendar (Fidelity/Schwab/Vanguard) or the EMMA New Issue Calendar scrape.")


def load_calendar(path):
    """Load a broker-exported calendar. Accepts JSON (list of dicts) or CSV. Maps common column names to
    {issuer, deal_name, sale_date, amount, dtype}."""
    p = Path(path)
    raw = json.load(open(p)) if p.suffix.lower() == ".json" else list(csv.DictReader(open(p)))
    deals = []
    for r in raw:
        g = lambda *ks: next((r[k] for k in ks if k in r and r[k]), None)
        deals.append({
            "issuer": g("issuer", "Issuer", "issuer_name", "obligor", "Issuer Name"),
            "deal_name": g("deal_name", "description", "Description", "issue_name", "Issue", "name") or "",
            "sale_date": g("sale_date", "Sale Date", "date", "Date", "expected_sale") or "",
            "amount": g("amount", "Amount", "par", "Par", "principal", "size") or "",
            "dtype": g("type", "Type", "security", "Security", "debt_type", "pledge") or "",
            "tax_status": g("tax_status", "Tax Status", "taxstatus") or "",
        })
    return deals


def _core_score(deal, blob, sec, known, is_cab):
    """The original insulated-core path: school GO / water-utility revenue -> FIT/REVIEW, tier CORE."""
    notes = []
    if sec == "School/education":
        is_go = re.search(r"general obligation|\bgo\b|unlimited|ad valorem|bond", blob, re.I) and not _HARD_EXCLUDE.search(blob)
        notes.append("CA school/CC GO — AI-insulated (local property tax, not State cap-gains)" if is_go
                     else "confirm UNLIMITED ad-valorem GO (vs COP/lease) on the POS")
        if is_cab:
            notes.append("⚠ deal includes Capital Appreciation Bonds (accreting/zero-coupon) — for an income "
                         "ladder buy the Current Interest (CIB) series, not the CABs")
        fit = ("REVIEW" if is_cab else "FIT") if is_go else "REVIEW"
    else:  # Water/utility
        sup = None
        try:
            import sys as _s; _s.path.insert(0, str(HERE / "detectors"))
            import water_supply_authority as W
            sup = W.verify_supply(deal.get("issuer") or "", district=deal.get("issuer") or "", system_type="water")
        except Exception:
            pass
        if sup:
            notes.append(f"supply (first-principles): {sup['risk_level']} [{sup['confidence']}] — {sup['note'][:90]}")
            fit = "FIT" if sup["risk_level"] in ("low", "moderate") and not sup.get("import_dependent") else "REVIEW"
        else:
            notes.append("essential-service utility revenue — verify net-revenue pledge + supply on the POS")
            fit = "REVIEW"
    if known:
        notes.append("KNOWN-CLEAN ISSUER — already DD'd in the book/want-list; a new series is high-confidence")
        if fit == "REVIEW":
            fit = "FIT"
    return {"fit": fit, "tier": "CORE", "reach": False, "sector": sec, "known_issuer": known, "why": "; ".join(notes)}


def score(deal):
    iss, name, dt = deal.get("issuer") or "", deal.get("deal_name") or "", deal.get("dtype") or ""
    blob = f"{iss} {name} {dt}"
    sec = SECTOR(iss, name, dt)
    is_cab = bool(_CAB.search(blob))
    vetted = _vetted_universe()
    it = _tok(iss)
    known = any(vt and vt <= it for v in vetted for vt in (_tok(v),))

    # ---- HARD EXCLUDES (traps / uncompensated) ----
    if "taxable" in (deal.get("tax_status") or "").lower():
        return {"fit": "EXCLUDE", "tier": "TAXABLE", "reach": False, "sector": sec,
                "why": "federally TAXABLE — loses the CA double-exemption"}
    if _STATE.search(blob):
        return {"fit": "EXCLUDE", "tier": "STATE-GO", "reach": False, "sector": "State GO",
                "why": "State-GF / cap-gains exposed (the AI channel) — pays ~0bp over school GO, uncompensated"}
    if _HARD_EXCLUDE.search(blob):
        return {"fit": "EXCLUDE", "tier": "BAD-STRUCTURE", "reach": False, "sector": sec,
                "why": "trap pledge (COP/lease/CFD/Mello/POB/tobacco) — uncompensated or high-default"}

    # ---- VALIDATED CREDIT-SPREAD REACH (checked BEFORE the core, because these carry sector-classifier-
    #      confusing words — esp. "charter school"/"academy" which the classifier mislabels as School/GO
    #      and whose "...Revenue Bonds" trips the is_go check. Route them out first.) ----
    def reach(tier, why, fit="REVIEW"):
        if known and fit == "REVIEW":
            why += "; KNOWN-CLEAN issuer/obligor"
        return {"fit": fit, "tier": tier, "reach": True, "sector": sec, "known_issuer": known, "why": why}

    # Charter — FIRST (collides with school-GO). cleared-CMO only; single-site/unknown is a trap.
    if _CHARTER.search(blob) or re.search(r"\bcsfa\b|school\s+finance\s+authority", blob, re.I):
        if _CMO.search(blob) or known:
            return reach("REACH-CHARTER",
                         "established charter CMO — confirm renewal status/term + enrollment + DSCR + days-cash. "
                         "Funded by State per-pupil aid (Prop 98) → AI-4/5; a deferral can reach PAR for thin "
                         "cushion. SIZE IN THE AI BUDGET.")
        return {"fit": "SKIP", "tier": "CHARTER-SINGLE", "reach": False, "sector": "Charter (conduit)",
                "why": "single-site/unknown charter — high default; only gauntlet-cleared CMOs "
                       "(Aspire/Classical/Summit/River Springs) qualify."}
    # RPTTF tax-allocation — the cleanest reach (segregated lien, ~money-good)
    if _RPTTF.search(blob):
        return reach("REACH-RPTTF",
                     "RPTTF tax-increment — segregated lien (city-GF turmoil doesn't reach it; default≈0). "
                     "Confirm on POS: RESIDENTIAL/diversified increment (NOT tech-CRE), senior-lien, AV coverage. "
                     "Property-based → largely AI-insulated.")
    # CCRC / senior living — INSURED is the primary-market concession; uninsured is a trap
    if _CCRC.search(blob) or (_CHFFA.search(blob) and not _HOSP.search(blob)):
        if _CALMORT.search(blob) or _CHFFA.search(blob):
            return reach("REACH-CCRC-INSURED",
                         "Cal-Mortgage/CHFFA CCRC — the PRIMARY-MARKET concession (the Sequoia 2025A tell: "
                         "AA- state wrap priced cheap to rating, ~NO secondary market). CONFIRM Cal-Mortgage "
                         "on the POS + Type-A/obligated-group + occupancy/days-cash. Thin — buy the new issue, "
                         "cap at PAR (premium new-issue scales hide a yield-to-call).")
        return {"fit": "SKIP", "tier": "CCRC-UNINSURED", "reach": False, "sector": sec,
                "why": "uninsured CCRC/senior-living — highest-default sector; only mature nonprofit "
                       "obligated-groups underwritable. SKIP unless Cal-Mortgage-insured."}
    # Hospital — system (A-AA, ~money-good) vs district (Baa, needs strong DSCR)
    if _HOSP.search(blob):
        if _SYSHOSP.search(blob):
            return reach("REACH-HOSPITAL-SYSTEM",
                         "system hospital (A-AA) — ~money-good; ~5% is mostly curve not credit. Confirm "
                         "rating + days-cash on the POS. Asset-reserve/Bay-Area-employment AI tail (AI-2/3).")
        return reach("REACH-HOSPITAL-DISTRICT",
                     "district/standalone hospital — needs strong DSCR + days-cash; Medi-Cal payer mix is "
                     "State-GF funded (AI-3). REVIEW coverage/payer-mix on the POS before sizing.")
    # University general revenue (UC/CSU) — strong, modest state-approp exposure
    if _UNIV.search(blob):
        return reach("REACH-UNIVERSITY",
                     "university general revenue (UC/CSU) — strong, diversified; ~10% state-approp exposure "
                     "(AI-3, medical centers off-pledge). Confirm pledge breadth on the POS.")

    # ---- INSULATED CORE (only genuine school-GO / water-utility left after the reach routing) ----
    if sec in INSULATED:
        return _core_score(deal, blob, sec, known, is_cab)

    return {"fit": "SKIP", "tier": "OTHER", "reach": False, "sector": sec,
            "why": "outside the thesis (insulated core + validated credit-reach)"}


def main():
    days = int(sys.argv[sys.argv.index("--days") + 1]) if "--days" in sys.argv else 45
    cal_path = sys.argv[sys.argv.index("--calendar") + 1] if "--calendar" in sys.argv else None
    # standing drop-spot: export your broker's CA muni new-issue calendar here and the cron picks it up
    if not cal_path and (HERE / "data" / "ca_newissue_calendar.csv").exists():
        cal_path = str(HERE / "data" / "ca_newissue_calendar.csv")
    if cal_path:
        deals, src = load_calendar(cal_path), f"broker calendar: {cal_path}"
    else:
        rows, src = fetch_cdiac_proposed(days)
        deals = [{"issuer": r[1] if len(r) > 1 else "", "deal_name": r[2] if len(r) > 2 else "",
                  "dtype": r[12] if len(r) > 12 else "", "sale_date": "", "amount": r[13] if len(r) > 13 else ""}
                 for r in rows] if rows else []

    scored = []
    for d in deals:
        if not d.get("issuer"):
            continue
        scored.append({**d, **score(d)})
    fits = [x for x in scored if x["fit"] == "FIT"]                              # insulated core
    reach = [x for x in scored if x["fit"] == "REVIEW" and x.get("reach")]       # validated credit-reach
    reviews = [x for x in scored if x["fit"] == "REVIEW" and not x.get("reach")] # core, confirm on POS

    json.dump({"asof": TODAY.isoformat(), "source": src, "n_deals": len(scored),
               "fits": fits, "reach": reach, "reviews": reviews}, open(OUT / "NEW_ISSUE_ALERTS.json", "w"),
              indent=1, default=str)

    L = [f"# New-Issue Watch — CA Muni Book Fit ({TODAY})", "",
         f"_Source: {src}. Alerts on UPCOMING deals. **FIT** = insulated core (school-GO / water-utility), "
         f"buy the retail order period at par. **REACH** = validated credit-spread sectors from the gauntlet "
         f"(RPTTF-residential, Cal-Mortgage CCRC, system hospital, cleared-CMO charter, university) — "
         f"DD-pending, but the new issue is where the concession lives (esp. Cal-Mortgage CCRC = no "
         f"secondary market). Cap REACH bids at PAR; size charters/district-hospital in the AI budget._", ""]
    if not scored:
        L += ["**No calendar loaded.** To get live alerts:",
              "1. Scrape the EMMA New Issue Calendar (`scrape_emma_newissues.py`) → data/ca_newissue_calendar.csv, or",
              "2. Export your broker's **CA muni new-issue calendar** (Fidelity/Schwab/Vanguard) as CSV and run "
              "`python new_issue_watch.py --calendar yourfile.csv`.",
              "", "_The fit-engine (core + 6 reach tiers) is built and tested; it just needs the calendar rows._"]
    else:
        L += [f"**{len(fits)} FIT (core) · {len(reach)} REACH · {len(reviews)} REVIEW · {len(scored)} screened**", ""]
        if fits:
            L += ["## FIT — insulated core · buy the retail order period", "",
                  "| Issuer | Deal | Sale date | $ | Sector | Notes |", "|---|---|---|---|---|---|"]
            for x in fits:
                L.append(f"| {x['issuer']} | {str(x.get('deal_name'))[:30]} | {x.get('sale_date')} | "
                         f"{x.get('amount')} | {x['sector']} | {x['why'][:100]} |")
        if reach:
            L += ["", "## REACH — validated credit-spread sectors · DD-pending, catch the concession at issue", "",
                  "| Tier | Issuer | Deal | Sale date | $ | Notes |", "|---|---|---|---|---|---|"]
            for x in sorted(reach, key=lambda r: r["tier"]):
                L.append(f"| **{x['tier'].replace('REACH-','')}** | {x['issuer']} | {str(x.get('deal_name'))[:26]} | "
                         f"{x.get('sale_date')} | {x.get('amount')} | {x['why'][:120]} |")
        if reviews:
            L += ["", "## REVIEW — core, confirm on the POS", "",
                  "| Issuer | Deal | Sale date | Why |", "|---|---|---|---|"]
            for x in reviews:
                L.append(f"| {x['issuer']} | {str(x.get('deal_name'))[:30]} | {x.get('sale_date')} | {x['why'][:110]} |")
    open(OUT / "NEW_ISSUE_ALERTS.md", "w").write("\n".join(L))
    print(f"new-issue watch: {len(scored)} screened -> {len(fits)} FIT, {len(reach)} REACH, {len(reviews)} REVIEW | source: {src[:55]}")
    print(f"  -> {OUT/'NEW_ISSUE_ALERTS.md'}")


if __name__ == "__main__":
    main()
