"""
Fresh-universe cohort for framework alpha test — shortable subset.

8 names that:
  1. Passed the AIRO-signature mechanical screen ("stock for services"
     AND "material weakness" in FY 10-K filed before 2025-05-15)
  2. Are $100M-$2B mcap at 2025-05-15 entry
  3. Are actually shortable (price >= $5, daily $vol >= $1M)
  4. Are NOT in any existing Signal OS cohort

Why this matters: the original v0 AIRO screen produced 15 names but 11
were unshortable (sub-$5 retail-blocked or sub-$1M daily-$vol hard-to-
borrow). The 11 unshortables included most of the catastrophic-short
winners (LBUY -99%, VIVK -99%, GNPX -93%, CDIX -81%, WKHS -72%). The
shortable subset alone has a much more dispersed return profile that
makes a tradable-strategy test meaningful.

Forward 2025-05-15 → 2026-05-15 (already on disk):

  TK    industry           price   12mo return
  LRHC  real-estate brk    $1120   -99.9%
  KULR  energy storage     $11.84  -69.6%
  HDSN  refrigerants       $7.88   -37.6%
  PESI  hazmat/nuclear     $9.57   +1.8%
  CWCO  water utility      $25.62  +13.1%
  CDNA  diagnostic biotech $16.10  +24.0%
  ALMU  compound semis     $12.22  +103.4% (catalyst)
  KLIC  semi equipment     $33.51  +204.5% (catalyst)

Short basket mean: -17.5% (catalyst rallies dragged it negative).
Median: +18%. Sector-hedged behavior is what we're testing.

Test question: does the framework's multi-source aggregation correctly
suppress the catalyst-rally names (KLIC, ALMU, CDNA) while keeping the
catastrophic shorts (LRHC, KULR, HDSN)?

Cutoff: 2025-05-15.
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
    CohortMember(ticker="LRHC",
                 name="La Rosa Holdings Corp.",
                 notes="Real-estate brokerage roll-up. AIRO-signature hit. "
                       "Forward -99.9% — catastrophic short."),
    CohortMember(ticker="KULR",
                 name="KULR Technology Group, Inc.",
                 notes="Energy storage / battery safety tech / Bitcoin treasury. "
                       "AIRO-signature hit. Forward -69.6%."),
    CohortMember(ticker="HDSN",
                 name="Hudson Technologies, Inc.",
                 notes="Refrigerant recovery & reclamation. AIRO-signature hit. "
                       "Forward -37.6%."),
    CohortMember(ticker="PESI",
                 name="Perma-Fix Environmental Services, Inc.",
                 notes="Hazmat / nuclear waste processing. AIRO-signature hit. "
                       "Forward +1.8%."),
    CohortMember(ticker="CWCO",
                 name="Consolidated Water Co. Ltd.",
                 notes="Desalination / water services. AIRO-signature hit. "
                       "Forward +13.1%."),
    CohortMember(ticker="CDNA",
                 name="CareDx, Inc.",
                 notes="Diagnostic biotech (organ-transplant testing). "
                       "AIRO-signature hit. Forward +24.0%."),
    CohortMember(ticker="ALMU",
                 name="Aeluma, Inc.",
                 notes="Compound semiconductors (GaAs/InP for AI/quantum). "
                       "AIRO-signature hit. Forward +103.4% — catalyst rally."),
    CohortMember(ticker="KLIC",
                 name="Kulicke & Soffa Industries, Inc.",
                 notes="Semiconductor packaging equipment. AIRO-signature hit. "
                       "Forward +204.5% — semi capex catalyst rally."),
]


CUTOFF = "2025-05-15"

COHORT_CONTEXT = (
    "FRESH SHORTABLE UNIVERSE for framework alpha test. 8 small-to-mid-caps "
    "($550M-$1.75B mcap at 2025-05-15) that all passed the AIRO-signature "
    "mechanical screen ('stock for services' AND 'material weakness' in FY "
    "10-K). All 8 are actually shortable (price >= $5, daily $vol >= $1M). "
    "NONE overlap with any existing Signal OS cohort. \n\n"
    "Test question: does the framework's multi-source aggregation produce "
    "additional discrimination beyond the single-signal screen? In particular, "
    "can it correctly suppress the catalyst-rally names (KLIC +204%, ALMU "
    "+103%, CDNA +24%) while keeping the catastrophic shorts (LRHC -100%, "
    "KULR -70%, HDSN -38%)? \n\n"
    "Industries are heterogeneous (real-estate brokerage, energy storage, "
    "refrigerants, nuclear waste, water utility, diagnostic biotech, "
    "compound semis, semi packaging equipment). The framework should "
    "adjudicate each name's claims through its standard heuristics — "
    "counterparty disclosure, operational capacity tests, claim evolution, "
    "USPTO patents, sec_filings cadence, etc. — and produce an emit "
    "decision via the dual-gate truth_signal rule "
    "(red>=1 OR severe>=2 OR (composite>=0.10 AND n_flags>=2))."
)

# Common counterparties for cross-checks.
COMMON_COUNTERPARTY_CIKS = {
    "Amazon":     "0001018724",
    "Microsoft":  "0000789019",
    "Walmart":    "0000104169",
    "Tesla":      "0001318605",
    "Apple":      "0000320193",
    "Alphabet":   "0001652044",
    "Nvidia":     "0001045810",
}
