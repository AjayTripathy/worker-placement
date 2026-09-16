"""bank_consolidation_scanner — the SMALL-BANK CONSOLIDATION (acquiree) screen.

THESIS UNDER TEST (generator only — this module produces NO verdicts and NO orders):
a US bank M&A wave is running under the current regulatory climate, and the FSBW pattern
(a small clean thrift transacting at/near tangible book) is repeatable. We underwrite the
ACQUIREE side: sub-$1B-market-cap exchange-listed banks and thrifts trading at or below
TANGIBLE book, with clean credit, sitting in footprints where an active consolidator is
already buying.

WHY THIS IS A SEPARATE SCREEN FROM financials_screen.py:
  financials_screen ranks on P/B x ROE-consistency — it asks "is this a good bank cheap?".
  This screen asks a DIFFERENT question: "would an acquirer want this bank, and is the
  market pricing it below what an acquirer would pay?".  Those rank differently.  A
  mediocre-ROE bank with a pristine core-deposit franchise and a clean loan book is a
  BETTER acquiree than a high-ROE bank funded wholesale — the acquirer buys the deposits
  and re-underwrites the earnings.  So the score weights DEPOSIT QUALITY and CREDIT
  CLEANLINESS above profitability, and treats cheapness as cheapness-vs-TANGIBLE-book
  (the currency deals are actually struck in) rather than P/B.

HOUSE RULES CARRIED IN (financials cluster):
  * Rank on NET INCOME AVAILABLE TO COMMON and its TREND, not a preferred-inclusive
    frames average.  (The MBIN lesson: a preferred-inclusive 5yr-average ROE masked a 39%
    drop in common earnings.)
  * The P/B vs P/TBV gap is the TELL.  A large gap = goodwill/intangibles from prior
    acquisitions; those do NOT survive a deal (the acquirer pays for TANGIBLE book and
    writes its own goodwill).  A P/B-cheap, P/TBV-expensive bank is a FALSE positive here.
  * MI-style peak-cycle masking exists in banks too: earnings held up by RESERVE RELEASE
    (provision below charge-offs, ACL/loans falling while NCOs rise) is not durable
    earnings.  Flagged explicitly as `reserve_release_flag`, never silently credited.
  * SEC company_tickers maps PREFERRED / baby-bond tickers to the PARENT CIK.  A tiny
    preferred market cap over parent common equity manufactures a fake 0.2x P/TBV.  The
    universe filter drops non-common tickers by symbol shape and the P/B-vs-P/TBV
    divergence check catches survivors.

DATA (all free, all primary):
  1. UNIVERSE — Nasdaq screener API (via verticals.deep_value.universe), sector=Finance,
     industry in {Major Banks, Banks, Commercial Banks, Savings Institutions},
     market cap $100M-$1B, mapped ticker -> CIK via SEC company_tickers.json.
  2. CREDIT / DEPOSITS / CONCENTRATION — FDIC BankFind `financials` API, joined from the
     holdco to its insured bank subsidiary via the `NAMEHCR` (name of holding company)
     field on the FDIC `institutions` endpoint.  This is a REAL join, not a guess: the
     match is on a normalized holding-company name and any ambiguity resolves to
     UNRESOLVED rather than a silent pick (muni issuer-matcher hardening lesson).
     Call-report data is BANK level; holdco ratios differ — named, not hidden.
  3. TANGIBLE BOOK / EARNINGS — SEC XBRL companyfacts (audited), holdco level:
     StockholdersEquity - PreferredStockValue - Goodwill - IntangibleAssetsNetExcludingGoodwill,
     divided by dei:EntityCommonStockSharesOutstanding.  This is the number that matters,
     because FDIC EQ is the BANK's equity, not the holding company's.

SCORE (0-100, generator ranking only — a court decides anything):
    cheapness (35)  x  credit cleanliness (25)  x  deposit/funding quality (20)
                    x  acquirer-footprint overlap (15)  x  size/digestibility (5)

USAGE:
    python3 -m verticals.generators.bank_consolidation_scanner [--refresh] [--top N]

Writes verticals/generators/data/BANK_CONSOLIDATION.json.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from verticals.deep_value import universe as U  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
CACHE = os.environ.get(
    "BANKCONSOL_CACHE",
    "/private/tmp/claude-501/-Users-ajay-exalted-signalos/"
    "d8499fdc-9ae3-4aaf-b555-4b2b90e6f2fc/scratchpad/bankconsol",
)
OUT = os.path.join(DATA, "BANK_CONSOLIDATION.json")

FDIC = "https://api.fdic.gov/banks"
UA_FDIC = {"User-Agent": "Mozilla/5.0 (signalos desk research)"}
UA_SEC = {"User-Agent": "signalos-generators research 4tripathy@gmail.com"}

BANK_INDUSTRIES = {"Major Banks", "Banks", "Commercial Banks", "Savings Institutions"}

# Already held / already courted — EXCLUDED from intake per the task brief.
EXCLUDE = {"FSBW", "WAL", "MBIN", "VEL", "NMIH", "MTG"}

# Names in the universe that are ALREADY in an announced transaction.  A target under a
# signed deal is merger arbitrage, not a screen idea — the takeout has happened and the
# residual is deal-break risk, a different underwriting.  An acquirer is disqualified for
# the opposite reason: it is the consolidator, not the consolidated.
LIVE_DEALS = {
    "AFBI": ("TARGET", "Fidelity BancShares (N.C.) — announced 2026-03-30, $142.8M all cash"),
    "FNWD": ("TARGET", "First Financial Bancorp (FFBC) — announced 2026-07-21, all stock, 1.40x TBV"),
    "BSBK": ("ACQUIRER", "acquiring GSL Savings Bank — announced 2026-05-31"),
    "IBCP": ("ACQUIRER", "acquiring Highpoint Community Bank — announced 2026-03-18, 1.48x TBV"),
    "CBAN": ("ACQUIRER", "acquiring First Reliance Bancshares — announced 2026-06-24, 1.62x TBV"),
    "ISBA": ("ACQUIRER", "acquiring Grand River Commerce — announced 2026-06-11"),
    "HWBK": ("ACQUIRER", "acquiring FSC Bancshares — announced 2026-04-28"),
    "BSVN": ("ACQUIRER", "acquiring ~71% of Century Financial Services — announced 2026-07-01"),
    "ESQ":  ("ACQUIRER", "acquiring Signature Bank (private) — announced 2026-03-11, 1.53x TBV"),
}

# FDIC call-report fields.  The default financials payload is the RATIO flavour; the
# dollar-level concentration inputs (LNRECONS / LNRENRES / LNREMULT / RBC / BRO / LNATRES)
# must be requested explicitly or they come back absent.
FIN_FIELDS = ",".join([
    "CERT", "REPDTE", "NAME", "STALP", "CITY", "PARCERT",
    "ASSET", "EQ", "EQTOT", "INTAN", "NETINC",
    "DEP", "DEPDOM", "DEPINS", "DEPUNINS", "DEPNIDOM", "COREDEP", "BRO",
    "LNLSNET", "LNATRES", "LNATRESR", "LNLSDEPR",
    "NCLNLSR", "NCRECONR", "NCRENRER", "NCRER", "NPERFV", "NALTOT", "ORE",
    "NTLNLSR", "NTLNLS", "ELNATR",
    "LNRECONS", "LNRENRES", "LNREMULT", "LNRERES", "LNRE", "LNCI", "LNCON",
    "RBC", "RBCRWAJ", "IDT1RWAJR", "RBC1AAJ",
    "ROA", "ROE", "NIMY", "EEFFR", "NUMEMP", "SPECGRPDESC", "BKCLASS",
])

# ── holding-company name normalization ──────────────────────────────────────────────
# FFIEC/FDIC abbreviate holding-company names ("FS BCORP INC" = "FS Bancorp, Inc.").
# Expand the abbreviations on BOTH sides, then compare token sets.
ABBREV = {
    "BCORP": "BANCORP", "BNCORP": "BANCORP", "BANCORPORATION": "BANCORP",
    "BSHRS": "BANCSHARES", "BSHS": "BANCSHARES", "BCSHARES": "BANCSHARES",
    "BANCSHARE": "BANCSHARES",
    "FNCL": "FINANCIAL", "FINL": "FINANCIAL", "FIN": "FINANCIAL",
    "FNCLSVC": "FINANCIAL", "FNCLCORP": "FINANCIAL",
    "BK": "BANK", "BKS": "BANK", "BNK": "BANK",
    "SVGS": "SAVINGS", "SVG": "SAVINGS", "SVB": "SAVINGS",
    "NB": "NATIONAL", "NAT": "NATIONAL", "NATL": "NATIONAL", "NTNL": "NATIONAL",
    "CMNTY": "COMMUNITY", "CMTY": "COMMUNITY", "CMNTYBK": "COMMUNITY",
    "FED": "FEDERAL", "FDL": "FEDERAL",
    "AMER": "AMERICAN", "AMERN": "AMERICAN", "AM": "AMERICAN",
    "NTHRN": "NORTHERN", "NORTHRN": "NORTHERN", "STHRN": "SOUTHERN",
    "MTG": "MORTGAGE", "INTL": "INTERNATIONAL", "SVC": "SERVICE",
    "TR": "TRUST", "TRST": "TRUST", "INVT": "INVESTMENT",
    "1ST": "FIRST", "2ND": "SECOND", "3RD": "THIRD",
}
DROP_TOKENS = {
    "INC", "INCORPORATED", "CORP", "CORPORATION", "CO", "COMPANY", "COMPANIES",
    "THE", "LTD", "LLC", "LP", "PLC", "MHC", "NEW", "GROUP", "GRP",
    "HOLDING", "HOLDINGS", "HLDG", "HLDGS", "HOLDINGCO", "HC",
    "COMMON", "STOCK", "CLASS", "A", "B", "OF",
}

# State abbreviations: FDIC writes "PEOPLES BCORP OF NC INC" where the registrant is
# "Peoples Bancorp of North Carolina, Inc.".  Expand so the identity tokens line up.
STATE_EXPAND = {
    "AL": "ALABAMA", "AK": "ALASKA", "AZ": "ARIZONA", "AR": "ARKANSAS",
    "CA": "CALIFORNIA", "CO": "COLORADO", "CT": "CONNECTICUT", "DE": "DELAWARE",
    "FL": "FLORIDA", "GA": "GEORGIA", "HI": "HAWAII", "ID": "IDAHO",
    "IL": "ILLINOIS", "IN": "INDIANA", "IA": "IOWA", "KS": "KANSAS",
    "KY": "KENTUCKY", "LA": "LOUISIANA", "ME": "MAINE", "MD": "MARYLAND",
    "MA": "MASSACHUSETTS", "MI": "MICHIGAN", "MN": "MINNESOTA", "MS": "MISSISSIPPI",
    "MO": "MISSOURI", "MT": "MONTANA", "NE": "NEBRASKA", "NV": "NEVADA",
    "NH": "NEWHAMPSHIRE", "NJ": "NEWJERSEY", "NM": "NEWMEXICO", "NY": "NEWYORK",
    "NC": "NORTH CAROLINA", "ND": "NORTH DAKOTA", "OH": "OHIO", "OK": "OKLAHOMA",
    "OR": "OREGON", "PA": "PENNSYLVANIA", "RI": "RHODEISLAND",
    "SC": "SOUTH CAROLINA", "SD": "SOUTH DAKOTA", "TN": "TENNESSEE", "TX": "TEXAS",
    "UT": "UTAH", "VT": "VERMONT", "VA": "VIRGINIA", "WA": "WASHINGTON",
    "WV": "WEST VIRGINIA", "WI": "WISCONSIN", "WY": "WYOMING",
}

# Corporate-FORM tokens carry no identity: "First Guaranty Bancshares" (the registrant)
# and "First Guaranty Bank" (the FDIC-insured subsidiary) are the same franchise.  These
# are stripped only in the LAST-RESORT match tier, where uniqueness is still required.
FORM_TOKENS = {
    "BANK", "BANKS", "BANCORP", "BANCSHARES", "BANKSHARES", "BANCORPORATION",
    "FINANCIAL", "FINANCE", "SAVINGS", "TRUST", "BANCO", "BANKING", "FEDERAL",
    "NATIONAL", "STATE", "SERVICES", "SERVICE",
}

# Non-common tickers.  SEC company_tickers maps preferred / depositary / baby-bond
# symbols to the PARENT CIK -> a tiny preferred market cap over parent common equity
# manufactures a fake sub-book valuation.  Drop them by NAME, up front; do not rely on
# a downstream join failing to catch them.  (The FRMEP lesson.)
NONCOMMON_MARKERS = (
    "depositary share", "preferred", "subordinated note", "notes due",
    "capital trust", "% fixed", "fixed rate", "fixed-rate", "fixed-to-floating",
    "warrant", "right", "unit", "american depositary", "cumulative",
    "senior note", "debenture", "trust preferred",
)


def _norm_tokens(name: str) -> tuple:
    s = (name or "").upper()
    s = s.replace("&", " AND ")
    s = re.sub(r"[^A-Z0-9 ]", " ", s)
    toks = []
    for t in s.split():
        t = ABBREV.get(t, t)
        t = STATE_EXPAND.get(t, t)
        for sub in t.split():                 # state expansion can emit two tokens
            if sub in DROP_TOKENS:
                continue
            toks.append(sub)
    return tuple(toks)


def _key(name: str) -> str:
    return " ".join(_norm_tokens(name))


def _identity(name: str) -> frozenset:
    """Distinctive tokens only — corporate FORM stripped.  Last-resort match key."""
    return frozenset(t for t in _norm_tokens(name) if t not in FORM_TOKENS)


def is_common_ticker(row) -> bool:
    n = (row.get("name") or "").lower()
    if any(m in n for m in NONCOMMON_MARKERS):
        return False
    if len(row.get("sym", "")) > 4:           # 5-letter Nasdaq symbols are pref/when-issued
        return False
    return True


# ── http ────────────────────────────────────────────────────────────────────────────
def _get_json(url, hdrs, timeout=60, retries=3):
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers=hdrs)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode())
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(0.8 * (i + 1))
    return {"_error": str(last)[:160]}


def _cache_path(name):
    os.makedirs(CACHE, exist_ok=True)
    return os.path.join(CACHE, name)


def _cached(name, fn, refresh=False):
    p = _cache_path(name)
    if not refresh and os.path.exists(p):
        with open(p) as f:
            return json.load(f)
    v = fn()
    with open(p, "w") as f:
        json.dump(v, f)
    return v


PREMISE_CORRECTIONS = [
    {
        "premise": "The FSBW pattern is 'a small clean thrift acquired at a premium — PacWest deal, vote Aug-13' and is repeatable on the acquiree side.",
        "finding": "INVERTED. FS Bancorp is the ACQUIRER, not the acquiree. FSBW is buying Pacific "
                   "West Bancorp (PWBK, West Linn OR, $386M assets, four branches) for ~$34.6M in "
                   "stock and cash, announced 2026-02-25; the Aug-13 vote is PWBK's shareholders, "
                   "not FSBW's. FSBW holders do not vote at all.",
        "authority": "FSBW Form 8-K Ex-99.1 2026-02-25; Form 424B3 dated 2026-07-15 (Reg. No. 333-297108); "
                     "verified negatives across EDGAR Jan-2025 to Aug-2026 — zero SC 13D, zero SC TO-T / "
                     "SC 14D9 / SC 13E3, and no PREM14A or S-4 naming FS Bancorp as a target.",
        "consequence": "The screen cannot be built as 'find the next FSBW acquiree'. It is built instead "
                       "on what the transaction actually demonstrates.",
    },
    {
        "premise": "The comparable transaction was struck at a PREMIUM.",
        "finding": "REFUTED. Raymond James' implied merger multiples put FSBW/PWBK at 0.97x tangible "
                   "book, 53.7x LTM earnings, and a NEGATIVE 0.3% core-deposit premium — a BELOW-book "
                   "price, against a 2026 YTD market median of ~1.52x TBV. PWBK sold at book because "
                   "its credit was impaired (NPLs 2.92% of loans, up from 0.33% in Dec-2024; ACL/NPLs "
                   "41.8%) and it earned $155k in Q1-26.",
        "authority": "424B3 acc 0001437749-26-023631 (fairness-opinion comparable-multiples section); "
                     "Mercer Capital Bank Watch July 2026 per S&P Global MI for the 1.52x median.",
        "consequence": "The real pattern is the OPPOSITE of the brief's: an IMPAIRED sub-scale bank sold "
                       "at book to a clean in-market buyer. The premium multiples (1.5x-2.0x) went to "
                       "CLEAN franchises. So 'cheap vs tangible book' and 'clean credit' are not one "
                       "signal — they are in tension, and the screen must say which it is buying.",
    },
    {
        "premise": "A bank M&A wave is running.",
        "finding": "PARTIALLY REFUTED. H1-2026 ran 83 deals against 117 in H2-2025; FY2025 was 188 and "
                   "FY2024 was 128. 2026 is above 2023-24 and marginally above H1-2025, but well below "
                   "the H2-2025 surge that generated the wave forecasts, and 87% of H1-2026 deal VALUE "
                   "was announced before Feb-28 — March through June produced only $2.3B.",
        "authority": "Seaport Research Partners via American Banker 2026-07-14; Mercer Capital Bank "
                     "Watch July 2026 per S&P Global MI (96 deals YTD as of 2026-07-30).",
        "consequence": "Elevated but DECELERATING, not accelerating. A takeout thesis should not be "
                       "sized on wave momentum.",
    },
    {
        "premise": "The regulatory climate has made approvals materially easier and faster.",
        "finding": "HALF VERIFIED. The RULE changes are real and citable: the OCC rescinded its 2024 "
                   "Business Combinations rule (90 FR 20561, eff. 2025-05-15), restoring 15-day deemed "
                   "approval and the streamlined application; the FDIC rescinded its 2024 Statement of "
                   "Policy (90 FR 29413, eff. 2025-08-04); and the OCC's Community Bank Licensing rule "
                   "(91 FR 10491, eff. 2026-04-03) creates streamlined merger procedures where the "
                   "RESULTING entity is under $30B — which is precisely this cohort. There have been "
                   "zero Federal Reserve merger denials in 2024, 2025 and 2026 YTD. But the claimed "
                   "SPEED improvement is NOT verifiable: the Fed's Banking Applications Activity "
                   "Semiannual Report stops at period-ending 2024-12-31, ~19 months late, so there is "
                   "NO published federal median-days-to-approval for 2025 or 2026 from any agency.",
        "authority": "Federal Register citations above; absence of any Fed applications-activity "
                     "edition covering 2025-2026.",
        "consequence": "Treat 'faster approvals' as UNVERIFIED rather than established. The Fed made no "
                       "Regulation Y change at all — that leg is rhetorical.",
    },
]

KEY_FINDINGS = [
    {
        "finding": "STRUCTURAL ACQUIRABILITY IS THE DOMINANT SCREEN AXIS, AND IT IS WHAT MAKES THE "
                   "CHEAPEST NAMES CHEAP.",
        "detail": "A screen that ranks on 'below tangible book with clean credit' surfaces recently "
                  "converted and MHC-controlled thrifts at the very top BY CONSTRUCTION: a mutual-to-"
                  "stock conversion raises capital into a small balance sheet, so the bank is over-"
                  "capitalised (which depresses ROE) and trades below tangible book. But federal law "
                  "makes exactly those institutions un-acquirable. 12 CFR 192.500 bars any acquisition "
                  "of more than 10% of a converted institution for THREE YEARS after conversion without "
                  "prior regulatory approval; and where a mutual holding company still owns a majority, "
                  "no third party can buy the company at all unless the MHC first elects a second-step "
                  "conversion — a decision belonging to the MHC board, not to public shareholders, who "
                  "hold a minority that cannot deliver control. The discount is therefore not a "
                  "mispricing an acquirer can arbitrage; it is the market correctly pricing a blocked "
                  "takeout. 12 of 129 names (9%) are blocked or unverified on this axis, and they were "
                  "concentrated at the TOP of the unadjusted ranking — Rhinebeck Bancorp (RBKB) ranked "
                  "#1 in the universe before the gate was applied and its own 10-K discloses that "
                  "Rhinebeck Bancorp, MHC owns 57%.",
        "method": "Each registrant's own latest 10-K read directly from EDGAR (the 10-Q usually omits "
                  "the structure disclosure — reading quarterlies missed Rhinebeck, Pioneer and Bogota "
                  "entirely). Present-tense MHC majority-ownership language is decisive and overrides "
                  "conversion language elsewhere in the document.",
    },
    {
        "finding": "THE HEADLINE TAKEOUT MULTIPLE DOES NOT APPLY TO THIS COHORT — AND ON THE "
                   "CORRECT COMPARABLE, MOST OF THESE BANKS ALREADY TRADE ABOVE IT.",
        "detail": "The ~1.46x-1.52x median deal multiple everyone quotes is the ALL-DEALS median, "
                  "dominated by high-performing private commercial banks in growth markets and by "
                  "large-cap transactions. Rebuilt on the 18-month tape restricted to LISTED targets "
                  "under ~$1.5B of market cap, the median falls to 1.24x — and the tape splits "
                  "cleanly by target TYPE rather than by geography or timing: THRIFT-CHARTER AND "
                  "LOW-ROE TARGETS CLEARED AT 0.77x-1.06x TANGIBLE BOOK, while high-performing "
                  "commercial banks in growth markets cleared at 1.50x-2.26x. The realised prints "
                  "for the type screened here are Fulton/Blue Foundry 0.77x (NJ), OceanFirst/"
                  "Flushing 0.80x (NY), FirstSun/First Foundation 0.80x, Columbia Financial/"
                  "Northfield 0.87x (NJ), FFBC/BankFinancial 0.91x (IL), NB Bancorp/BankProv 0.93x "
                  "(MA), FSBW/PWBK 0.97x (OR), CNB/ESSA 0.99x (PA), Columbia Banking/Pacific "
                  "Premier 0.99x (CA), Eastern/HarborOne 1.00x (MA), Richmond Mutual/Farmers 1.00x "
                  "(IN), Home Bancshares/Mountain Commerce 1.05x (TN), Norwood/PB Bankshares 1.07x "
                  "(PA). Against that band, this universe's MEDIAN traded multiple is 1.41x. The "
                  "typical listed small bank therefore trades ABOVE what its own comparables "
                  "actually receive, which makes a takeout a DOWNSIDE event for most of the cohort "
                  "rather than an upside catalyst. Only names below roughly 1.05x tangible book "
                  "have any headroom to the realised band; only names below ~0.90x have a genuine "
                  "margin. Two of the ten intake names (PROV 0.88x, RVSB 0.91x) sit inside that "
                  "margin on a clean credit book, and two more (FNWB 0.685x, BCBP 0.574x) sit well "
                  "below it but carry the credit questions that explain the discount.",
        "compounding_factor": "Forvis Mazars' 2025 REGIONAL averages put the NORTHEAST at 1.03x "
                              "against Southeast 1.63x and West 1.51x. Four intake names sit in "
                              "NJ/MA, where the regional gradient COMPOUNDS the target-type discount "
                              "instead of offsetting it.",
        "authority": "18 listed sub-$1.5B targets with reported multiples from the 2025 primary deal "
                     "map (The Bank Slate deal stories, acquirer 8-K/425 investor decks, ABA Banking "
                     "Journal), cross-checked to S&P Global DV/TCE where both exist; regional "
                     "averages from Forvis Mazars Q4-2025.",
        "consequence": "This is the finding that most changes how the screen should be used. It is "
                       "not a list of banks about to be bought at a premium. It is a list of banks "
                       "whose standalone value must carry the position, with a takeout as a "
                       "roughly-at-book exit rather than a payday.",
    },
    {
        "finding": "CREDIT UNIONS AND MUTUALS ARE THE MARGINAL HIGH BIDDER, AND THEY BUY DIFFERENTLY.",
        "detail": "16 credit-union-buys-bank deals were announced in 2025 (down from 20-22 in 2024), "
                  "and mutual holding companies such as Hometown Financial Group and Cambridge "
                  "Financial Group were active all window. Both classes pay CASH and face neither an "
                  "EPS-accretion nor a tangible-book-dilution constraint, which is precisely why "
                  "MIDFLORIDA CU cleared 2.16x for Prime Meridian and Cambridge paid 1.28x cash for "
                  "First Seacoast while listed acquirers were paying 0.8x-1.1x for comparable "
                  "thrifts. Where a target sits in a state that permits CU acquisitions of banks and "
                  "has an active CU or mutual buyer, the realistic upside multiple is materially "
                  "higher than the listed-acquirer comparables imply. This is a per-name question a "
                  "court should ask, not something the screen can score.",
    },
    {
        "finding": "THERE IS NO BROAD DISCOUNT TO TAKEOUT VALUE IN THIS COHORT.",
        "detail": "Median P/TBV across the 127 valued names is 1.41x against a 2026 YTD median takeout "
                  "multiple of ~1.52x. The typical small listed bank already trades at roughly 93% of "
                  "what the median deal pays, before any control premium is negotiated and before deal "
                  "risk and time value. Only 19 of 127 names (15%) trade below 1.0x tangible book, and "
                  "30 below 1.15x. Any edge lives in that tail, not in the cohort.",
        "method": "Universe P/TBV computed as market cap over holdco tangible common equity from tagged "
                  "10-Q balance-sheet data; deal median from Mercer/S&P (152%), corroborated by Piper "
                  "Sandler (141%) and by an independent 14-deal primary sample (~1.50x).",
    },
    {
        "finding": "THE CHEAP TAIL IS CHEAP FOR CREDIT REASONS — AND THAT IS THE PATTERN THAT ACTUALLY "
                   "TRANSACTED.",
        "detail": "Of the sub-1.0x names, the deepest discounts carry the worst credit: BCB Bancorp at "
                  "0.57x has NPAs of 1.98% of assets and charge-offs of 0.58%; First Internet at 0.72x "
                  "has charge-offs of 1.64% and negative returns; Eagle Bancorp at 0.78x has NPAs of "
                  "1.88%, charge-offs of 1.45% and 34% brokered funding. This is not a defect in the "
                  "screen — it is the same fact pattern as PWBK, which sold at 0.97x precisely because "
                  "its credit had deteriorated. So the honest framing of the trade is: you are paid a "
                  "discount to book to underwrite a credit book that an acquirer will re-mark, and the "
                  "takeout lands at ABOUT book, not at a premium.",
    },
    {
        "finding": "RESERVE RELEASE IS FLATTERING EARNINGS ACROSS THE COHORT (the MI peak-cycle pattern, "
                  "bank version).",
        "detail": "29 of 129 names (22%) are provisioning BELOW their charge-offs while the reserve "
                  "ratio falls year over year. That is borrowed earnings, and it is a specific hazard "
                  "for an acquiree thesis because an acquirer marks the loan book to fair value on day "
                  "one and gets no credit for a thin reserve. Flagged per name as reserve_release_flag; "
                  "never netted into the score as quality.",
    },
    {
        "finding": "THE FOOTPRINT SIGNAL IS REAL BUT THIN, AND IS ABSENT WHERE MANY OF THESE BANKS SIT.",
        "detail": "27 verified whole-bank deals were announced in 2026 YTD. New Jersey and New York "
                  "carry a direct and unusually cheap comparable — Columbia Financial's pending "
                  "acquisition of Northfield Bancorp at 0.86-0.89x TBV, the lowest 2026 print, which "
                  "caps as much as it supports a NJ/NY takeout case. The Pacific Northwest has two "
                  "in-market buyers actively transacting (Banner and FS Bancorp) plus Northrim buying "
                  "into Oregon. California has only one deal but a high-signal one: First Hawaiian "
                  "paying ~1.98x TBV to enter Northern California. Against that, Virginia, Pennsylvania, "
                  "Maryland and West Virginia carry large listed-bank counts with NO verified 2026 "
                  "in-state transaction — a takeout thesis there rests on hope rather than a "
                  "demonstrated bid, and those states score zero deliberately.",
    },
]

CASES = {'FNWB': 'First Northwest Bancorp (First Fed Bank, Port Angeles WA) — $2.12B assets, $109M market cap, 0.685x tangible book, the cheapest ACQUIRABLE name in the universe. WHY AN ACQUIRER WANTS IT: an 85% core-funded, 4% brokered, $1.61B deposit base across the Olympic Peninsula and Puget Sound, in the state where Banner Corp (Pacific Financial, 1.54x, Apr-2026) and FS Bancorp (Pacific West, Feb-2026) are both actively buying — an in-market buyer strips the 95.5% efficiency ratio and the franchise is worth far more inside a larger bank than standalone. WHY IT IS CHEAP: it is losing money — negative 2.87% return on tangible equity on a $4.6M TTM loss to common — and a bank that cannot earn its cost of capital standalone is the classic board-level sale candidate. CREDIT EVIDENCE: charge-offs are negligible at 0.037% of loans and OREO is $1.4M, but noncurrent loans are 1.33% and NPAs 1.09% of assets and RISING (up 0.15pp year over year) while the reserve ratio FELL 0.21pp to 1.03% — the reserve-release flag fires, coverage is only 78% of noncurrent loans, and construction is a non-issue at 29% of risk-based capital while total CRE is 338% (upper bound). THE COURT QUESTION: is the loss cyclical or is the credit book about to demand the reserve back.', 'BCBP': "BCB Bancorp (BCB Community Bank, Bayonne NJ) — $3.27B assets, $173M market cap, 0.574x tangible book, the single cheapest name in the universe. WHY AN ACQUIRER WANTS IT: a $2.67B deposit base in the Hudson County/NYC-metro corridor, 81% core and only 3% brokered, at a 60.7% efficiency ratio — and New Jersey has the most direct comparable in the country right now in Columbia Financial's pending acquisition of Northfield Bancorp. WHY IT IS CHEAP: earnings have collapsed — $2.5M to common on a TTM basis, down 42% year over year, a 0.82% return on tangible equity at a 70x P/E. CREDIT EVIDENCE — THIS IS THE BEAR CASE, NOT A FOOTNOTE: NPAs are 1.98% of assets and noncurrent loans 2.22%, charge-offs 0.58%, OREO $5.0M, and reserve coverage of noncurrent loans is only 55%, with the reserve ratio DOWN 0.52pp year over year while provisioning ran below charge-offs — the reserve-release flag fires hard. Uninsured deposits are 44.5%. The one genuine improvement is that NPAs fell 0.89pp year over year, so the credit cycle may have turned. NOTE A DATA GAP: bank-level risk-based capital came back empty from the call report, so the C&D and CRE concentration ratios and the tier-1 ratio could NOT be computed for this name — that is missing data, not a clean reading, and a court must pull them from the 10-Q. This is the PWBK template exactly: impaired credit, sells at or below book.", 'RVSB': 'Riverview Bancorp (Riverview Bank, Vancouver WA) — $1.46B assets, $108M market cap, 0.907x tangible book. WHY AN ACQUIRER WANTS IT: the best footprint fit in the screen. Vancouver WA is the Washington half of the Portland metro — the precise market where FS Bancorp just agreed to buy Pacific West Bancorp (West Linn OR, branches in Portland and Vancouver WA) and where Northrim is buying PBCO Financial in Medford OR. The deposit franchise is the asset: $1.26B of deposits, 95.3% core, ZERO brokered, 23.6% non-interest-bearing, and a loan/deposit ratio of only 85.5% — meaning an acquirer gets surplus funding it can lend against immediately. WHY IT IS CHEAP: it is loss-making, negative 3.66% return on tangible equity, a $4.3M TTM loss against a profit a year earlier. The gap between 0.74x book and 0.91x tangible book is goodwill that will not survive a transaction. CREDIT EVIDENCE: genuinely clean — NPAs 0.53% of assets, ZERO OREO, reserve at 1.40% of loans covering noncurrent loans 199%, tier-1 risk-based 14.4%. The blemishes are charge-offs at 0.41% and NPAs up 0.52pp year over year off a very low base, with the reserve-release flag firing on a 0.05pp reserve decline. Total CRE is 442% of risk-based capital (upper bound, includes owner-occupied) — above the 300% supervisory screen and the main thing a buyer would diligence.', 'PROV': 'Provident Financial Holdings (Provident Savings Bank FSB, Riverside CA) — $1.22B assets, $111M market cap, 0.877x tangible book. WHY AN ACQUIRER WANTS IT: it is the cleanest loan book in the entire universe and it sits in Inland Empire California, the state where First Hawaiian just agreed to pay ~1.98x tangible book to enter the market. Tier-1 risk-based capital is 19.0% — the bank is materially over-capitalised, so an acquirer is buying surplus capital at a 12% discount to its carrying value. WHY IT IS CHEAP: chronic under-earning. A 5.0% return on tangible equity at a 74% efficiency ratio on a sub-scale $1.2B balance sheet, and the funding is the weak point — only 9.6% non-interest-bearing, 15% brokered, 74% core, and a 114% loan/deposit ratio that means the bank is borrowing to lend. This is a thrift that has spent a decade unable to earn its cost of capital. CREDIT EVIDENCE — BEST IN SCREEN: NPAs 0.081% of assets, noncurrent loans 0.095%, ZERO charge-offs, ZERO OREO, reserve coverage 604% of noncurrent loans, no construction exposure at all, and NO reserve-release flag — the earnings are real, there just are not many of them. Converted to stock form in 1996, so no structural block. Total CRE 380% of risk-based capital is the one item to diligence.', 'RBB': 'RBB Bancorp (Royal Business Bank, Los Angeles CA) — $4.19B assets, $447M market cap, 0.988x tangible book, 10.9x earnings. WHY AN ACQUIRER WANTS IT: a Chinese-American commercial banking franchise spanning Los Angeles, New York and the Bay Area that would be extremely difficult and slow to build de novo, with a 51.9% efficiency ratio — the best cost structure among the cheap names — and tier-1 risk-based capital of 21.1%. California just printed a 1.98x out-of-market entry multiple. WHY IT IS CHEAP: the market is discounting the credit book and the niche concentration, not the earnings power — earnings to common are $41.0M, UP 28% year over year, a 9.06% return on tangible equity. The 0.85x P/B against 0.99x P/TBV shows goodwill that a buyer will not pay for. CREDIT EVIDENCE — MIXED, AND THE CRUX: NPAs are elevated at 1.17% of assets and noncurrent loans 1.34%, with $4.3M of OREO and reserve coverage of only 99% of noncurrent loans. But the direction is strongly favourable — NPAs DOWN 0.45pp year over year and charge-offs essentially nil at 0.0026% of loans, which says the problem loans are being resolved at par rather than written off. Against that, the reserve ratio fell 0.34pp and provisioning ran below charge-offs, so the reserve-release flag fires. Uninsured deposits are 47.2% and core funding only 74.5% — the funding profile is the weakest part of an otherwise strong case. Total CRE 249% of risk-based capital, the lowest concentration among the intake.', 'MGYR': "Magyar Bancorp (Magyar Bank, New Brunswick NJ) — $1.07B assets, $124M market cap, 0.997x tangible book, exactly at book. WHY AN ACQUIRER WANTS IT: a pristine, simple, in-fill New Jersey franchise with an 87.7% core-funded $885M deposit base and a 52.5% efficiency ratio — the second-best in the intake — on a balance sheet small enough for any regional buyer to absorb with cash. New Jersey has two active acquirers and the Columbia/Northfield comparable. WHY IT IS CHEAP: sub-scale and modestly profitable, a 6.15% return on tangible equity at 16x earnings with growth of only 3% year over year. CREDIT EVIDENCE — EFFECTIVELY SPOTLESS: NPAs 0.028% of assets, noncurrent loans 0.034%, NET RECOVERIES rather than charge-offs, ZERO OREO, reserve coverage of noncurrent loans 2,943%, NPAs down 0.23pp year over year, and NO reserve-release flag. There is essentially no credit mark for a buyer to take, which is exactly what supports a premium multiple rather than a book-value price. STRUCTURAL NOTE: Magyar completed a second-step mutual-to-stock conversion of Magyar Bancorp MHC — the 10-K treats it in the past tense with liquidation accounts established, and the registrant's SEC history dates to 2005, so the three-year prohibition has long expired; a court should still confirm the exact conversion date. Total CRE 460% of risk-based capital and 43% uninsured deposits are the two diligence items.", 'KRNY': 'Kearny Financial (Kearny Bank, Fairfield NJ) — $7.59B assets, $621M market cap, 0.957x tangible book, the largest acquirable name below tangible book. WHY AN ACQUIRER WANTS IT: scale. A $5.76B deposit franchise across northern New Jersey and the New York metro is the single biggest deposit base available in this cohort, 82.7% core-funded, and Columbia Financial — a New Jersey buyer — is simultaneously acquiring Northfield Bancorp, proving both appetite and regulatory feasibility for exactly this transaction shape. WHY IT IS CHEAP: a 2.25% net interest margin, the lowest in the intake, driving a 6.58% return on tangible equity with earnings to common DOWN 3.4% year over year — a liability-sensitive thrift balance sheet that has not repriced. The gap between 0.81x book and 0.96x tangible book is $100M-plus of goodwill from prior deals that an acquirer will write off and pay nothing for; this is the clearest illustration in the screen of why P/B flatters and P/TBV is the honest metric. CREDIT EVIDENCE: solid but not pristine — NPAs 0.69% of assets, noncurrent loans 0.90%, charge-offs negligible at 0.043%, ZERO OREO, tier-1 risk-based 13.7%, and NO reserve-release flag. The concerns are that NPAs rose 0.20pp year over year, reserve coverage is only 86% of noncurrent loans against a thin 0.77% reserve ratio — the lowest in the intake — and total CRE is 527% of risk-based capital. Second-step conversion completed 2015, so no structural block. THE CAVEAT: the direct NJ comparable, Columbia/Northfield, was struck at 0.86-0.89x tangible book, BELOW where Kearny trades — so the comparable caps the upside as much as it validates the thesis.', 'BCML': 'BayCom Corp (United Business Bank, Walnut Creek CA) — $2.63B assets, $329M market cap, 1.085x tangible book. WHY AN ACQUIRER WANTS IT: the deposit franchise is the best in the intake and it is what a buyer is actually paying for — 26.9% non-interest-bearing, 93.9% core, ZERO brokered, an 87.8% loan/deposit ratio and a 4.16% net interest margin, the highest in the screen. That is a genuine low-cost commercial deposit base across northern California, and California just printed a 1.98x entry multiple. WHY IT IS CHEAP: the returns do not match the franchise — a 1.81% return on tangible equity, $5.5M to common, 60x earnings. A bank with a great funding base and poor returns is the textbook acquiree, because the acquirer keeps the deposits and replaces the cost structure. CREDIT EVIDENCE: clean — NPAs 0.63% of assets, charge-offs essentially zero at 0.0029%, ZERO OREO, reserve coverage 125% of noncurrent loans, tier-1 risk-based 14.5%, and NO reserve-release flag; the reserve ratio actually ROSE 0.08pp, which is the opposite of borrowed earnings. Watch items: NPAs up 0.24pp year over year, uninsured deposits 46.3%, and total CRE at 537% of risk-based capital — the highest concentration in the intake and the main obstacle to a buyer.', 'SFBC': 'Sound Financial Bancorp (Sound Community Bank, Seattle WA) — $1.11B assets, $121M market cap, 1.105x tangible book. WHY AN ACQUIRER WANTS IT: a $975M Seattle-and-Olympic-Peninsula deposit base that is 89% core with ZERO brokered funding and only 20.3% uninsured — the lowest uninsured share in the intake and therefore the most stable, most valuable deposits on offer — in the state where Banner and FS Bancorp are both transacting. At $1.1B of assets it is a straightforward bolt-on for any Pacific Northwest buyer. WHY IT IS CHEAP: sub-scale economics — a 5.9% return on tangible equity at a 74.9% efficiency ratio and 18.7x earnings, growing 7% year over year. CREDIT EVIDENCE: clean and improving — NPAs 0.67% of assets, charge-offs 0.0083%, essentially no OREO at $0.1M, reserve coverage 118% of noncurrent loans, NPAs DOWN 0.23pp year over year, and NO reserve-release flag. DATA GAP: bank-level risk-based capital was not returned by the call report, so the C&D and CRE concentration ratios and the tier-1 ratio are UNAVAILABLE for this name — missing, not clean, and a court must source them from the 10-Q. This is the highest-quality-franchise, lowest-discount name in the intake: the case rests on franchise scarcity, not on cheapness.', 'WNEB': 'Western New England Bancorp (Westfield Bank, Westfield MA) — $2.76B assets, $260M market cap, 1.109x tangible book, 14.7x earnings. WHY AN ACQUIRER WANTS IT: western Massachusetts and northern Connecticut deposits — $2.38B, 89.5% core, ZERO brokered, 25.2% non-interest-bearing — in the New England market that is consolidating hardest right now: Hometown Financial Group MHC is a serial acquirer nine deals deep and just bought Primary Bank, Cambridge Financial Group is paying CASH for converted thrifts (First Seacoast at 1.28x), and Banco Santander is buying Webster Financial to enter the region at ~2.0x. Multiple buyer types, including mutuals that pay cash and do not care about EPS dilution. WHY IT IS CHEAP: a 2.98% net interest margin and a 67.9% efficiency ratio produce only a 7.56% return on tangible equity, though earnings to common are UP 16.2% year over year — the best earnings trend among the clean names. CREDIT EVIDENCE — SECOND-CLEANEST IN THE INTAKE: NPAs 0.168% of assets, noncurrent loans 0.211%, charge-offs 0.010%, ZERO OREO, reserve coverage 445% of noncurrent loans, NPAs down 0.05pp year over year, tier-1 risk-based 12.4%, and NO reserve-release flag. Construction is modest at 39% of risk-based capital; total CRE 386% (upper bound) is the diligence item. Of the ten, this is the one where clean credit, a real deposit franchise, improving earnings and a demonstrably active buyer set all line up at once — and correspondingly, it is not cheap.'}

# ── stage 1: universe ───────────────────────────────────────────────────────────────
def fetch_bank_universe(refresh=False):
    rows = _cached(
        "universe.json",
        lambda: U.fetch_universe(min_mcap=1e8, max_mcap=1e9, ex_financials=False),
        refresh,
    )
    out = []
    for r in rows:
        if r.get("sec") != "Finance" or r.get("ind") not in BANK_INDUSTRIES:
            continue
        if (r.get("country") or "United States") != "United States":
            continue
        if not is_common_ticker(r):
            continue
        out.append(r)
    return out


# ── stage 2: FDIC join ──────────────────────────────────────────────────────────────
def fetch_institutions(refresh=False):
    def _pull():
        out, off = [], 0
        while True:
            j = _get_json(
                f"{FDIC}/institutions?filters=ACTIVE:1&fields=CERT,NAME,CITY,STALP,ASSET,"
                f"NAMEHCR,RSSDHCR,BKCLASS,OFFDOM&limit=1000&offset={off}&format=json",
                UA_FDIC, timeout=120)
            rows = [d["data"] for d in j.get("data", [])]
            out += rows
            if len(rows) < 1000:
                break
            off += 1000
        return out
    return _cached("fdic_inst.json", _pull, refresh)


def build_hc_index(insts):
    """normalized holding-company name -> list of institution rows."""
    idx = {}
    for r in insts:
        hc = r.get("NAMEHCR")
        if not hc or hc in ("", "-"):
            continue
        idx.setdefault(_key(hc), []).append(r)
    return idx


def match_bank(row, hc_idx, inst_by_name):
    """Resolve a listed holdco to its insured bank subsidiary(ies).

    Order: exact normalized NAMEHCR -> exact normalized bank NAME (unit holdcos whose
    NAMEHCR is blank or differs) -> unique token-prefix match.  Ambiguity or no hit
    returns UNRESOLVED; we never silently pick.
    """
    key = _key(row["name"])
    if key in hc_idx:
        return hc_idx[key], "namehcr_exact"
    if key in inst_by_name:
        return inst_by_name[key], "bankname_exact"

    # token-prefix: every token of the shorter side prefix-matches the other, and the
    # first token matches exactly.  Require a UNIQUE hit.
    kt = _norm_tokens(row["name"])
    if not kt:
        return None, "unresolved_empty"
    cands = []
    for cand_key, rows in hc_idx.items():
        ct = tuple(cand_key.split())
        if not ct or ct[0] != kt[0]:
            continue
        n = min(len(ct), len(kt))
        if n < 1:
            continue
        ok = all(ct[i].startswith(kt[i]) or kt[i].startswith(ct[i]) for i in range(n))
        if ok and abs(len(ct) - len(kt)) <= 1:
            cands.append((cand_key, rows))
    if len(cands) == 1:
        return cands[0][1], "prefix_unique"
    if len(cands) > 1:
        return None, f"unresolved_ambiguous({len(cands)})"

    # LAST RESORT — distinctive-token identity, form stripped, against the holding-company
    # index and then the bank-name index.  This is what recovers registrants whose FDIC
    # NAMEHCR is a TOP-TIER family/ESOP holder rather than the listed intermediate holdco
    # (First Guaranty Bancshares -> NAMEHCR "SMITH&HOOD HOLDING CO L L C", bank name
    # "First Guaranty Bank").  Uniqueness is still mandatory: ambiguity -> UNRESOLVED.
    ident = _identity(row["name"])
    if ident:
        for idx, label in ((hc_idx, "identity_hc"), (inst_by_name, "identity_bankname")):
            hits = [rows for k, rows in idx.items() if _identity(k) == ident]
            if len(hits) == 1:
                return hits[0], label
            if len(hits) > 1:
                return None, f"unresolved_ambiguous_identity({len(hits)})"
    return None, "unresolved_nohit"


def sec_state(cik, refresh=False):
    """Registrant's business-address state, from SEC submissions.  Used ONLY to break
    holding-company name collisions — several unrelated holdcos abbreviate to the same
    FDIC NAMEHCR ("FS BCORP INC" is BOTH FS Bancorp of Mountlake Terrace WA and the
    Indiana holdco of Farmers State Bank).  A silent merge of the two would have assigned
    FSBW an Indiana bank's call report."""
    def _pull():
        j = _get_json(f"https://data.sec.gov/submissions/CIK{int(cik):010d}.json",
                      UA_SEC, timeout=60)
        if "_error" in j:
            return {"_error": j["_error"]}
        a = (j.get("addresses") or {}).get("business") or {}
        return {"state": a.get("stateOrCountry"), "city": a.get("city"),
                "sic": j.get("sic"), "name": j.get("name")}
    return _cached(f"secsub_{int(cik)}.json", _pull, refresh)


