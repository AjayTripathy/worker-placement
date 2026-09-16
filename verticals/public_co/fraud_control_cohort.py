"""
Fraud-vs-control cohort for framework discrimination test.

Goal: with cutoff dates BEFORE each fraud was publicly revealed, does
the framework's EMIT rate discriminate documented frauds from same-
vintage same-industry clean controls?

Each member carries its OWN cutoff date (one date pre-revelation per
fraud, matching the control to its fraud's cutoff for industry/vintage
parity).

Fraud members:
  NKLA — Nikola Corp. Hindenburg report 2020-09-10; SEC settled Dec 2021.
         Cutoff 2020-08-01. Pre-Hindenburg, no 10-K yet (SPAC merger
         closed June 2020); use S-1 dated 2020-07-17.
  LOOP — Loop Industries. Hindenburg 2020-10-13 alleged fake plastic
         recycling tech. Cutoff 2020-09-01. Use 10-K/A 2020-05-06.
  RIDE — Lordstown Motors. Hindenburg 2021-03-12; SEC settled 2023.
         Cutoff 2021-02-01. Use 10-Q 2020-11-16 (SPAC, no 10-K yet).
  CEI  — Camber Energy. Kerrisdale short 2021-10-05; long filing-
         delinquency. Cutoff 2021-09-01. Use 10-Q/A 2020-12-21
         (most recent available given delinquency).

Control members (vintage / size / narrative-class matched):
  PLUG  — Plug Power. Clean hydrogen/fuel-cell incumbent.
          Cutoff 2020-08-01 (NKLA match). Use 10-K 2020-03-10.
  GEVO  — Gevo Inc. Renewable-chemicals cleantech, no fraud charges.
          Cutoff 2020-09-01 (LOOP match). Use 10-Q 2020-08-10.
          (PCT — original LOOP match — was not yet public; sub'd.)
  WKHS  — Workhorse Group. EV trucks SPAC class.
          Cutoff 2021-02-01 (RIDE match). Use 10-K 2020-03-13.
          BORDERLINE: WKHS later faced SEC scrutiny over USPS contract
          claims (settled 2024). At our cutoff, the SEC action had not
          been announced — but the underlying claims existed. EMIT on
          WKHS would be consistent with the SEC's eventual view, not a
          framework error.
  REI   — Ring Energy. Small-cap E&P, no fraud allegations.
          Cutoff 2021-09-01 (CEI match). Use 10-K 2021-03-16.

The discrimination test: framework EMIT rate on the 4 frauds vs the
3 clean controls (PLUG, GEVO, REI). WKHS is reported separately as
a borderline case.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class FraudControlMember:
    ticker:   str
    cik:      str
    name:     str
    cutoff:   str           # ISO date, pre-revelation
    klass:    str           # "FRAUD" | "CONTROL" | "BORDERLINE"
    notes:    str


COHORT: list[FraudControlMember] = [
    # ── FRAUDS ──────────────────────────────────────────────────────
    FraudControlMember(
        ticker="NKLA", cik="0001731289",
        name="Nikola Corporation",
        cutoff="2020-08-01", klass="FRAUD",
        notes=("Hindenburg report 2020-09-10. Trevor Milton SEC fraud "
               "charges July 2021; jailed 2023. Pre-cutoff filing: "
               "S-1 dated 2020-07-17 (no 10-K yet — SPAC merger closed "
               "June 2020). Claims under scrutiny: hydrogen-truck "
               "operational demos (rolled downhill), GM/Bosch/Anheuser "
               "partnerships, in-house hydrogen production capacity.")),
    FraudControlMember(
        ticker="LOOP", cik="0001504678",
        name="Loop Industries, Inc.",
        cutoff="2020-09-01", klass="FRAUD",
        notes=("Hindenburg report 2020-10-13 alleged fake plastic "
               "depolymerization tech, no commercial production, "
               "fabricated partnership claims with Coca-Cola/Pepsi/"
               "L'Oreal/Indorama. Pre-cutoff filing: 10-K/A 2020-05-06.")),
    FraudControlMember(
        ticker="RIDE", cik="0001759546",
        name="Lordstown Motors Corp.",
        cutoff="2021-02-01", klass="FRAUD",
        notes=("Hindenburg report 2021-03-12 alleged misleading preorder "
               "claims (~$1.4B reservations from non-binding LOIs, some "
               "from shell companies with no fleet). SEC settled 2023; "
               "Chapter 11 filed June 2023. Pre-cutoff filing: 10-Q "
               "2020-11-16 + S-1 (SPAC, no 10-K yet).")),
    FraudControlMember(
        ticker="CEI", cik="0001309082",
        name="Camber Energy, Inc.",
        cutoff="2021-09-01", klass="FRAUD",
        notes=("Kerrisdale short 2021-10-05 alleged ESG/Viking energy "
               "inflation, going-concern hidden, dilutive death-spiral "
               "convertibles. Long filing-delinquency. Pre-cutoff filing: "
               "10-Q/A 2020-12-21 (most recent available given delinquency).")),

    # ── CLEAN CONTROLS ──────────────────────────────────────────────
    FraudControlMember(
        ticker="PLUG", cik="0001093691",
        name="Plug Power Inc.",
        cutoff="2020-08-01", klass="CONTROL",
        notes=("Hydrogen/fuel-cell incumbent. No fraud charges sustained. "
               "Match for NKLA on hydrogen narrative + 2020 vintage. "
               "Pre-cutoff filing: 10-K 2020-03-10.")),
    FraudControlMember(
        ticker="GEVO", cik="0001392380",
        name="Gevo, Inc.",
        cutoff="2020-09-01", klass="CONTROL",
        notes=("Renewable-chemicals cleantech (ethanol-to-jet-fuel). Has "
               "had short interest but no fraud charges. Match for LOOP "
               "on cleantech narrative + 2020 vintage. Substituted for "
               "PCT (PureCycle didn't IPO until March 2021). Pre-cutoff "
               "filing: 10-Q 2020-08-10 + S-1/A 2020-06-29.")),
    FraudControlMember(
        ticker="REI", cik="0001384195",
        name="Ring Energy, Inc.",
        cutoff="2021-09-01", klass="CONTROL",
        notes=("Permian Basin small-cap E&P. No fraud allegations. "
               "Match for CEI on small-cap energy + 2021 vintage. "
               "Pre-cutoff filing: 10-K 2021-03-16 / 10-K/A 2021-03-17.")),

    # ── BORDERLINE ──────────────────────────────────────────────────
    FraudControlMember(
        ticker="WKHS", cik="0001425287",
        name="Workhorse Group Inc.",
        cutoff="2021-02-01", klass="BORDERLINE",
        notes=("EV trucks. Later SEC scrutiny over USPS-contract claims "
               "(settled 2024 for $1.7M). At 2021-02-01 cutoff, no SEC "
               "action announced — but underlying claims existed. EMIT "
               "here would be consistent with SEC's eventual view, not "
               "a framework error. Match for RIDE on EV-truck SPAC "
               "narrative. Pre-cutoff filing: 10-K 2020-03-13.")),
]


CUTOFF_DEFAULT = "2021-09-01"  # latest cutoff; used as the "as-of" for the cohort report

COHORT_CONTEXT = (
    "FRAUD-VS-CONTROL DISCRIMINATION TEST. 4 documented frauds (NKLA, "
    "LOOP, RIDE, CEI) + 3 clean controls (PLUG, GEVO, REI) + 1 borderline "
    "(WKHS — later SEC scrutiny). Each member uses its own pre-revelation "
    "cutoff date for hindsight-blinding. The test question: does the "
    "framework's multi-source aggregation EMIT at higher rates on the "
    "documented frauds than on the clean controls? \n\n"
    "All members are small-to-mid-cap public companies. Frauds have "
    "documented post-revelation outcomes (Hindenburg reports, SEC "
    "actions, bankruptcies). Controls are same-vintage same-industry "
    "names with no sustained fraud allegations. WKHS sits in a gray "
    "zone — later SEC action over USPS contract claims means an EMIT "
    "would be consistent with eventual SEC view."
)

# Common counterparties — frauds tend to cite mega-cap relationships.
COMMON_COUNTERPARTY_CIKS = {
    "Amazon":      "0001018724",
    "Microsoft":   "0000789019",
    "Walmart":     "0000104169",
    "Tesla":       "0001318605",
    "Apple":       "0000320193",
    "Alphabet":    "0001652044",
    "Nvidia":      "0001045810",
    "GM":          "0001467858",
    "Ford":        "0000037996",
    "Pepsi":       "0000077476",
    "Coca-Cola":   "0000021344",
    "L'Oreal":     "",       # foreign filer; not on EDGAR
    "Anheuser-Busch": "0001668717",  # AB InBev
    "Bosch":       "",       # private German
    "USPS":        "",       # gov entity not on EDGAR
}
