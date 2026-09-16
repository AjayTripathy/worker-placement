"""
Robotics / autonomous-systems cohort — Signal OS blinded forward test.

4 speculative robotics / autonomous-systems names (SYM Symbotic warehouse
automation, KSCP Knightscope security robots, BBAI BigBear.AI defense
analytics, SERV Serve Robotics last-mile delivery) + 2 mature controls
(IRBT iRobot consumer / Roomba; TER Teradyne semi test + Universal
Robots collaborative-robotics subsidiary).

Less calibration-overlap with prior cohorts. Speculative names share
the recent IPO / de-SPAC pattern with named-customer pilot programs
(Walmart for SYM; Uber Eats for SERV; DoD / IC programs for BBAI;
named municipal customers for KSCP). Pilot programs vs. commercial-scale
deployments is the central stage-ladder distinction.

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
        ticker="SYM",
        name="Symbotic Inc.",
        notes="Warehouse-automation robotics; primary customer is Walmart "
              "(material customer concentration). De-SPAC 2022. Recent "
              "accounting restatement (revenue recognition)."),
    CohortMember(
        ticker="KSCP",
        name="Knightscope, Inc.",
        notes="Autonomous Security Robots (ASRs); named municipal / "
              "private-security customers. IPO 2022. Small cap, multiple "
              "reverse splits in recent history. Going-concern signals."),
    CohortMember(
        ticker="BBAI",
        name="BigBear.ai Holdings, Inc.",
        notes="AI / analytics for defense + intelligence community; named "
              "DoD program participation claims. De-SPAC 2021."),
    CohortMember(
        ticker="SERV",
        name="Serve Robotics Inc.",
        notes="Sidewalk-delivery robots; Uber Eats partnership is the "
              "centerpiece claim. Recent Nvidia-led financing."),
    CohortMember(
        ticker="IRBT", cik_override="0001159167",
        name="iRobot Corp.",
        notes="**CONTROL** — consumer robotic vacuum (Roomba) maker. Real "
              "consumer revenue, mature product line. (Failed Amazon "
              "acquisition was a separate issue.) Expected to score "
              "relatively clean; Amazon deal collapse and post-deal "
              "distress should be in the filings as disclosed."),
    CohortMember(
        ticker="TER",
        name="Teradyne, Inc.",
        notes="**CONTROL** — semiconductor automated test equipment + "
              "industrial-robotics (Universal Robots / MiR autonomous "
              "mobile robots subsidiaries). Real revenue, established "
              "customer base. Expected to score clean."),
]


COHORT_CONTEXT = (
    "Robotics / autonomous-systems pure-play (warehouse automation, security, "
    "last-mile delivery, defense AI/analytics) or mature robotics-adjacent "
    "industrial OEM. Counterparties span e-commerce / retail (Walmart WMT, "
    "Amazon AMZN, Target TGT), food delivery (Uber UBER, DoorDash DASH), "
    "logistics (FedEx FDX, UPS), defense (Lockheed LMT, Northrop NOC, "
    "Raytheon RTX) + intel community (no SEC filings — UNVERIFIABLE), and "
    "consumer-electronics (Apple AAPL, Google GOOGL).\n\n"
    "Claims typically reference: named-customer pilot vs. commercial "
    "deployment, units shipped / deployed / in-service, named site / "
    "city deployment count, contract awards (especially DoD via USAspending), "
    "AI / model claims (parameter count, dataset, benchmark performance).\n\n"
    "Apply Calibration Heuristic 3 (planned vs operational) WITH EXTRA WEIGHT. "
    "Robotics deployments move through stages: lab demo -> field trial -> "
    "named-customer pilot -> first commercial deployment -> scaled multi-"
    "site -> recurring revenue. Each stage is a different M-side check. "
    "Pilots-as-PR is the central evasion pattern — a named-customer pilot "
    "is real but doesn't imply current commercial revenue.\n\n"
    "Apply Layer 3 Rule 7 (counterparty-disclosure threshold). For SYM the "
    "Walmart customer concentration is so material it MUST appear in Walmart's "
    "10-K (already disclosed). For SERV the Uber Eats partnership should "
    "appear in Uber's 10-K if it's commercially material. For BBAI named DoD "
    "programs should appear in USAspending. Absence = HARD CONTRADICTION."
)


COMMON_COUNTERPARTY_CIKS: dict[str, str] = {
    # E-commerce / retail
    "Amazon (AMZN)":               "0001018724",
    "Walmart (WMT)":               "0000104169",
    "Target (TGT)":                "0000027419",
    # Food delivery
    "Uber (UBER)":                 "0001543151",
    "DoorDash (DASH)":             "0001792789",
    # Logistics
    "FedEx (FDX)":                 "0001048911",
    "UPS (UPS)":                   "0001090727",
    # Defense (BBAI customers)
    "Lockheed Martin (LMT)":       "0000936468",
    "Northrop Grumman (NOC)":      "0001133421",
    "Raytheon Technologies (RTX)": "0000101829",
    # Consumer / silicon
    "Apple (AAPL)":                "0000320193",
    "Alphabet (GOOGL)":            "0001652044",
    "Nvidia (NVDA)":               "0001045810",
}


CUTOFF = "2026-05-16"
