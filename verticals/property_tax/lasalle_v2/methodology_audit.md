# Methodology Audit — Layer 3 Discipline Rules vs Detroit Property Tax

For each of the 6 operational-discipline rules from `signalos/ARCHITECTURE.md` Layer 3, I assess whether and how it transfers to the Detroit property-tax-uncap problem. The rules were derived from public-company backtests (eVTOL + 3D-printing cohorts) and held out against this domain.

---

## Rule 1 — Read the notes section, not just the marketing tier

**Public-co version:** highest-density divergence signals live in financial-statement notes (Commitments and Contingencies, Related Party, Going Concern), not Item 1 Business.

**Property-tax equivalent:** does the framework read deeper records beyond the assessor's headline TV / SEV / sale_date / sale_price? Currently: largely no.

**What the assessor publishes (the marketing tier):** TV, SEV, ETCV, sale_date, sale_price_record, owner, homestead_pct, property_class, NEZ district. All read.

**What the assessor / county also publish or hold but the framework does NOT read (the notes):**

| Record | Why it matters | Currently read? |
|---|---|---|
| **Form L-4260 (Property Transfer Affidavit)** filings — submitted to local assessor on every transfer | Direct evidence of whether buyer filed; absence is the actual MCL 211.27a(10) violation, not the TV gap | **No** — inferred circularly from "TV not reset" |
| **Board of Review (BoR) petition log** — annual appeal docket | A reduced SEV that holds the floor for the post-transfer uncap can be the result of a successful appeal; collusive or false-income appeals are a distinct under-payment pattern | **No** |
| **Michigan Tax Tribunal docket** | Same as BoR but for higher-value commercial appeals | **No** |
| **PRE certification / denial letters** | If PRE was denied for a specific year, the property should be at non-homestead millage — comparing assessor PRE % to actual denial history catches mid-period reversals | **No** |
| **NEZ Homestead certificate filings** (City of Detroit, application + approval) | NEZ benefit requires owner-occupant filing + approval; absence of certificate while showing NEZ-rate millage = unsupported claim | **No** |
| **Land Bank conveyance contract terms** | Side Lot vs Auction vs Rehabbed have different uncap-exemption status; the contract terms determine which | **No** |

**Verdict:** Rule 1 transfers cleanly. The framework currently reads the assessor's headline tier and the deed recorder. The "notes" — PTA log, BoR docket, tribunal docket, PRE letters, NEZ certificates — would shift the analysis from "TV looks low" (a *consequence*) to "the buyer never filed L-4260" (the *violation itself*). The 1553 GLYNN CT case in `analysis.md` shows the difference: we can confidently say the TV is too low, but we cannot directly say the buyer failed to file the affidavit — only infer it from the gap.

**Most actionable upgrade per rule 1:** the FOIA-able PTA log from Detroit Assessor's office is a direct M-source for the actual claim violation, not a downstream consequence.

---

## Rule 2 — Coverage assessment before reading absences as signal

**Public-co version:** distinguish corroborated / contradicted / no-data; pair every "no-data" with which sources covered which actor types.

**Property-tax application:** documented in detail in `coverage_assessment.md`. The single largest mis-read in current framework output is treating `mls_sales` as a true MLS-tier source when 99.9999% of its rows are just the assessor's own sale field repackaged. Citywide, 4 of the 5 nominal M-sources (Redfin, Zillow, PropStream, ATTOM) are dark code paths with zero rows in the database snapshot.

**Concrete mis-read on the case parcel (1553 GLYNN CT):** the framework's `method_agreement = both` flag suggests two independent methods agreeing. But Method A (sale-price) and Method B (SEV) are both derived from the same source: the assessor's record. There is no true cross-record corroboration here. The signal is still real (TV is below SEV the assessor itself published, which is a tautological "the assessor's own number contradicts itself"), but the "agreement" framing is misleading.

**Verdict:** Rule 2 transfers cleanly and the framework violates it. Every "method_agreement = both" line should be re-read as "two interpretations of one source agree" — this is not coverage convergence.

---

## Rule 3 — Divergence detection ≠ solvency / completeness model