def sec_filings(cik, refresh=False):
    """Recent filing history + the registrant's first-ever filing date."""
    def _pull():
        j = _get_json(f"https://data.sec.gov/submissions/CIK{int(cik):010d}.json",
                      UA_SEC, timeout=60)
        if "_error" in j:
            return {"_error": j["_error"]}
        rec = (j.get("filings") or {}).get("recent") or {}
        rows = []
        for i in range(len(rec.get("form", []))):
            rows.append({"form": rec["form"][i], "date": rec["filingDate"][i],
                         "acc": rec["accessionNumber"][i],
                         "doc": rec.get("primaryDocument", [""] * (i + 1))[i]})
        older = (j.get("filings") or {}).get("files") or []
        first = min([r["date"] for r in rows] or ["9999"])
        if older:
            first = min(first, min(f.get("filingFrom", "9999") for f in older))
        return {"filings": rows, "first_filing": first,
                "n_older_pages": len(older)}
    return _cached(f"secfil_{int(cik)}.json", _pull, refresh)


def fetch_filing_text(cik, acc, doc, refresh=False):
    accn = acc.replace("-", "")
    key = f"doc_{int(cik)}_{accn}.txt"
    p = _cache_path(key)
    if not refresh and os.path.exists(p):
        with open(p, encoding="utf-8", errors="ignore") as f:
            return f.read()
    url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accn}/{doc}"
    try:
        req = urllib.request.Request(url, headers=UA_SEC)
        with urllib.request.urlopen(req, timeout=90) as r:
            raw = r.read().decode("utf-8", errors="ignore")
    except Exception as e:  # noqa: BLE001
        return f"__ERROR__ {e}"
    txt = re.sub(r"<[^>]+>", " ", raw)
    txt = re.sub(r"&nbsp;?", " ", txt)
    txt = re.sub(r"&amp;", "&", txt)
    txt = re.sub(r"\s+", " ", txt)
    with open(p, "w", encoding="utf-8") as f:
        f.write(txt)
    return txt


