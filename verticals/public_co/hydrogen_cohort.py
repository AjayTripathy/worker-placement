"""
Hydrogen / fuel-cell cohort — Signal OS blinded forward test.

5 speculative hydrogen pure-plays (PLUG / BE / BLDP / FCEL / HYZN) +
2 industrial-gas controls (LIN Linde, APD Air Products). Controls
are dominant H2 producers via established steam-methane-reforming
and electrolyzer businesses with real revenue and real customer base;
they're the natural in-cohort longs for any emitted speculative shorts.

Sibling to nuclear: same hyperscaler-PPA / utility-offtake narrative
structure (e.g. Plug Power's hydrogen-for-data-centers pitch, Bloom's
SOFC hyperscaler claims), same stage-ladder discipline (electrolyzer
GW capacity ANNOUNCED vs UNDER CONSTRUCTION vs OPERATING), same
counterparty-disclosure threshold (named hyperscaler / heavy-industry
customer should appear in counterparty 10-K).

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
        ticker="PLUG",
        name="Plug Power Inc.",
        notes="Hydrogen fuel cells + electrolyzer + green-hydrogen production. "
              "Long history of headline customer claims (Amazon, Walmart, "
              "Microsoft, etc.) and missed revenue / EBITDA targets. "
              "Going-concern history."),
    CohortMember(
        ticker="BE",
        name="Bloom Energy Corp.",
        notes="Solid-oxide fuel cells (SOFCs). Hyperscaler data-center / "
              "AI-power narrative; major Equinix and AEP partnerships claimed. "
              "Revenue exists but profitability cyclical."),
    CohortMember(
        ticker="BLDP",
        name="Ballard Power Systems, Inc.",
        notes="PEM fuel cells (transportation / stationary). Canadian filer. "
              "Long history of OEM partnership announcements (Audi, Weichai, "
              "Solaris) that did not convert to scaled commercial revenue."),
    CohortMember(
        ticker="FCEL",
        name="FuelCell Energy, Inc.",
        notes="Carbonate / SOFC stationary fuel cells. Customer concentration "
              "(Korea Hydro, Toyota, U.S. DOE projects). Multiple reverse "
              "splits in recent history."),
    CohortMember(
        ticker="HYZN", cik_override="0001716583",
        name="Hyzon Motors Inc.",
        notes="Hydrogen heavy-duty trucks. Prior SEC enforcement / restatement "
              "of revenue claims (2021/2022). Going-concern indications. "
              "Likely already in late-stage distress."),
    CohortMember(
        ticker="LIN",
        name="Linde plc",
        notes="**CONTROL** — world's largest industrial-gas company; dominant "
              "H2 producer via steam-methane reforming + electrolyzer projects "
              "(Niagara Falls, Clear Lake, etc.). Real H2 revenue, mature "
              "customer base. Expected to score clean."),
    CohortMember(
        ticker="APD",
        name="Air Products and Chemicals, Inc.",
        notes="**CONTROL** — major industrial-gas + hydrogen player, NEOM "
              "green-hydrogen project, Louisiana blue-hydrogen project. "
              "Mature, scaled, real revenue. Expected to score clean."),
]


COHORT_CONTEXT = (
    "Hydrogen / fuel-cell pure-play (PEM, SOFC, carbonate) or H2 production "
    "/ heavy-duty FCEV. Counterparties span hyperscaler data-center customers "
    "(Amazon AMZN, Microsoft MSFT, Meta META, Alphabet GOOGL), heavy industry "
    "(Nucor NUE, Cleveland-Cliffs CLF — steel decarbonization customers), "
    "utilities (NextEra NEE, Duke DUK, Exelon EXC, AEP), auto OEMs (Honda HMC, "
    "Toyota TM — historical FCEV partners), and retail / logistics (Walmart "
    "WMT, FedEx FDX — Plug Power material-handling customers).\n\n"
    "Claims typically reference: announced electrolyzer GW capacity, named "
    "data-center customer wins, MW-scale stationary power deployments, "
    "FCEV truck delivery counts, DOE Hydrogen Hub awards (regional H2 hubs), "
    "PTC/45V eligibility, green vs blue hydrogen, IRA Section 48 ITC.\n\n"
    "Apply Calibration Heuristic 3 (planned vs operational) WITH EXTRA WEIGHT. "
    "H2 announcements move through stages: framework PPA / MoU -> binding offtake "
    "-> FID (final investment decision) -> construction -> commissioning -> "
    "operating at design capacity. Headline GW or MW capacity often refers to "
    "announced-not-built capacity; check the financial-statement notes for the "
    "actual capacity-in-operation figure.\n\n"
    "Apply Layer 3 Rule 7 (counterparty-disclosure threshold): if the company "
    "claims a binding hyperscaler PPA or heavy-industry offtake, that contract "
    "is material to the counterparty (data centers are 3-5% of grid load — "
    "anything material to them is in their 10-K) and should appear in their "
    "10-K / 8-K. Absence while company claims headline customer revenue is "
    "HARD CONTRADICTION -> RED_FLAG_NEGATIVE."
)


COMMON_COUNTERPARTY_CIKS: dict[str, str] = {
    # Hyperscaler data-center customers
    "Amazon (AMZN)":               "0001018724",
    "Microsoft (MSFT)":            "0000789019",
    "Meta Platforms (META)":       "0001326801",
    "Alphabet (GOOGL)":            "0001652044",
    # Heavy industry / steel
    "Nucor (NUE)":                 "0000073309",
    "Cleveland-Cliffs (CLF)":      "0000764065",
    # Utilities
    "NextEra Energy (NEE)":        "0000753308",
    "Duke Energy (DUK)":           "0001326160",
    "Exelon (EXC)":                "0001109357",
    # Retail / logistics
    "Walmart (WMT)":               "0000104169",
    "Target (TGT)":                "0000027419",
    "FedEx (FDX)":                 "0001048911",
    "UPS (UPS)":                   "0001090727",
    # Auto OEMs
    "Toyota Motor (TM, 20-F)":     "0001094517",
    "Honda Motor (HMC, 20-F)":     "0000715153",
}


CUTOFF = "2026-05-16"
