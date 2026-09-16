# Methodology Audit — art_donation_fraud v1

Per-rule transfer of the Layer 3 operational-discipline rules from top-level `ARCHITECTURE.md`. Parallel structure to `verticals/rent_stabilization/audit_v1/methodology_audit.md` and `verticals/property_tax/lasalle_v2/methodology_audit.md`.

---

## Rule 1: Read the notes

**The rule:** the most signal-dense parts of a filing live in notes/commentary sections (Notes-to-financials in 10-Ks; credit-line metadata in museum records; Bureau-of-Review proceedings in tax records). Don't skim past them.

**Transfer to art_donation_fraud:** **strong**, with a narrow definition of "notes."

The museum credit-line is the equivalent of a 10-K's Note 15 here. It carries:
- Donor identity (often "Mr. and Mrs. X" pattern that requires careful parsing)
- Gift year (sometimes different from accession year)
- Memorial/honorary attribution ("in memory of Y") which often signals an estate disbursement
- Foundation passthrough patterns ("Gift of the X Foundation" vs "Gift of X")
- "Promised gift" vs "gift" vs "bequest" prefix — the partition between living-donor active-collection patterns and estate dispersals

The v1 parses these but does NOT fully use them yet. The partition between "Gift of" and "Bequest of" is captured in `gift_year` but the runner's archetyping heuristic uses cluster-year-share, not credit-line prefix. That's a known v2 cleanup.

Beyond the credit-line, the "notes" analogue extends to:
- Museum press releases announcing major donations (often disclose a value range)
- Museum exhibition catalogues (provenance section gives ownership history)
- ARTnews / Art Newspaper coverage of named gifts (sometimes prints the appraised value)

None of these are currently parsed. They're the agent-doable next step after the auction-comp connector.

---

## Rule 2: Coverage assessment before scoring

**The rule:** know what the M-source covers before reading 0 hits as "no fraud."

**Transfer:** **strong**, this is the most important Layer 3 rule for this vertical because the M-side is the weakest part.

Full breakdown in `coverage_assessment.md`. Headline:
- The v1 covers Met + MoMA only, which is ~30% of major-donor art philanthropy by dollar volume.
- The R-side (Form 8283 claimed FMV) is structurally invisible. Every signal is inferred from M alone.
- The two cleanest fraud shapes (auction-to-donation match per work; §170(e)(7) recapture event) require connectors that are not yet wired.

Practical implication: the 1,218 donors NOT flagged by the v1 cohort run cannot be read as "low fraud risk." They could equally be donors who give to Whitney + Guggenheim instead, or who donate single high-value works (failing the volume threshold), or whose name normalizes to multiple keys.

---

## Rule 3: Divergence ≠ scope

**The rule:** the one R/f/M shape you've wired catches one fraud pattern. Sibling triples in the same vertical address different patterns and shouldn't be conflated with "no fraud" if your one rule didn't fire.

**Transfer:** **strong**, with five clear sibling triples worth wiring.

See `candidate_triples.md` for the full list. Headline:
- The v1 fires only on portfolio-pattern flags (volume × volatility × clustering).
- The §170(e)(7) recapture rule is declared but not implemented (needs deaccession connector).
- Auction-to-donation per-work match (the literal fraud shape) is declared in spirit but currently fires on portfolio features instead of per-work — needs Artnet/Artprice.
- Other shapes: (a) Form 990 Schedule M reconciliation, (b) private-operating-foundation passthrough timing, (c) appraiser-history pattern (some appraisers are repeat Art Advisory Panel rejects), (d) capital-gains-event correlation (donor's stock-sale year matches gift cluster year).

---

## Rule 4: Subagent firewall for blinded scoring

**The rule:** for cohort screens where you already know some outcomes, spawn subagents to score blind so hindsight contamination doesn't bias severity assignment.

**Transfer:** **marginal** at v1 stage. Becomes important if/when we backtest against known fraud cases.

There ARE known cases in the public record:
- *Hostetter v. Commissioner* (T.C. Memo 2018-101) — art appraisal inflation, IRS won
- The *Crystal Cathedral* art appraisal scheme (2010s-era civil settlements)
- Various conservation easement abuse cases (adjacent doctrine, often involving art-as-property)
- Mark Hostetter, Hari Hodi, and several "art syndicate" tax-shelter promoters publicly named in IRS-DOJ enforcement actions

If we ever build a held-out test cohort of these known cases, blinding the scoring agent (per the property_tax/lasalle_v2 pattern) becomes essential. For now, the rule isn't binding because we have no labeled outcomes to leak.

---

## Rule 5: Stock-for-services as distress flag

**The rule:** vendor-payable-to-equity conversions are a generic distress fingerprint in public-co backtests.

**Transfer:** **does not transfer** directly. No equity-for-services dynamic in personal charitable contributions.

The closest analogue might be: art-donation-in-lieu-of-cash settlement of a personal obligation (e.g., a divorce settlement transferring art to a charity to satisfy a property-division equalization). That's exotic and not currently in scope.

---

## Rule 6: Hindsight calibration discipline

**The rule:** thresholds tuned on the cohort you're scoring are hindsight-fitted. Set them from prior held-out data or document the tuning.

**Transfer:** **moderate**, currently a known weakness.

The `AUCTION_TO_DONATION_MATCH` rule's thresholds (≥25 works, ≥50% market-volatile share, ≥60% year-cluster, ≥100 portfolio scale) are author-declared. They were chosen by looking at the Met+MoMA distribution and picking points that gave a reasonable-looking flagged-donor list. That's hindsight-fitting on the same dataset.

Honest mitigations available:
1. Hold out a museum (e.g., MoMA-only training, Met-only test) and verify thresholds generalize.
2. Pre-register thresholds against the IRS Art Advisory Panel's published "30% of submissions, 30% reduction" baseline rather than against the visible flagged list.
3. Once auction-comp connector is wired, validate that the structural-flag list overlaps with the per-work-flag list — if not, the structural thresholds need refinement.

None of these are done in v1. The threshold tuning is the second-largest piece of methodological debt after the missing auction connector.

---

## Bottom line

The single highest-leverage methodological improvement is calibrating Rule 1 (parse credit-line prefix as a partition between living-donor and bequest patterns) and Rule 2 (add Whitney + Guggenheim + other top US museums) before adding the paid auction connector. Both are agent-doable in the next session. Together they would tighten the false-positive rate on the existing rule without needing the binding-constraint paid M-source.