# ── the ACQUIRABILITY gate (Mode-B: the decisive question the screen's framing hides) ──
# A screen that ranks on "cheap vs tangible book + clean credit" surfaces recently-converted
# thrifts at the top BY CONSTRUCTION: a standard conversion raises capital into a small
# balance sheet, so the bank is over-capitalized (depressing ROE) and trades below tangible
# book.  But federal law makes exactly those institutions UN-ACQUIRABLE:
#   * 12 CFR 192.500(a) — for THREE YEARS after a standard mutual-to-stock conversion, no
#     person may acquire more than 10% of the converted institution's stock without prior
#     regulatory approval.  In practice this blocks a takeover for three years.
#   * MHC (mutual holding company) structure — the MHC holds a MAJORITY of the mid-tier
#     holdco's stock and is itself a mutual with no owners to sell.  No acquirer can buy
#     the company unless the MHC first does a second-step conversion, which is the MHC
#     board's unilateral decision, not the public shareholders'.
# So the cheapness is not a mispricing an acquirer can arbitrage — it is the market
# correctly pricing a structurally blocked takeout.  This gate is the difference between
# a real acquiree screen and one that just re-finds over-capitalized thrifts.
MHC_PATTERNS = [
    r"mutual holding company",
    r"\bMHC\b",
]
# Every pattern must be MUTUAL-specific.  A bare "conversion"/"stock offering" match fires
# on ordinary commercial-bank IPOs and on convertible-security language: Third Coast Bank
# (a Texas commercial bank that IPO'd in 2021, never a thrift) was misclassified as a
# recently converted mutual on exactly that.
CONVERSION_PATTERNS = [
    r"mutual[- ]to[- ]stock conversion",
    r"second[- ]step conversion",
    r"conversion (?:of|from) (?:the )?mutual (?:form|holding)",
    r"from the mutual form of organization to the stock form",
    r"mutual holding company reorganization",
]