**Public-co version:** a name passing divergence checks (every claim corroborated) can still fail for cash-burn reasons the framework is structurally blind to.

**Property-tax equivalent:** the framework answers "did the assessor reset TV after a transfer per MCL 211.27a?" — not "is the property's tax burden correct." The latter requires a much wider set of checks the framework does not perform:

| Tax-evasion category | Currently scored? | Why missed |
|---|---|---|
| Improper PRE on LLC-owned property (MCL 211.7cc) | **No** | Not a divergence between R-sale and M-deed; it's a divergence between R-claim and M-occupancy. Different f, different M. **20,180 LLC-owned parcels claim 100% PRE citywide.** |
| Improper NEZ Homestead claim by non-occupants | **No** | Same pattern as PRE; different exemption |
| Collusive / appeal-secured under-SEV | **No** | The framework treats SEV as authoritative; it cannot detect "the SEV itself is wrong" |
| Income-property under-assessment (commercial SEV not reflecting actual NOI) | **No** | Requires rent-roll M-source (CoStar, HUD HAP, listed rents) |
| Personal property (PA 198 / IFEC abatements with shaky qualification) | **No** | Different statute, different M |
| Renaissance Zone (PA 376) abuse where TV freeze is allowed but qualification weak | **No** | Different exemption framework |
| Ag exemption (qualified agricultural use) on non-farming property | N/A in Detroit | Out of scope |

**Verdict:** Rule 3 transfers strongly. The framework is a divergence-detector for ONE specific f (TV-must-reset-on-transfer). It systematically misses the broader population of property-tax-underpayment patterns. The PRE-on-LLC pattern alone (20,180 parcels citywide) is a larger non-compliance population by parcel count than the entire missed-uncap finding (8,126 parcels). Adding it requires a different f, not a tweak to the existing one.

A second framework, with f = "PRE eligibility requires owner-occupancy under MCL 211.7cc" and M = "ownership type from assessor + occupancy proxies (USPS NCOA, voter registration, water bill address)," would cover this gap. It is genuinely a different vertical, not a feature.

---

## Rule 4 — Subagent firewall for blinded cohort scoring

**Public-co version:** when analyst has outcome knowledge for some/all cohort items, hindsight contaminates query selection and scoring; spawn isolated subagents per item.

**Property-tax application:** This re-run IS a subagent-firewall instance. The blinding worked in one direction (no access to the prior LASALLE writeup) and produced an independently-arrived-at GLYNN CT case that overlaps the LASALLE pattern but isn't identical. Whether the outputs match the prior analysis A/B is an empirical question the operator will answer.

