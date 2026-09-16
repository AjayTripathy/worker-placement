"""
Space / satcom cohort — Signal OS blinded forward test.

5 speculative names (RKLB / ASTS / RDW / PL / SATS) + 2 mature commercial
controls (SATS or IRDM treated as control if appropriate, otherwise
defense-prime cross-cohort). Strong fit: USAspending covers federal
contracts (NASA, USSF, DARPA, NOAA); commercial customer claims are
verifiable via counterparty 10-K.

Note: IRDM (Iridium) has $700M+ stable commercial revenue from
satellite-services — closer to control than speculative; we'll treat
it as a "small control" (real but smaller than the defense primes).

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
        ticker="RKLB",
        name="Rocket Lab USA, Inc.",
        notes="Small-launch (Electron) + space-systems (Photon). "
              "Neutron medium-launch in development. Recent strong "
              "growth narrative around DoD launch contracts."),
    CohortMember(
        ticker="ASTS",
        name="AST SpaceMobile, Inc.",
        notes="Direct-to-mobile satellite broadband. BlueWalker 3 "
              "demonstration + BlueBird operational sat claims. AT&T, "
              "Verizon, Vodafone partnership narrative."),
    CohortMember(
        ticker="RDW",
        name="Redwire Corp.",
        notes="Space infrastructure (solar arrays, deployable "
              "structures, in-space manufacturing). NASA + DoD program "
              "participation claims."),
    CohortMember(
        ticker="PL",
        name="Planet Labs PBC",
        notes="Earth-observation satellite imagery. SkySat + Dove "
              "constellations. Mostly commercial revenue; some "
              "federal/intel customers."),
    CohortMember(
        ticker="SATS",
        name="EchoStar Corporation",
        notes="Satellite-based communications (Hughes / DISH after "
              "DISH merger). Real revenue at scale. Closer to control "
              "but recently has had complex disclosure around 5G "
              "buildout obligations."),
    CohortMember(
        ticker="IRDM",
        name="Iridium Communications Inc.",
        notes="**CONTROL** — operational 66-satellite LEO constellation "
              "with stable $700M+ annual commercial-services revenue. "
              "Mature, scaled, real customer base across IoT, "
              "maritime, aviation, government."),
]


COHORT_CONTEXT = (
    "Space launch / satellite / earth-observation / direct-to-mobile "
    "satellite communications. Counterparties span federal agencies "
    "(NASA, US Space Force USSF, DARPA, NOAA — all USAspending "
    "queryable), defense primes (Lockheed Martin LMT, Northrop "
    "Grumman NOC, Raytheon RTX — EDGAR-queryable), and commercial / "
    "telecom partners (AT&T T, Verizon VZ, Vodafone — foreign filer, "
    "T-Mobile TMUS).\n\n"
    "Claims typically reference: federal contract awards (NSSL, USSF "
    "STP-S series, NASA CLPS / Artemis subcontracts, NOAA weather "
    "constellation), launch cadence (X launches per year), satellite "
    "deployment milestones (constellation size, operational sats), "
    "named-customer commercial contracts, direct-to-mobile partnership "
    "stages (test-call demo vs MVNO agreement vs commercial service "
    "live).\n\n"
    "Apply Calibration Heuristic 3 (planned vs operational) WITH EXTRA "
    "WEIGHT. Constellation claims move through stages: design -> "
    "prototype -> first launch -> demonstration sat operational -> "
    "block-buy production -> full constellation operational. ASTS in "
    "particular has a long history of test-sat-as-proof claims vs "
    "operational-network claims.\n\n"
    "Apply Layer 3 Rule 7: federal contracts at the $-millions level "
    "ARE in USAspending; ABSENCE is a HARD CONTRADICTION."
)


COMMON_COUNTERPARTY_CIKS: dict[str, str] = {
    # Defense primes (cross-cohort with defense)
    "Lockheed Martin (LMT)":     "0000936468",
    "Northrop Grumman (NOC)":    "0001133421",
    "Raytheon Technologies (RTX)":"0000101829",
    "Boeing (BA)":               "0000012927",
    "L3Harris (LHX)":            "0000202058",
    # Commercial / telecom
    "AT&T (T)":                  "0000732717",
    "Verizon (VZ)":              "0000732712",
    "T-Mobile US (TMUS)":        "0001283699",
    # Hyperscalers (some space-as-service / GS plays)
    "Amazon (AMZN, Kuiper)":     "0001018724",
    "Microsoft (MSFT)":          "0000789019",
    "Alphabet (GOOGL)":          "0001652044",
}


CUTOFF = "2026-05-16"