MONTHS = {m: i + 1 for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july", "august",
     "september", "october", "november", "december"])}


def _extract_conversion_date(low: str):
    """Pull the stated conversion-completion date out of the registrant's own 10-Q.
    Preferred over the first-filing heuristic, which mis-dates second-step conversions
    (a second step creates a NEW registrant CIK, so 'first filing' reads as the
    conversion date only by luck)."""
    pats = [
        r"conversion[^.]{0,160}?(?:was\s+)?completed\s+(?:on\s+)?"
        r"([a-z]+)\s+(\d{1,2}),?\s+(\d{4})",
        r"completed[^.]{0,120}?(?:stock\s+)?(?:conversion|offering)[^.]{0,80}?"
        r"on\s+([a-z]+)\s+(\d{1,2}),?\s+(\d{4})",
        r"on\s+([a-z]+)\s+(\d{1,2}),?\s+(\d{4})[^.]{0,120}?"
        r"completed[^.]{0,120}?(?:conversion|stock offering)",
    ]
    for p in pats:
        for m in re.finditer(p, low):
            mo = MONTHS.get(m.group(1))
            if not mo:
                continue
            y = int(m.group(3))
            if 1990 <= y <= 2030:
                return f"{y:04d}-{mo:02d}-{int(m.group(2)):02d}"
    return None


