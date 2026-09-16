"""
Fintech lending / BNPL cohort — Signal OS blinded forward test.

4 speculative names (UPST AI-underwriting / AFRM BNPL / OPEN iBuying /
SOFI neobank) + 1 large-bank control (COF Capital One, credit-card
heavy, real revenue, mature disclosure).

Less-traction cohort: the framework's counterparty-cross-check is
weaker here because fintech disclosures lean on credit-loss reserves
and charge-off-rates rather than named-counterparty contracts. The
test here is whether the framework can find anything; the bar for
emission is correspondingly higher (we expect fewer hits, more
UNVERIFIABLE).

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
        ticker="UPST",
        name="Upstart Holdings, Inc.",
        notes="AI underwriting platform for personal/auto loans. "
              "Bank-partner model (revenue from referral fees, not "
              "balance-sheet loans). Loan-volume cyclicality tied to "
              "credit cycle."),
    CohortMember(
        ticker="AFRM",
        name="Affirm Holdings, Inc.",
        notes="BNPL — pay-over-time at point of sale. Major partners: "
              "Shopify, Amazon, Walmart, Apple Pay. Revenue mix between "
              "interest income and merchant network revenue."),
    CohortMember(
        ticker="OPEN",
        name="Opendoor Technologies Inc.",
        notes="iBuying / instant home-purchase platform. Inventory-"
              "carry-heavy business model. Going-concern questions in "
              "prior cycles."),
    CohortMember(
        ticker="SOFI",
        name="SoFi Technologies, Inc.",
        notes="Neobank + student-loan refinance + crypto + brokerage. "
              "Bank-charter acquired. Mixed-segment disclosure."),
    CohortMember(
        ticker="COF",
        name="Capital One Financial Corporation",
        notes="**CONTROL** — large credit-card-heavy bank. Real "
              "consumer-credit exposure. Recent Discover acquisition. "
              "Mature regulatory + financial disclosure."),
]


COHORT_CONTEXT = (
    "Fintech lending / BNPL / iBuying / neobank, or large-bank "
    "control. Counterparties span bank partners (for UPST, the lending "
    "banks behind the platform), merchant partners (AFRM via Shopify, "
    "Amazon, Walmart), securitization investors (loan-backed asset-"
    "backed-securities trustees), and regulators (CFPB, OCC, FDIC).\n\n"
    "Claims typically reference: loan origination volume, charge-off "
    "rates, credit-loss provisions, named-partner relationships, "
    "AI-model performance, regulatory clearance, securitization "
    "issuance.\n\n"
    "Apply Calibration Heuristic 3 (planned vs operational): "
    "originated-loan volume vs serviced-loan volume vs balance-sheet "
    "loan volume are different — UPST in particular emphasizes "
    "origination volume which is not balance-sheet risk. AFRM "
    "headline 'GMV' is gross merchandise volume not Affirm revenue.\n\n"
    "Apply Layer 3 Rule 7: material BNPL merchant relationships "
    "should appear in the merchant's 10-K (e.g. AMZN/Affirm "
    "checkout integration). The framework's bar here is higher "
    "because of the disclosure-quality nature of credit-loss "
    "reserves — many claims will score UNVERIFIABLE.\n\n"
    "**Calibration note for this cohort:** the framework is built "
    "for divergence detection where M-sources are authoritative "
    "registries; consumer-credit-quality assertions don't have a "
    "clean registry analog. Expect more UNVERIFIABLE than other "
    "cohorts; emissions should be rare and high-conviction when "
    "they happen."
)


COMMON_COUNTERPARTY_CIKS: dict[str, str] = {
    # Merchant partners (BNPL counterparties)
    "Amazon (AMZN)":               "0001018724",
    "Walmart (WMT)":               "0000104169",
    "Target (TGT)":                "0000027419",
    "Apple (AAPL)":                "0000320193",
    "Shopify (SHOP)":              "0001594805",
    # Bank partners (UPST counterparties)
    "JPMorgan (JPM)":              "0000019617",
    "Capital One (COF)":           "0000927628",
    "Goldman Sachs (GS)":          "0000886982",
    "Bank of America (BAC)":       "0000070858",
    # Compare-set
    "Block / Square (SQ)":         "0001512673",
    "PayPal (PYPL)":               "0001633917",
}


CUTOFF = "2026-05-16"
