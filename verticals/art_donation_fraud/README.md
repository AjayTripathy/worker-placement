# art_donation_fraud — charitable contribution fraud on art donations

**Signal = R − f(M)** for inflated fair-market-value (FMV) deductions on art donated to qualified museums.

## The fraud

Under §170(e), donating long-term-held appreciated tangible personal property to a qualified §501(c)(3) lets the donor deduct **fair market value**, not cost basis. The fraud:

1. Donor (or buyer-of-record) acquires work W for $X (basis).
2. Work is held >12 months (so deduction is FMV not basis).
3. Donor commissions an appraiser to value W at $Y where $Y >> $X.
4. Donor donates W to a museum.
5. Donor claims $Y deduction × marginal rate ≈ tax savings.
6. Treasury loss = ($Y − true_FMV) × marginal rate.

The IRS Art Advisory Panel (1968-present) reviews appraisals >$50K and historically reduces ~30% of submitted valuations by ~30%. Aggregate fraud estimate: ~$1B+/yr. The §170(e)(7) recapture provision (added 2006): if the museum disposes of the work within 3 years for less than the claimed FMV, the donor's deduction is recomputed to the disposition price.

## R / f / M

- **R:** the FMV the donor claims on Form 8283 (private — inferred from museum acknowledgements, gift size disclosed in press releases, or matched against the donor's recent auction purchase price).
- **f:** Treas. Reg. §1.170A-13(c) — claimed FMV must equal what a willing buyer would pay in the regular market. Auction comparables for the same artist / period / size are the regulatory benchmark.
- **M:** museum collection databases (acquisition records with credit lines), auction sale records (Christie's / Sotheby's / Phillips / Heritage public archives), §170(e)(7) deaccession events.

## Pipeline state (v1)

| Component | Status |
|---|---|
| Met collection connector | shipped |
| MoMA collection connector | shipped |
| Sotheby's lot connector | partial (best-effort scrape) |
| Cohort runner | shipped |
| Auction → donation match rule | shipped |
| §170(e)(7) recapture rule | scoped, not yet wired |

See `audit_v1/fraud_report.md` for current output and `audit_v1/connectors_to_add.md` for the M-source roadmap.