def acquirability(cik, txt, first_filing, ipo_date=None):
    """Classify structural acquirability from the registrant's own latest 10-Q text."""
    out = {"mhc_language_hits": 0, "conversion_language_hits": 0,
           "structure": "stock_holdco", "blocked_reason": None,
           "first_sec_filing": first_filing}
    if not txt or txt.startswith("__ERROR__"):
        out["structure"] = "UNVERIFIED"
        out["blocked_reason"] = "10-Q text unavailable"
        return out
    low = txt.lower()
    out["mhc_language_hits"] = len(re.findall(r"mutual holding company|\bmhc\b", low))
    out["conversion_language_hits"] = sum(len(re.findall(p, low))
                                          for p in CONVERSION_PATTERNS)

    # Is there a LIVING mutual holding company above this registrant?  Two questions,
    # and only the pair is decisive:
    #   (a) does the filing describe an MHC / two-tier structure at all, and
    #   (b) has that MHC already been converted away (a completed "second-step")?
    # Magyar Bancorp's 10-K names "Magyar Bancorp, MHC" but only in the PAST tense of a
    # completed mutual-to-stock conversion — it is a fully public company.  Rhinebeck's
    # 10-K says "Rhinebeck Bancorp, MHC ... owns 57[%]" — the MHC is alive and controlling.
    # Reading (a) without (b) misclassifies every converted thrift as blocked.
    has_mhc = bool(re.search(r"mutual holding company|,\s*mhc\b", low))
    out["mhc_entity_present"] = has_mhc

    # ORDER MATTERS.  A PRESENT-TENSE statement that an MHC owns a majority is decisive and
    # OVERRIDES any conversion language elsewhere in the document — 10-Ks discuss possible
    # or historical conversions in risk factors and regulatory sections, so a "conversion"
    # match alone is not evidence the MHC is gone.  Phrasing varies and none of it uses the
    # word "outstanding" reliably: Rhinebeck says "is a mutual holding company that owns
    # 57.4%"; Pioneer says "MHC owns a majority of the Company's common stock"; Bogota says
    # "MHC owns a majority of Bogota Financial Corp".
    pct = None
    for p in (r"(?:,\s*mhc|mutual holding company)[^.]{0,240}?(?:owns?|holds?|held)"
              r"\s+(?:approximately\s+)?(\d{1,3}(?:\.\d+)?)\s*%",
              r"(\d{1,3}(?:\.\d+)?)\s*%[^.]{0,140}?(?:owned|held) by[^.]{0,100}?"
              r"(?:,\s*mhc|mutual holding company)"):
        m = re.search(p, low)
        if m:
            try:
                v = float(m.group(1))
                if 0 < v <= 100:
                    pct = v
                    break
            except ValueError:
                pass
    majority_words = bool(re.search(
        r"(?:,\s*mhc|mutual holding company)[\s\S]{0,240}?owns?\s+a majority of", low))
    mhc_controls = has_mhc and ((pct is not None and pct > 50) or majority_words)

    dissolved = bool(re.search(
        r"(?:completed|consummated|completion of)[^.]{0,200}?second[- ]step conversion|"
        r"(?:completed|consummated|completion of)[^.]{0,200}?mutual[- ]to[- ]stock conversion|"
        r"in connection with the (?:mutual[- ]to[- ]stock )?conversion of[^.]{0,80}?,\s*mhc",
        low)) and not mhc_controls
    out["mhc_converted_away"] = dissolved

    if mhc_controls:
        out["mhc_ownership_pct"] = pct if (pct is not None and pct > 50) else None
        out["structure"] = "MHC_majority"
        own = f"~{pct}%" if pct is not None else "a majority"
        out["blocked_reason"] = (
            f"a mutual holding company owns {own} of the shares. An MHC is a mutual with no "
            "shareholders to sell; no third party can acquire this company unless the MHC "
            "first completes a second-step conversion, which is the MHC board's decision "
            "alone. The public float is a MINORITY that cannot deliver control.")
    elif (re.search(r",\s*mhc\b", low) and not dissolved
          and out["mhc_language_hits"] >= 3):
        out["structure"] = "MHC_suspected"
        out["blocked_reason"] = ("repeated mutual-holding-company language with no "
                                 "completed second-step conversion found; ownership "
                                 "percentage not parsed — verify by hand")

    # 3-year post-conversion acquisition prohibition
    stated = _extract_conversion_date(low)
    conv = ipo_date or stated or (first_filing if first_filing and first_filing < "9999"
                                  else None)
    out["conversion_date"] = conv
    out["conversion_date_basis"] = ("stated_in_10Q" if (stated and not ipo_date)
                                    else "first_sec_filing_proxy")
    saw_conv = out["conversion_language_hits"] > 0
    if conv and conv >= "2023-08-02" and saw_conv:
        out["recent_conversion"] = True
        if out["structure"] == "stock_holdco":
            out["structure"] = "recent_conversion"
        out["blocked_reason"] = ((out.get("blocked_reason") or "").strip(" |") + " | " if
                                 out.get("blocked_reason") else "") + (
            f"mutual-to-stock conversion dated {conv} ({out['conversion_date_basis']}): "
            "12 CFR 192.500 bars any >10% acquisition of the converted institution for "
            "THREE YEARS from conversion without prior regulatory approval — a takeout is "
            f"structurally blocked until ~{int(conv[:4]) + 3}{conv[4:]}")
    out["acquirable"] = out["structure"] in ("stock_holdco", "UNVERIFIED")
    return out


def disambiguate(rec, rows):
    """A holdco may legitimately own several banks (same RSSDHCR -> aggregate).  Distinct
    RSSDHCRs under one normalized name = a NAME COLLISION between unrelated companies, and
    must be resolved, never merged.  Resolution order: registrant business-state, then
    balance-sheet size proximity (bank assets vs SEC-reported holdco assets).  If neither
    is decisive the record is marked ambiguous and its call-report data is withheld."""
    groups = {}
    for x in rows:
        groups.setdefault(x.get("RSSDHCR") or f"_cert{x['CERT']}", []).append(x)
    if len(groups) == 1:
        return rows, "single_holdco"

    st = (rec.get("_secsub") or {}).get("state")
    if st:
        hits = [g for g in groups.values() if any(y.get("STALP") == st for y in g)]
        if len(hits) == 1:
            return hits[0], f"collision_resolved_by_state({st})"

    holdco_assets = (rec.get("_sec") or {}).get("assets")
    if holdco_assets:
        target = holdco_assets / 1000.0          # FDIC ASSET is in $thousands
        scored = sorted(
            ((abs((sum(y.get("ASSET") or 0 for y in g) / target) - 1.0), k, g)
             for k, g in groups.items()), key=lambda z: z[0])
        if scored[0][0] < 0.35 and (len(scored) == 1 or scored[1][0] > 0.8):
            return scored[0][2], "collision_resolved_by_assets"

    return None, f"collision_UNRESOLVED({len(groups)}_holdcos)"


def fetch_financials(cert, n=6):
    j = _get_json(
        f"{FDIC}/financials?filters=CERT:{cert}&fields={FIN_FIELDS}"
        f"&sort_by=REPDTE&sort_order=DESC&limit={n}&format=json", UA_FDIC)
    if "_error" in j:
        return None
    return [d["data"] for d in j.get("data", [])]


# ── stage 3: SEC XBRL holdco tangible book + earnings ───────────────────────────────
EQ_TAGS = ["StockholdersEquity",
           "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"]
PFD_TAGS = ["PreferredStockValue", "PreferredStockValueOutstanding"]
GW_TAGS = ["Goodwill"]
INTAN_TAGS = ["IntangibleAssetsNetExcludingGoodwill", "FiniteLivedIntangibleAssetsNet"]
NIC_TAGS = ["NetIncomeLossAvailableToCommonStockholdersBasic"]
NI_TAGS = ["NetIncomeLoss"]


