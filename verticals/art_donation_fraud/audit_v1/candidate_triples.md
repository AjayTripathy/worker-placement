# Candidate Sibling R/f/M Triples — art_donation_fraud

Per Layer 3 Rule 3: the one fraud shape currently wired (portfolio-pattern flag against IRC §170(e)(1)(A) using Met+MoMA acquisition records) is one of several sibling triples within the vertical. Each is a separate R-claim with a separate f relationship and a partly-overlapping M-side. Ranked by **build cost ascending** then **ROI descending**.

---

## 1. Per-work auction-to-donation match (the named v1 rule, but properly wired)

- **R:** the donor's claimed FMV on a specific Form 8283 (or inferred from museum acknowledgement of the work).
- **f:** Treas. Reg. §1.170A-13(c) — claimed FMV must equal arm's-length market value. An auction sale by the same buyer-of-record within ~36 months is the most directly comparable evidence; the deduction is capped at (or close to) the auction price absent substantiated appreciation.
- **M:** Met + MoMA acquisition records (already wired) cross-joined with auction-house lot results.
- **Build cost:** **medium** (paid-vendor connector: Artnet $480/yr OR free Artsy xapp_token + reverse-engineering). Per the connector-discipline rule, this is the **binding constraint** for the vertical — once shipped, the existing cohort runner becomes per-work fraud confirmation engine instead of a portfolio flag.
- **Why this is properly distinct from the v1 rule:** the v1 fires on structural features of the donor's portfolio (volume × volatility × clustering). The properly-wired auction-match rule fires on per-work evidence (donor X bought W for $A at Christie's on date T; donor X claims $B FMV on Form 8283 for W gifted to Met on date T+12mo).

---

## 2. §170(e)(7) early-deaccession recapture (declared, unimplemented)

- **R:** the donor's claimed FMV on the original donation.
- **f:** IRC §170(e)(7) — if the donee disposes of the work within 3 years for less than claimed FMV, the donor's deduction is mandatorily recomputed to the disposition price. Excess is recaptured as ordinary income.
- **M:** Museum acquisition records (already wired) cross-joined with museum deaccession events.
- **Build cost:** **medium-high.** Deaccession data is fragmented: museums sometimes publish in annual reports, sometimes via auction lot consignor designations ("Property from the Collection of X Museum"), sometimes only via FOIL or state nonprofit disclosure law. No central registry. Per-museum FOIL would be the highest-quality path; the auction-side scrape would also surface most deaccessions naturally.
- **Why valuable:** this is the **lawsuit-grade** signal. Unlike the auction-match rule (which requires inferring the claimed FMV), §170(e)(7) is mandatory — the math is unambiguous once the deaccession event is observed.

---

## 3. Private-operating-foundation passthrough timing

- **R:** the donor's contribution to a private operating foundation in year T, claiming full FMV.
- **f:** §170(b)(1)(A) gives full FMV deduction for gifts to qualifying PoFs (vs. 30%-of-AGI limit for non-operating foundations). The PoF then donates to a museum at some later date. If the PoF's window is short and the museum-gift announcement value differs from the donor-claim value, that's a flag.
- **M:** 990-PF filings (free, IRS bulk) + museum acquisition records (already wired).
- **Build cost:** **medium.** 990-PF connector needed; mostly XML parsing. Match logic is on PoF name + work attribution.
- **Why valuable:** this is the sophistication tier above straightforward FMV inflation. The donor uses the PoF as a tax-deduction-now-museum-gift-later vehicle.

---

## 4. Appraiser pattern detection

- **R:** the specific appraiser named on Form 8283 Section B.
- **f:** Treas. Reg. §1.170A-13(c)(5) defines "qualified appraiser" and excludes those with a financial relationship to the donor or donee. The IRS Art Advisory Panel publishes appraisers whose work has been repeatedly rejected.
- **M:** IRS Art Advisory Panel annual reports + tax-court opinions naming appraisers + the appraiser's own published market reports.
- **Build cost:** **low-medium.** Annual reports are PDF-scrape; tax-court opinions are on Google Scholar.
- **Why valuable:** doesn't catch any individual donor but identifies appraisers who function as repeat tax-shelter facilitators. The Art Advisory Panel has flagged certain names for decades; surfacing those donors who use those appraisers is a high-precision signal.

---

## 5. Capital-gains-event correlator

- **R:** the donor's claimed FMV deduction in tax year T.
- **f:** the donation's tax-shelter value is highest when used to offset a large concurrent capital gain. A clustered donation in the same year as a known stock-sale event is the highest-leverage tax-planning moment.
- **M:** SEC EDGAR Form 4 / Form 144 (already wired in `public_co/edgar.py`) cross-joined with museum donation records (already wired).
- **Build cost:** **low** (we already have edgar.py; ~3 hr to integrate).
- **Why valuable:** doesn't directly prove inflation but identifies the donors who have the strongest tax-planning *motive* in the year they cluster their donations. Combined with #1 (per-work auction match), this is the strongest fraud-risk fingerprint.

---

## 6. Form 990 Schedule M reconciliation

- **R:** the museum's reported aggregate non-cash contribution dollar value on Schedule M.
- **f:** sum of inferred fair-market values for all gifts received in the year should reconcile to Schedule M's "Art, Historical Treasures" line within a reasonable margin.
- **M:** 990 Schedule M bulk (`s3://irs-form-990/`) + museum acquisition records (already wired).
- **Build cost:** **low-medium.** 990 bulk parser; we have the museum side.
- **Why valuable:** aggregate sanity check, not per-case. Catches museums whose Schedule M is materially out-of-line with their visible gifts — which would imply either (a) lots of hidden gifts the public doesn't see, or (b) reported aggregate is inflated by appraisal aggressiveness.

---

## Cost-vs-ROI summary

| Rank | Triple | Build cost | Why pursue | Notes |
|---|---|---|---|---|
| 1 | Per-work auction match | medium (paid-vendor) | **binding constraint** for the whole vertical | Artnet/Artprice subscription |
| 2 | §170(e)(7) recapture | medium-high (FOIL per museum + auction scrape) | Lawsuit-grade signal | Mandatory recapture math |
| 3 | Capital-gains-event correlator | low (reuse edgar.py) | Highest tax-planning motive donors | Quick win |
| 4 | Appraiser pattern | low-medium (PDF scrape) | High-precision facilitator detection | Annual report parse |
| 5 | 990 Schedule M reconciliation | low-medium (XML bulk) | Aggregate sanity check | Catches museum-level skew |
| 6 | PoF passthrough timing | medium (990-PF connector) | Sophistication tier | XML parsing |

**Highest-ROI move:** ship the paid auction-comp connector (#1) AND the capital-gains-event correlator (#3) — together they convert this vertical from "structural pattern flagger" into "per-case fraud lead generator." Estimated combined effort: 1 day once Artnet trial is active.