**Where the rule is operationally relevant for property tax going forward:**
- **Citywide overdue ranking.** If the analyst sees top-10 cases in advance, hindsight contaminates which severity thresholds they tune. The audit-priority-score thresholds (column literally named `fraud_score` in v1's source; currently 30 / 40 / 60 / 80 cuts) appear hand-tuned; whether they survive a held-out neighborhood test is unverified.
- **Single-deal forensic DD does NOT need this** (per Layer 3 explicit carveout). For a single-parcel investigation (e.g. someone hands the analyst "investigate 1553 GLYNN CT"), seeing all the data and probing adversarially is the right mode.

**Verdict:** Rule 4 transfers cleanly to citywide cohort scoring; not relevant for single-parcel work. The discipline-rule itself does not change conclusions for the case parcel — it changes confidence in the citywide rankings.

---

## Rule 5 — Stock-for-services / vendor-payable-to-equity = generic distress fingerprint

**Public-co version:** vendor invoices settled in shares = high-signal flag; recurring across SRFM, LILM, etc.

**Property-tax application:** N/A directly. There's no equivalent of "issuing equity to settle a creditor" in residential property tax.

**The closest property-tax analogue,** if forced: $0 quit claims used to extinguish recorded mortgage / lien liabilities by transferring the property to a sibling LLC instead of paying the debt. The 2024-06-18 HOF I → HOF I REO 5 LLC $0 QC on the case parcel is structurally similar — moving the asset into a different entity wrapper for accounting reasons rather than paying. But in property tax this is mostly benign (entity restructuring) rather than a distress signal.

**Verdict:** Rule 5 does NOT transfer. The closest analogue is too noisy to use as a flag.

---

## Rule 6 — Calibration heuristics tuned on known cohorts are contaminated

**Public-co version:** scoring rules authored after seeing cohort outcomes carry hindsight even through subagent blinding; require strict train/test split.

**Property-tax application — what does NOT transfer cleanly:**

The audit-priority-score weights (column `fraud_score` in v1's `analysis/uncap.py`, lines 290-399) were authored after the analyst already knew the LASALLE pattern. Specifically:
- The 30-point bucket for `instr == "QC" and zero and prior_arms_length` directly encodes the LASALLE shape.
- The 30-point TV-suppression-depth bucket (TV/SEV < 20%) sets the cutoff right where LASALLE sits.
- The "consideration suppression" 15-point dimension is calibrated to the LASALLE deed-vs-MLS-price gap.

These are reasonable in retrospect, but they are calibration heuristics promoted to scoring without held-out validation. Per Rule 6, they are contaminated for any future evaluation that includes the LASALLE class of cases.

**Concrete consequence:** the case parcel (1553 GLYNN CT) gets an audit-priority score of 95 (column literally named `fraud_score`) partly because it shares structural features with LASALLE that the score weights were built around. The same parcel, scored against a held-out blind test cohort, might rank 60 or 70. The score is not falsifiable in its current form.

**What the property-tax domain has that the public-co domain doesn't (rules need adjustment):**
- **Statutory exemptions are well-defined and numerous.** MCL 211.27a(7) lists 10+ specific transfer exemptions (family, entity restructuring, qualified ag, conservation easements, leases-under-35-years, etc.). Public-co divergence checks usually don't have this many built-in legitimate exceptions. The framework needs an explicit exemption-screen step that the public-co version does not need.
- **Penalty for the underlying non-filing is tiny ($200 max for L-4260 non-filing per MCL 211.27a(10)).** Compare to public-co cases where SEC enforcement penalties scale with the harm. This means a high-confidence audit-priority finding in property tax has very low individual-actor consequences — the policy lever is enforcement reform, not individual prosecution. Severity-tier interpretation must reflect this.
- **Population is hundreds of thousands of small actors,** not dozens of large ones. False-positive cost per case is much lower (one homeowner gets a corrected tax bill) but aggregate false-positive cost across the population can be politically large. The severity thresholds need a precision-vs-coverage tradeoff calibration that the public-co framework does not need at the same scale.

**Verdict:** Rule 6 strongly applies and the current framework violates it. The audit-priority-score weights (column `fraud_score` in v1's source) need a held-out neighborhood-or-zip cohort to validate. As of this re-run, the audit-priority score should be treated as a heuristic ranking aid, not a calibrated probability.

---

## Summary table — rule transfer to property tax

| Rule | Transfers? | Most important consequence |
|---|---|---|
| 1. Read the notes | **Yes** | PTA log, BoR docket, PRE/NEZ certificates are unread "notes" — direct violation evidence vs downstream consequence |
| 2. Coverage before absence | **Yes** | `mls_sales` is 99.9999% assessor-record; `method_agreement = both` is misleading |
| 3. Divergence ≠ solvency | **Yes (strongly)** | PRE-on-LLC alone (20,180 parcels) is bigger than the missed-uncap finding by parcel count |
| 4. Subagent firewall | **Yes (cohort only)** | Citywide rankings need it; single-parcel work doesn't |
| 5. Stock-for-services | **No** | Closest analogue ($0 QC for entity restructuring) is too noisy |
| 6. Hindsight calibration | **Yes (strongly)** | The audit-priority-score weights (column `fraud_score` in v1) encode the LASALLE shape; not held-out validated |

**Net change to the case parcel finding:** unchanged on direction (1553 GLYNN CT is a real overdue uncap). Reduced confidence in the score-95 magnitude (artifact-flag inflation per rule 2). Expanded scope of "what should be in scope" per rule 3 — the right question for citywide work is not "how much overdue uncap is there?" but "how much property-tax exposure is there from all forms of evasion the divergence framework can or should reach?" The PRE-on-LLC population, an order of magnitude larger by parcel count, is the highest-ROI extension.