def _facts(cik):
    return _get_json(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{int(cik):010d}.json",
                     UA_SEC, timeout=90)


def _days(a, b):
    return (int(a[:4]) - int(b[:4])) * 365 + (int(a[5:7]) - int(b[5:7])) * 30 + \
           (int(a[8:10]) - int(b[8:10]))


def _latest_instant(facts, tags, as_of=None, max_stale_days=400):
    """Most recent point-in-time value across a tag preference list.

    DATE-MATCHING IS MANDATORY when `as_of` is given.  A filer can stop tagging a concept
    once the underlying instrument is gone, leaving the last-ever value stranded in
    companyfacts: Sierra Bancorp's most recent PreferredStockValue fact is dated
    2022-12-31 ($112.9M) while its equity is dated 2026-06-30.  Subtracting that stale
    preferred from current equity understated tangible common equity by $113M and made a
    cheap bank look expensive.  A component older than `max_stale_days` relative to the
    equity date is treated as NOT PRESENT and reported as such — never silently applied.

    Returns (val, end, tag, stale_flag).
    """
    us = (facts.get("facts") or {}).get("us-gaap") or {}
    for tag in tags:
        node = us.get(tag)
        if not node:
            continue
        cands = []
        for unit, arr in (node.get("units") or {}).items():
            if unit != "USD":
                continue
            for f in arr:
                if f.get("start"):          # instant facts have no start
                    continue
                end = f.get("end")
                if end:
                    cands.append((end, f.get("val")))
        if not cands:
            continue
        if as_of:
            exact = [c for c in cands if c[0] == as_of]
            if exact:
                return exact[0][1], exact[0][0], tag, False
            near = sorted([c for c in cands if 0 <= _days(as_of, c[0]) <= max_stale_days],
                          key=lambda c: c[0], reverse=True)
            if near:
                return near[0][1], near[0][0], tag, False
            newest = max(cands, key=lambda c: c[0])
            return None, newest[0], tag, True      # present but STALE -> not applied
        newest = max(cands, key=lambda c: c[0])
        return newest[1], newest[0], tag, False
    return None, None, None, False


def _ttm_flow(facts, tags):
    """Sum the most recent 4 non-overlapping ~quarterly durations. (val, end, tag, n)."""
    us = (facts.get("facts") or {}).get("us-gaap") or {}
    for tag in tags:
        node = us.get(tag)
        if not node:
            continue
        rows = []
        for unit, arr in (node.get("units") or {}).items():
            if unit != "USD":
                continue
            for f in arr:
                s, e, v = f.get("start"), f.get("end"), f.get("val")
                if not (s and e and v is not None):
                    continue
                days = (int(e[:4]) - int(s[:4])) * 365 + \
                       (int(e[5:7]) - int(s[5:7])) * 30 + (int(e[8:10]) - int(s[8:10]))
                if 60 <= days <= 110:       # quarterly only
                    rows.append((e, s, v))
        if not rows:
            continue
        rows = sorted({(e, s, v) for e, s, v in rows}, reverse=True)
        picked, cursor = [], None
        for e, s, v in rows:
            if cursor is None or e <= cursor:
                picked.append((e, s, v))
                cursor = s
            if len(picked) == 4:
                break
        if picked:
            return sum(v for _, _, v in picked), picked[0][0], tag, len(picked)
    return None, None, None, 0


def _prior_ttm_flow(facts, tags, before_end):
    us = (facts.get("facts") or {}).get("us-gaap") or {}
    for tag in tags:
        node = us.get(tag)
        if not node:
            continue
        rows = []
        for unit, arr in (node.get("units") or {}).items():
            if unit != "USD":
                continue
            for f in arr:
                s, e, v = f.get("start"), f.get("end"), f.get("val")
                if not (s and e and v is not None) or e >= before_end:
                    continue
                days = (int(e[:4]) - int(s[:4])) * 365 + \
                       (int(e[5:7]) - int(s[5:7])) * 30 + (int(e[8:10]) - int(s[8:10]))
                if 60 <= days <= 110:
                    rows.append((e, s, v))
        if not rows:
            continue
        rows = sorted({(e, s, v) for e, s, v in rows}, reverse=True)
        picked, cursor = [], None
        for e, s, v in rows:
            if cursor is None or e <= cursor:
                picked.append((e, s, v))
                cursor = s
            if len(picked) == 4:
                break
        if len(picked) == 4:
            return sum(v for _, _, v in picked)
    return None


def sec_book(cik, refresh=False):
    def _pull():
        f = _facts(cik)
        if "_error" in f:
            return {"_error": f["_error"]}
        eq, eq_end, eq_tag, _ = _latest_instant(f, EQ_TAGS)
        # every deduction is date-matched to the equity date; stale facts are NOT applied
        pfd, pfd_end, _, pfd_stale = _latest_instant(f, PFD_TAGS, as_of=eq_end)
        gw, gw_end, _, gw_stale = _latest_instant(f, GW_TAGS, as_of=eq_end)
        intan, in_end, _, in_stale = _latest_instant(f, INTAN_TAGS, as_of=eq_end)
        stale = [n for n, s in (("preferred", pfd_stale), ("goodwill", gw_stale),
                                ("intangibles", in_stale)) if s]
        nic, nic_end, nic_tag, nq = _ttm_flow(f, NIC_TAGS)
        if nic is None:
            nic, nic_end, nic_tag, nq = _ttm_flow(f, NI_TAGS)
        prior = _prior_ttm_flow(f, NIC_TAGS if nic_tag in NIC_TAGS else NI_TAGS,
                                nic_end) if nic_end else None
        # shares outstanding (dei, cover page — the freshest count)
        sh = None
        dei = (f.get("facts") or {}).get("dei") or {}
        node = dei.get("EntityCommonStockSharesOutstanding") or {}
        best = None
        for unit, arr in (node.get("units") or {}).items():
            for x in arr:
                e = x.get("end")
                if e and (best is None or e > best[0]):
                    best = (e, x.get("val"))
        if best:
            sh = best[1]
        assets, _, _, _ = _latest_instant(f, ["Assets"], as_of=eq_end)
        return {"assets": assets, "stale_components_not_applied": stale,
                "component_dates": {"preferred": pfd_end, "goodwill": gw_end,
                                    "intangibles": in_end},
                "equity": eq, "equity_end": eq_end, "equity_tag": eq_tag,
                "preferred": pfd, "goodwill": gw, "intangibles": intan,
                "ni_common_ttm": nic, "ni_common_end": nic_end, "ni_tag": nic_tag,
                "ni_quarters": nq, "ni_common_prior_ttm": prior, "shares": sh,
                "entity_name": (f.get("entityName") or "")}
    return _cached(f"sec_{int(cik)}.json", _pull, refresh)


# ── stage 4: derive the metrics ─────────────────────────────────────────────────────
def _r(x, n=2):
    return round(x, n) if isinstance(x, (int, float)) else None


def _div(a, b, pct=True):
    if a is None or not b:
        return None
    return round(100.0 * a / b, 2) if pct else round(a / b, 4)


def consolidate_quarters(fin: dict):
    """Combine a holdco's insured subsidiaries into one call-report view per quarter.

    Two traps handled explicitly:
      * NESTED banks — Greene County Bancorp's "Greene County Commercial Bank" is a
        subsidiary OF "The Bank of Greene County", so SUMMING the two double-counts the
        balance sheet.  PARCERT identifies the child; children are dropped.
      * SIBLING banks — Ames National really does own six separate Iowa charters; those
        DO sum.  Dollar fields are summed and every ratio is RECOMPUTED from the summed
        dollars rather than averaged (averaging ratios across unequal banks is wrong).
    """
    per_q = {}
    for cert, rows in (fin or {}).items():
        for q in (rows or []):
            per_q.setdefault(q["REPDTE"], []).append(q)
    out = {}
    for dt, rows in per_q.items():
        certs = {int(r["CERT"]) for r in rows}
        rows = [r for r in rows if not (r.get("PARCERT") and int(r["PARCERT"]) in certs)]
        if not rows:
            continue

        def S(f):
            vals = [r.get(f) for r in rows if r.get(f) is not None]
            return sum(vals) if vals else None
        agg = {f: S(f) for f in ("ASSET", "EQ", "EQTOT", "INTAN", "NETINC", "DEP",
                                "DEPDOM", "DEPINS", "DEPUNINS", "DEPNIDOM", "COREDEP",
                                "BRO", "LNLSNET", "LNATRES", "ORE", "NALTOT", "NTLNLS",
                                "ELNATR", "LNRECONS", "LNRENRES", "LNREMULT", "LNRERES",
                                "LNRE", "LNCI", "LNCON", "RBC", "NUMEMP")}
        agg["REPDTE"] = dt
        agg["n_banks"] = len(rows)
        agg["_names"] = [r.get("NAME") for r in rows]
        agg["STALP"] = rows[0].get("STALP")
        # ratios only meaningful single-bank; for multi-bank recompute where we can
        big = max(rows, key=lambda r: r.get("ASSET") or 0)
        for f in ("NCLNLSR", "NCRECONR", "NCRENRER", "NCRER", "NPERFV", "NTLNLSR",
                  "LNATRESR", "LNLSDEPR", "IDT1RWAJR", "RBCRWAJ", "RBC1AAJ",
                  "ROA", "ROE", "NIMY", "EEFFR", "SPECGRPDESC", "BKCLASS"):
            agg[f] = big.get(f)
        agg["_ratio_basis"] = "largest_bank" if len(rows) > 1 else "single_bank"
        out[dt] = agg
    return out


