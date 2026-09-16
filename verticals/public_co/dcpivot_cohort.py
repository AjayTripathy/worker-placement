"""
AI data-center crypto-miner pivot cohort — Signal OS blinded forward test.

5 crypto-mining or recently-pivoted hyperscaler-AI-DC companies (CIFR /
IREN / APLD / CORZ / BTDR) + 2 mature data-center REIT controls (EQIX
Equinix, DLR Digital Realty). The speculative names all share the same
narrative: "we have power-grid interconnect capacity / shell DC capacity
that we're pivoting from BTC mining to AI/HPC hosting under multi-year
hyperscaler PPAs / hosting contracts." The REIT controls are the
established benchmark for that customer relationship — if a name claims
hyperscaler hosting, the hyperscaler's 10-K should mention them at a
scale comparable to EQIX/DLR.

This cohort is a direct cross-check on the hyperscaler-PPA narrative
that drove much of the nuclear cohort's Heuristic-3 / Heuristic-7
scoring. Where nuclear claims are pre-licensing (years of NRC work
before any kWh), AI-DC pivots claim near-term operating revenue from
hyperscaler hosting — much more verifiable on the counterparty 10-K.

Uniform cutoff: 2026-05-16.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CohortMember:
    """Cohort member with CIK derived from ticker via SEC's authoritative map.

    Do NOT pass cik= directly. Use cik_override= only for tickers SEC's
    company_tickers.json doesn't list (rare: certain foreign filers, recently
    delisted, or special ADRs). Default code path resolves CIK on demand from
    `edgar.cik_for(ticker)` — single source of truth, no hand-typed CIKs.
    """
    ticker: str
    name:   str
    notes:  str
    cik_override: str | None = None  # rarely used; default is SEC lookup

    @property
    def cik(self) -> str:
        from .edgar import cik_for
        return cik_for(self.ticker, override=self.cik_override)
COHORT: list[CohortMember] = [
    CohortMember(
        ticker="CIFR",
        name="Cipher Mining Inc.",
        notes="BTC miner pivoting to AI-DC hosting. Texas-based; Black "
              "Pearl 300MW build narrative. Has named a hyperscaler-class "
              "tenant deal as material claim recently."),
    CohortMember(
        ticker="IREN",
        name="Iris Energy Limited",
        notes="Australia-domiciled BTC miner + AI cloud / GPU rental "
              "pivot. Childress + Sweetwater + West Texas sites. Claims "
              "hyperscaler-quality power-grid interconnect."),
    CohortMember(
        ticker="APLD",
        name="Applied Digital Corp.",
        notes="HPC / AI-cloud hosting + crypto background. Major CoreWeave "
              "lease claim (Ellendale ND). Has tried to recategorize as "
              "data-center REIT for valuation purposes."),
    CohortMember(
        ticker="CORZ",
        name="Core Scientific, Inc.",
        notes="BTC mining + post-Ch. 11 reorganized; signed multi-billion "
              "CoreWeave HPC hosting deal claim (one of the largest AI-DC "
              "deals announced). Post-emergence balance sheet."),
    CohortMember(
        ticker="BTDR",
        name="Bitdeer Technologies Group",
        notes="Singapore-domiciled BTC miner + HPC pivot. Founded by "
              "Bitmain founder Jihan Wu. Foreign filer (20-F likely)."),
    CohortMember(
        ticker="EQIX",
        name="Equinix, Inc.",
        notes="**CONTROL** — world's largest data-center REIT; primary "
              "hyperscaler colocation provider. Real recurring hosting "
              "revenue from named hyperscaler customers, mature disclosure. "
              "Expected to score clean."),
    CohortMember(
        ticker="DLR",
        name="Digital Realty Trust, Inc.",
        notes="**CONTROL** — second-largest data-center REIT; hyperscaler "
              "colocation + interconnect. Mature, scaled. Expected to "
              "score clean."),
]


COHORT_CONTEXT = (
    "BTC miner pivoting to AI / HPC data-center hosting (or pure-play AI-DC), "
    "or mature data-center REIT. Counterparties span hyperscalers (Amazon "
    "AMZN, Microsoft MSFT, Meta META, Alphabet GOOGL, Apple AAPL), AI-compute "
    "specialists (Nvidia NVDA, AMD), neocloud (CoreWeave — private), and "
    "utilities supplying grid interconnect (NextEra NEE, Duke DUK, ERCOT-"
    "adjacent texas utilities).\n\n"
    "Claims typically reference: MW-scale grid interconnect approved / "
    "available, hyperscaler hosting contracts (often multi-billion-dollar "
    "headlines with multi-year ramps), CoreWeave (or similar neocloud) "
    "leases, conversion of BTC-mining floor space to AI/HPC, AI-DC PUE "
    "claims, water / cooling infrastructure.\n\n"
    "Apply Calibration Heuristic 3 (planned vs operational) WITH EXTRA WEIGHT. "
    "Hosting contracts move through stages: term sheet -> definitive lease -> "
    "shell construction -> commissioning -> energized -> generating revenue. "
    "Headline contract value often references TOTAL contract value over the "
    "full term (e.g. 12 years), not current-period revenue. Check the "
    "financial-statement notes for backlog vs. recognized-revenue split.\n\n"
    "Apply Layer 3 Rule 7 (counterparty-disclosure threshold) HARD. AI hosting "
    "contracts with hyperscalers (Microsoft, Amazon, etc.) at the multi-"
    "$100M-MW scale ARE material to the hyperscaler's data-center capex "
    "commentary and SHOULD appear in their 10-K. Absence while the AI-DC "
    "company claims a multi-billion-dollar deal is a HARD CONTRADICTION -> "
    "RED_FLAG_NEGATIVE. Note that CoreWeave is private and won't show up "
    "in EDGAR — that's a coverage gap, score CoreWeave-named contracts as "
    "UNVERIFIABLE on the counterparty axis."
)


COMMON_COUNTERPARTY_CIKS: dict[str, str] = {
    # Hyperscalers
    "Amazon (AMZN)":               "0001018724",
    "Microsoft (MSFT)":            "0000789019",
    "Meta Platforms (META)":       "0001326801",
    "Alphabet (GOOGL)":            "0001652044",
    "Apple (AAPL)":                "0000320193",
    "Oracle (ORCL)":               "0001341439",
    # AI compute partners
    "Nvidia (NVDA)":               "0001045810",
    "AMD (AMD)":                   "0000002488",
    # DC REITs (comparison / colocation context)
    "Equinix (EQIX)":              "0001101239",
    "Digital Realty (DLR)":        "0001297996",
    # Utilities (grid interconnect customer-of-the-utility)
    "NextEra Energy (NEE)":        "0000753308",
    "Duke Energy (DUK)":           "0001326160",
    "Exelon (EXC)":                "0001109357",
}


CUTOFF = "2026-05-16"