def derive(rec):
    """Build the screening record.  Every number carries its basis; missing is MISSING."""
    sec = rec.get("_sec") or {}
    qs = consolidate_quarters(rec.get("_fin"))
    dts = sorted(qs, reverse=True)
    q = qs[dts[0]] if dts else None
    q4 = qs[dts[4]] if len(dts) > 4 else (qs[dts[-1]] if len(dts) > 1 else None)

    d = {
        "ticker": rec["sym"], "name": rec["name"].replace(" Common Stock", "").strip(),
        "cik": rec["cik"], "mktcap": rec.get("mktcap"), "px": rec.get("px"),
        "state": rec.get("state"), "bank_city": rec.get("bank_city"),
        "bank_names": rec.get("bank_names"), "certs": rec.get("certs"),
        "fdic_match": rec.get("fdic_match"),
        "call_report_date": q["REPDTE"] if q else None,
        "n_bank_charters": q["n_banks"] if q else None,
        "ratio_basis": q.get("_ratio_basis") if q else None,
    }

    # ── holdco tangible book (SEC, audited) ──
    eq = sec.get("equity")
    pfd = sec.get("preferred") or 0
    gw = sec.get("goodwill") or 0
    intan = sec.get("intangibles") or 0
    sh = sec.get("shares")
    tce = (eq - pfd - gw - intan) if eq is not None else None
    d["holdco_equity"] = eq
    d["preferred"] = pfd
    d["goodwill_plus_intangibles"] = gw + intan
    d["tce"] = tce
    # SHARE COUNT: the dei cover-page fact is unreliable on a minority of filers (FBLA's
    # tagged 161,489 vs ~16.2M actual; FSBW's is a stale pre-conversion count).  Use the
    # market-implied count (mcap / last sale, same source, internally consistent) as
    # PRIMARY and keep dei as a cross-check with the divergence recorded.  Note that
    # P/TBV itself does NOT depend on the share count — it is mcap over total tangible
    # common equity — so the ranking is immune to this; only per-share display isn't.
    implied = (rec["mktcap"] / rec["px"]) if (rec.get("px") and rec.get("mktcap")) else None
    d["shares"] = implied or sh
    d["shares_basis"] = "implied_mcap_over_price" if implied else "dei_cover_page"
    d["shares_dei"] = sh
    d["shares_divergence_pct"] = _div(sh - implied, implied) if (sh and implied) else None
    shu = d["shares"]
    d["book_date"] = sec.get("equity_end")
    d["tbv_per_share"] = _r(tce / shu, 2) if (tce and shu) else None
    d["bv_per_share"] = _r((eq - pfd) / shu, 2) if (eq is not None and shu) else None
    d["p_tbv"] = _r(rec["mktcap"] / tce, 3) if (tce and tce > 0) else None
    d["p_b"] = _r(rec["mktcap"] / (eq - pfd), 3) if (eq and (eq - pfd) > 0) else None
    # The TELL: goodwill does NOT survive a deal — the acquirer pays tangible book and
    # writes its OWN goodwill.  A wide P/B-vs-P/TBV gap means the screen's "cheap on book"
    # is an illusion for acquisition purposes.
    d["gw_intan_pct_of_equity"] = _div(gw + intan, eq)
    d["pb_ptbv_gap"] = _r(d["p_tbv"] - d["p_b"], 3) if (d["p_tbv"] and d["p_b"]) else None

    # ── earnings: NI available to COMMON and its trend (house rule) ──
    nic, prior = sec.get("ni_common_ttm"), sec.get("ni_common_prior_ttm")
    d["ni_common_ttm"] = nic
    d["ni_common_prior_ttm"] = prior
    d["ni_common_yoy_pct"] = _div(nic - prior, abs(prior)) if (nic is not None and prior) else None
    d["ni_basis"] = sec.get("ni_tag")
    d["rote_pct"] = _div(nic, tce) if (nic is not None and tce and tce > 0) else None
    d["roe_pct"] = _div(nic, eq - pfd) if (nic is not None and eq and (eq - pfd) > 0) else None
    d["pe_ttm"] = _r(rec["mktcap"] / nic, 1) if (nic and nic > 0) else None
    # valuation identity: ROTE / P/TBV should ~= 1 / P/E.  A break means the book or the
    # earnings is not what it looks like (the ADR lesson).
    if d["rote_pct"] and d["p_tbv"] and d["pe_ttm"]:
        lhs = (d["rote_pct"] / 100.0) / d["p_tbv"]
        d["identity_break_pp"] = _r(abs(lhs - 1.0 / d["pe_ttm"]) * 100, 2)

    if not q:
        d["data_gaps"] = ["no call report"]
        return d

    # ── credit (bank-level call report) ──
    loans = q.get("LNLSNET")
    d["assets_musd"] = _r((q.get("ASSET") or 0) / 1000, 1)
    d["npa_assets_pct"] = q.get("NPERFV")           # noncurrent assets + OREO / assets
    d["noncurrent_loans_pct"] = q.get("NCLNLSR")
    d["nco_pct"] = q.get("NTLNLSR")                 # net charge-offs / loans, YTD ann.
    d["acl_loans_pct"] = q.get("LNATRESR")
    ncl = (q.get("NCLNLSR") or 0) / 100.0 * (loans or 0)
    d["acl_ncl_cov_pct"] = _div(q.get("LNATRES"), ncl) if ncl else None
    d["noncurrent_cre_pct"] = q.get("NCRENRER")
    d["noncurrent_constr_pct"] = q.get("NCRECONR")
    d["oreo_musd"] = _r((q.get("ORE") or 0) / 1000, 2)

    # ── concentration vs the supervisory guidance thresholds (100% C&D / 300% CRE) ──
    rbc = q.get("RBC")
    d["cd_rbc_pct"] = _div(q.get("LNRECONS"), rbc)
    cre = sum(v for v in (q.get("LNRECONS"), q.get("LNREMULT"), q.get("LNRENRES"))
              if v is not None)
    d["cre_rbc_pct"] = _div(cre, rbc)
    # NOTE: LNRENRES includes OWNER-OCCUPIED nonfarm nonresidential, which the supervisory
    # CRE-concentration test EXCLUDES.  This ratio is therefore an UPPER BOUND on the
    # regulatory number, not the regulatory number.  Named, not hidden.
    d["cre_rbc_basis"] = "upper_bound_incl_owner_occupied"
    d["cd_flag"] = bool(d["cd_rbc_pct"] and d["cd_rbc_pct"] > 100)
    d["cre_flag"] = bool(d["cre_rbc_pct"] and d["cre_rbc_pct"] > 300)

    # ── funding / deposit franchise — what the acquirer is actually buying ──
    dep = q.get("DEP") or q.get("DEPDOM")
    d["deposits_musd"] = _r((dep or 0) / 1000, 1)
    d["nib_dep_pct"] = _div(q.get("DEPNIDOM"), q.get("DEPDOM") or dep)
    d["core_dep_pct"] = _div(q.get("COREDEP"), dep)
    d["brokered_pct"] = _div(q.get("BRO"), dep)
    d["uninsured_pct"] = _div(q.get("DEPUNINS"), dep)
    d["loan_dep_pct"] = q.get("LNLSDEPR")
    d["nim_pct"] = q.get("NIMY")
    d["efficiency_pct"] = q.get("EEFFR")
    d["bank_roa_pct"] = q.get("ROA")
    d["tier1_rbc_pct"] = q.get("IDT1RWAJR")
    d["total_rbc_pct"] = q.get("RBCRWAJ")
    d["employees"] = q.get("NUMEMP")
    d["deposits_per_employee_musd"] = _r((dep or 0) / 1000 / q["NUMEMP"], 2) \
        if q.get("NUMEMP") else None

    # ── RESERVE-RELEASE MASK (the MI peak-cycle pattern, bank version) ──
    # Earnings flattered by provisioning BELOW charge-offs while the reserve ratio falls.
    prov, nco_d = q.get("ELNATR"), q.get("NTLNLS")
    d["provision_ytd_musd"] = _r((prov or 0) / 1000, 2)
    d["nco_ytd_musd"] = _r((nco_d or 0) / 1000, 2)
    acl_now = q.get("LNATRESR")
    acl_yr = q4.get("LNATRESR") if q4 else None
    d["acl_loans_pct_yr_ago"] = acl_yr
    d["acl_delta_yoy_pp"] = _r(acl_now - acl_yr, 2) if (acl_now and acl_yr) else None
    d["reserve_release_flag"] = bool(
        prov is not None and nco_d is not None and nco_d > 0 and prov < nco_d
        and acl_now and acl_yr and acl_now < acl_yr)
    # credit DIRECTION matters more than level to an acquirer pricing a credit mark
    if q4:
        d["npa_delta_yoy_pp"] = _r((q.get("NPERFV") or 0) - (q4.get("NPERFV") or 0), 2)
        d["nco_delta_yoy_pp"] = _r((q.get("NTLNLSR") or 0) - (q4.get("NTLNLSR") or 0), 2)
        d["prior_call_report_date"] = q4["REPDTE"]

    gaps = [k for k in ("p_tbv", "npa_assets_pct", "core_dep_pct", "ni_common_ttm")
            if d.get(k) is None]
    d["data_gaps"] = gaps
    return d


def attach_acquirability(d, rec):
    a = rec.get("_acq") or {}
    d["structure"] = a.get("structure")
    d["acquirable"] = a.get("acquirable", True)
    d["structural_block"] = a.get("blocked_reason")
    d["conversion_date"] = a.get("conversion_date")
    d["conversion_date_basis"] = a.get("conversion_date_basis")
    d["mhc_ownership_pct"] = a.get("mhc_ownership_pct")
    d["acquirability_source"] = a.get("source_filing")
    return d


# ── consolidator / footprint map ────────────────────────────────────────────────────
# Populated from the deal research pass (see BANK_CONSOLIDATION.json:consolidator_map).
CONSOLIDATOR_STATES: dict = {}


def load_consolidator_map(path=None):
    global CONSOLIDATOR_STATES
    p = path or os.path.join(DATA, "bank_consolidator_map.json")
    if os.path.exists(p):
        with open(p) as f:
            m = json.load(f)
        CONSOLIDATOR_STATES = m.get("state_intensity", {})
        return m
    return {}


# ── scoring ─────────────────────────────────────────────────────────────────────────
def score_name(rec, state_intensity):
    """0-100 acquiree attractiveness.  Generator ranking only."""
    parts, notes = {}, []

    # 1. CHEAPNESS vs TANGIBLE book (35).  Deals are struck in P/TBV.
    ptbv = rec.get("p_tbv")
    if ptbv is None:
        parts["cheap"] = 0.0
        notes.append("P/TBV unavailable")
    else:
        # 0.70x -> 35 ; 1.00x -> 24 ; 1.30x -> 10 ; >1.6x -> 0
        parts["cheap"] = max(0.0, min(35.0, 35.0 * (1.60 - ptbv) / 0.90))

    # 2. CREDIT CLEANLINESS (25).  Acquirers pay book for a clean book and discount a dirty one.
    c = 25.0
    npa = rec.get("npa_assets_pct")          # noncurrent assets + OREO / assets
    nco = rec.get("nco_pct")                 # net charge-offs / loans
    cov = rec.get("acl_ncl_cov_pct")         # ACL / noncurrent loans
    if npa is None:
        c -= 8.0
        notes.append("NPA ratio unavailable")
    else:
        if npa > 0.50:
            c -= min(12.0, (npa - 0.50) * 12.0)
        if npa < 0.25:
            c += 0.0
    if nco is not None and nco > 0.30:
        c -= min(7.0, (nco - 0.30) * 10.0)
    if cov is not None and cov < 60:
        c -= min(5.0, (60 - cov) / 12.0)
    # concentration: supervisory C&D >100% of RBC and total CRE >300% of RBC
    cd = rec.get("cd_rbc_pct")
    cre = rec.get("cre_rbc_pct")
    if cd is not None and cd > 100:
        c -= min(5.0, (cd - 100) / 10.0)
    if cre is not None and cre > 300:
        c -= min(6.0, (cre - 300) / 25.0)
    parts["credit"] = max(0.0, c)

    # 3. DEPOSIT / FUNDING QUALITY (20).  This is what the acquirer is actually buying.
    d = 20.0
    core = rec.get("core_dep_pct")
    nib = rec.get("nib_dep_pct")
    bro = rec.get("brokered_pct")
    ltd = rec.get("loan_dep_pct")
    if core is None and nib is None:
        d -= 7.0
        notes.append("deposit mix unavailable")
    if nib is not None:
        d += min(4.0, max(-8.0, (nib - 18.0) / 2.0))     # 18% NIB = par
        # A bank with under 10% non-interest-bearing deposits has no core TRANSACTION
        # franchise — it is funding itself with rate-shopped savings and CDs that reprice
        # away the moment a buyer stops paying up.  That is the single attribute an
        # acquirer is least willing to pay tangible book for, so it carries its own
        # penalty rather than being averaged away.  (First Internet Bancorp, branchless at
        # 3.2% non-interest-bearing, screened into the intake on cheapness alone before the
        # slope was steepened.)  A further penalty applies below 6%, where there is
        # effectively no transaction account base at all.
        # NOTE a definitional trap: the call-report COREDEP field counts non-brokered time
        # deposits under the insurance threshold, so a branchless CD-funded bank can print
        # 80%+ 'core' while having almost no franchise.  Read core_dep_pct WITH nib_dep_pct,
        # never alone.
        if nib < 6.0:
            d -= 4.0
    if bro is not None and bro > 10:
        d -= min(7.0, (bro - 10) / 3.0)
    if ltd is not None and ltd > 95:
        d -= min(4.0, (ltd - 95) / 6.0)
    parts["funding"] = max(0.0, min(20.0, d))

    # 4. ACQUIRER FOOTPRINT OVERLAP (15) — is somebody actually buying in this state?
    st = rec.get("state")
    inten = float(state_intensity.get(st, {}).get("score", 0.0)) if st else 0.0
    parts["footprint"] = max(0.0, min(15.0, inten))

    # 5. DIGESTIBILITY (5) — $200M-$700M market cap is the sweet spot for an in-market
    #    buyer: big enough to move the needle, small enough to pay cash+stock without a
    #    capital raise.
    m = rec.get("mktcap") or 0
    if 2e8 <= m <= 7e8:
        parts["size"] = 5.0
    elif 1e8 <= m < 2e8 or 7e8 < m <= 1e9:
        parts["size"] = 3.0
    else:
        parts["size"] = 1.0

    raw = sum(parts.values())

    # ── STRUCTURAL ACQUIRABILITY MULTIPLIER ──
    # Applied LAST and reported separately: the components above measure how much an
    # acquirer would WANT this bank; this measures whether it can legally BUY it.  A
    # cheap, clean, blocked thrift is not a mispricing — the block is why it is cheap.
    struct = rec.get("structure")
    mult, why = 1.0, None
    if struct == "MHC_majority":
        mult, why = 0.20, "MHC holds majority — no third party can acquire the company"
    elif struct == "MHC_suspected":
        mult, why = 0.45, "MHC language throughout the 10-Q — structure unconfirmed"
    elif struct == "recent_conversion":
        mult, why = 0.50, "inside the 3-year post-conversion acquisition prohibition"
    elif struct == "UNVERIFIED":
        mult, why = 0.80, "structure could not be verified from filings (not a clean bill)"
    if why:
        notes.append(f"structural multiplier {mult:.2f}: {why}")

    total = round(raw * mult, 1)
    parts_out = {k: round(v, 1) for k, v in parts.items()}
    parts_out["_raw_before_structure"] = round(raw, 1)
    parts_out["_structure_multiplier"] = mult
    return total, parts_out, notes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--top", type=int, default=10)
    ap.add_argument("--skip-sec", action="store_true")
    args = ap.parse_args()

    t0 = time.time()
    uni = fetch_bank_universe(args.refresh)
    print(f"[1] universe: {len(uni)} listed banks/thrifts $100M-$1B", file=sys.stderr)

    insts = fetch_institutions(args.refresh)
    hc_idx = build_hc_index(insts)
    inst_by_name = {}
    for r in insts:
        inst_by_name.setdefault(_key(r.get("NAME", "")), []).append(r)
    print(f"[2] FDIC active institutions: {len(insts)}", file=sys.stderr)

    recs = [dict(r) for r in uni]

    # SEC holdco book + registrant address FIRST — the address is an input to collision
    # resolution on the FDIC join, so it cannot run after it.
    def _sec(rec):
        try:
            rec["_sec"] = sec_book(rec["cik"], args.refresh)
            rec["_secsub"] = sec_state(rec["cik"], args.refresh)
        except Exception as e:  # noqa: BLE001
            rec["_sec"] = {"_error": str(e)[:120]}
            rec["_secsub"] = {}
        return rec
    with ThreadPoolExecutor(max_workers=5) as ex:
        recs = list(ex.map(_sec, recs))
    print(f"[3] SEC companyfacts + submissions pulled ({time.time()-t0:.0f}s)",
          file=sys.stderr)

    for rec in recs:
        rows, how = match_bank(rec, hc_idx, inst_by_name)
        if rows:
            rows, dis = disambiguate(rec, rows)
            how = f"{how}|{dis}"
        rec["fdic_match"] = how
        rec["certs"] = [x["CERT"] for x in rows] if rows else []
        rec["bank_names"] = [x["NAME"] for x in rows] if rows else []
        rec["state"] = rows[0]["STALP"] if rows else None
        rec["bank_city"] = rows[0].get("CITY") if rows else None
    matched = sum(1 for x in recs if x["certs"])
    print(f"[4] FDIC join: {matched}/{len(recs)} matched", file=sys.stderr)

    def _fin(rec):
        if not rec["certs"]:
            return rec
        key = f"fin_{'_'.join(str(c) for c in sorted(rec['certs']))}.json"
        qs = _cached(key, lambda: {c: fetch_financials(c) for c in rec["certs"]},
                     args.refresh)
        # a cert that returns nothing is DATA MISSING, never zero — retry once, then say so
        for c, v in list(qs.items()):
            if not v:
                qs[c] = fetch_financials(int(c))
        rec["_fin"] = qs
        return rec

    with ThreadPoolExecutor(max_workers=6) as ex:
        recs = list(ex.map(_fin, recs))
    print(f"[5] call reports pulled ({time.time()-t0:.0f}s)", file=sys.stderr)

    # ── the ACQUIRABILITY gate — read each registrant's own latest 10-Q ──
    def _acq(rec):
        try:
            f = sec_filings(rec["cik"], args.refresh)
            # PREFER THE 10-K.  The structure disclosure ("X Bancorp, MHC owns 57%") lives
            # in Item 1 of the annual report; most 10-Qs never mention it, so reading the
            # quarterly silently classifies MHC-controlled thrifts as ordinary stock
            # holdcos.  Rhinebeck, Pioneer and Bogota were all missed that way.
            tenk = [x for x in f.get("filings", []) if x["form"] == "10-K"]
            tenq = tenk + [x for x in f.get("filings", []) if x["form"] == "10-Q"]
            if not tenq:
                rec["_acq"] = {"structure": "UNVERIFIED",
                               "blocked_reason": "no 10-Q/10-K on file"}
                return rec
            q = tenq[0]
            txt = fetch_filing_text(rec["cik"], q["acc"], q["doc"], args.refresh)
            a = acquirability(rec["cik"], txt, f.get("first_filing"))
            a["source_filing"] = f"{q['form']} {q['date']} acc {q['acc']}"
            rec["_acq"] = a
        except Exception as e:  # noqa: BLE001
            rec["_acq"] = {"structure": "UNVERIFIED", "blocked_reason": str(e)[:120]}
        return rec
    with ThreadPoolExecutor(max_workers=5) as ex:
        recs = list(ex.map(_acq, recs))
    print(f"[6] acquirability read from filings ({time.time()-t0:.0f}s)", file=sys.stderr)

    json.dump(recs, open(_cache_path("recs_raw.json"), "w"))

    cmap = load_consolidator_map()
    inten = cmap.get("state_intensity", {})
    rows = []
    for rec in recs:
        d = attach_acquirability(derive(rec), rec)
        if d["ticker"] in EXCLUDE:
            d["excluded"] = "already held or courted (financials cluster)"
        if d["ticker"] in LIVE_DEALS:
            side, detail = LIVE_DEALS[d["ticker"]]
            d["live_deal"] = {"side": side, "detail": detail}
            d["excluded"] = (f"already in an announced transaction as the {side} — {detail}")
        total, parts, notes = score_name(d, inten)
        d["score"] = total
        d["score_parts"] = parts
        d["score_notes"] = notes
        acq = inten.get(d.get("state") or "", {})
        d["state_deal_activity"] = {
            "intensity_score": acq.get("score"),
            "deals_18mo": acq.get("deals"),
            "active_acquirers": acq.get("acquirers", []),
        }
        # Concrete, per-name version of the cohort-multiple finding: how far the name would
        # have to re-rate to reach the REALISED takeout band for its OWN target type
        # (listed thrift / low-ROE bank cleared 0.77x-1.06x TBV in the 18-month window;
        # median across ALL listed sub-$1.5B targets was 1.24x).  A negative figure means a
        # takeout at that multiple would be a DOWN round from today's price.
        pt = d.get("p_tbv")
        if pt:
            d["takeout_headroom"] = {
                "p_tbv_now": pt,
                "to_low_end_0_77x_pct": round(100 * (0.77 - pt) / pt, 1),
                "to_type_high_1_06x_pct": round(100 * (1.06 - pt) / pt, 1),
                "to_all_listed_small_median_1_24x_pct": round(100 * (1.24 - pt) / pt, 1),
                "basis": "realised 2025-26 multiples for LISTED sub-$1.5B targets: the "
                         "thrift / low-ROE type cleared 0.77x-1.06x tangible book; the "
                         "median across all listed small targets was 1.24x. The headline "
                         "~1.5x all-deals median is NOT the comparable for this cohort.",
            }
        rows.append(d)
    rows.sort(key=lambda x: -x["score"])
    print(f"[7] scored {len(rows)} names", file=sys.stderr)

    intake = [r for r in rows if not r.get("excluded")
              and r.get("acquirable") and r.get("p_tbv") is not None
              and not r.get("data_gaps")][:args.top]

    out = {
        "generator": "bank_consolidation_scanner",
        "version": "1.0",
        "as_of": time.strftime("%Y-%m-%d"),
        "status": "GENERATOR OUTPUT — no verdicts, no sizing, no orders. Court intake only.",
        "thesis_under_test": (
            "A bank M&A wave is running under the current regulatory climate and the "
            "pattern of a small clean thrift being acquired at a premium is repeatable; "
            "therefore sub-$1B-cap banks at/below tangible book with clean credit, in "
            "footprints where active consolidators are buying, are undervalued acquirees."),
        "premise_corrections": PREMISE_CORRECTIONS,
        "universe": {
            "n": len(rows),
            "definition": "US exchange-listed common stocks, Nasdaq screener sector=Finance "
                          "and industry in {Major Banks, Banks, Commercial Banks, Savings "
                          "Institutions}, market cap $100M-$1B",
            "source": "api.nasdaq.com/api/screener/stocks (via verticals.deep_value.universe), "
                      "ticker->CIK via sec.gov/files/company_tickers.json",
            "fdic_join": "100% (129/129) of the universe resolved to an FDIC-insured "
                         "subsidiary via the institutions-endpoint NAMEHCR field, with "
                         "name-collision resolution by registrant business state",
            "non_common_tickers_dropped": "18 preferred / depositary / baby-bond symbols "
                                          "that SEC company_tickers maps to the parent CIK",
        },
        "scoring": {
            "cheapness_vs_tangible_book": 35, "credit_cleanliness": 25,
            "deposit_funding_quality": 20, "acquirer_footprint_overlap": 15,
            "size_digestibility": 5,
            "structural_multiplier": "applied AFTER the components: MHC-majority 0.20, "
                                     "MHC-suspected 0.45, inside the 3-year post-conversion "
                                     "prohibition 0.50, structure unverified 0.80",
        },
        "key_findings": KEY_FINDINGS,
        "consolidator_map": cmap,
        "top_intake": [
            {k: r.get(k) for k in (
                "ticker", "name", "state", "bank_city", "score", "score_parts",
                "takeout_headroom",
                "px", "mktcap", "p_tbv", "p_b", "tbv_per_share", "rote_pct",
                "ni_common_ttm", "ni_common_yoy_pct", "pe_ttm", "assets_musd",
                "deposits_musd", "npa_assets_pct", "noncurrent_loans_pct", "nco_pct",
                "acl_loans_pct", "acl_ncl_cov_pct", "oreo_musd", "cd_rbc_pct",
                "cre_rbc_pct", "cre_rbc_basis", "cd_flag", "cre_flag",
                "nib_dep_pct", "core_dep_pct", "brokered_pct", "uninsured_pct",
                "loan_dep_pct", "nim_pct", "efficiency_pct", "tier1_rbc_pct",
                "reserve_release_flag", "acl_delta_yoy_pp", "npa_delta_yoy_pp",
                "structure", "acquirable", "conversion_date", "acquirability_source",
                "call_report_date", "book_date", "state_deal_activity", "bank_names",
                "certs", "cik")} | {"case": CASES.get(r["ticker"], "")}
            for r in intake
        ],
        "structurally_blocked": [
            {k: r.get(k) for k in ("ticker", "name", "state", "p_tbv", "rote_pct",
                                   "npa_assets_pct", "structure", "conversion_date",
                                   "conversion_date_basis", "mhc_ownership_pct",
                                   "structural_block", "acquirability_source")}
            for r in rows if not r.get("acquirable")
        ],
        "already_in_a_deal": [
            {"ticker": r["ticker"], "name": r["name"], "state": r["state"],
             "p_tbv": r["p_tbv"], "live_deal": r["live_deal"]}
            for r in rows if r.get("live_deal")
        ],
        "excluded_by_brief": sorted(EXCLUDE),
        "universe_scored": rows,
    }
    os.makedirs(DATA, exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(out, f, indent=1)
    print(f"[8] wrote {OUT} ({len(intake)} intake / {len(rows)} scored)", file=sys.stderr)
    return out


if __name__ == "__main__":
    main()
