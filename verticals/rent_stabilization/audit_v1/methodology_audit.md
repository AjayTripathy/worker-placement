# Methodology Audit — Layer 3 Discipline Rules vs NYC Rent Stabilization

For each of the 6 operational-discipline rules from `signalos/ARCHITECTURE.md` Layer 3, I assess whether and how it transfers to NYC rent stabilization. The rules were derived from public-company backtests (eVTOL + 3D-printing cohorts) and held out against the property-tax domain in `verticals/property_tax/lasalle_v2/`. This audit asks the same question of rent stab.

---

## Rule 1 — Read the notes section, not just the marketing tier

**Public-co version:** highest-density divergence signals live in financial-statement notes (Commitments and Contingencies, Related Party, Going Concern), not Item 1 Business.

**Rent-stab equivalent:** does the framework read deeper records beyond the listing tier (the landlord's marketing) and the building characteristics tier (PLUTO)? Currently: no.

**What the framework reads (the marketing tier):** PLUTO building characteristics; J-51 cross-join; StreetEasy listings; ACS rent medians.

**What the framework does NOT read (the notes):**

| Record | Why it matters | Currently read? |
|---|---|---|
| **DHCR / HCR Annual Apartment Registration** — owner files annually per unit, including legal regulated rent, preferential rent, tenant of record (redacted), registered services | The authoritative legal regulated rent. Replaces borough-estimate base rent with measured base rent for every unit ever registered. | **No** — `gap.py:135` falls back to `BASE_RENT_1969.get(borough)` whenever per-unit data is missing, which is always |
| **J-51 expiration / abatement certifications** | Distinguishes active-benefit window from 35-year stabilization tail. Tail-period units are higher-fraud-risk because owners often forget the tail obligation. | **Half-read** — tail is included in `_load_j51_bbls` (`nyc_pluto.py:168`) but not flagged separately downstream |
| **HPD building registration** (managing agent, head officer, registered owner) | Owner identity for entity resolution; `nyc_pluto.py:58` does naive `_is_entity` string-match on PLUTO `ownername` | **No** |
| **DHCR rent reduction orders** (issued on past tenant complaints) | Past-adverse-outcome history on the same building — strong base rate prior. A building with 3 prior reduction orders is a very different signal than one with 0. | **No** |
| **DOF RPIE filings** | Building-wide actual collected rent, independent of listings | **No** |
| **ACRIS deed history** | Pre-HSTPA, vacancy-bonus rights triggered on lease-end. Knowing transfer history identifies units where owners had legitimate basis for legal rent above pure RGB compounding. | **No** |
| **Building-wide DOB CO + alteration history** | IAI claims must be substantiated by permits and contractor receipts. A claimed $40K kitchen IAI with no DOB-recorded plumbing work is fraud. | **No** |

**Verdict:** Rule 1 transfers cleanly. The framework currently reads the listing tier (R) and the PLUTO tier (M-coarse). The "notes" — DHCR registrations, J-51 certifications, HPD registrations, rent reduction orders, RPIE, ACRIS, DOB permits — would shift the analysis from "the listed rent looks too high relative to a borough-baseline estimate" (a *consequence-side circumstantial* signal) to "the owner registered $X with DHCR in 2020, claimed a $Y IAI, but no DOB permit substantiates the work" (a *direct* statutory violation).

**Most actionable upgrade per Rule 1:** DHCR Annual Apartment Registration. Same shape as the L-4260 PTA log addition for property tax — moves from inference to measurement.

---

## Rule 2 — Coverage assessment before reading absences as signal

**Public-co version:** distinguish corroborated / contradicted / no-data; pair every "no-data" with which sources covered which actor types.

**Rent-stab application:** documented in detail in `coverage_assessment.md`. The framework's nominal M-side has two real signals (PLUTO + J-51) and several silent failure modes that produce `None` GapResults indistinguishable from "compliant":
- Building filtered out by `unitsres < 6` → silent `None`
- `stabilization_confidence < 0.4` → silent `None` (`gap.py:63`)
- StreetEasy returned no listings (Cloudflare block, parse failure, off-platform listing) → silent `None`
- Census ACS returned no rents for the ZIP → silent `None`

In all four cases, downstream consumers see "no signal for this building" and have no way to distinguish "no overcharge happening" from "no coverage of this building's unit type."

**Concrete mis-read pattern:** the worked example in `analysis.md` (24-unit C4 pre-war Brooklyn building) gets a clean signal because all four PLUTO checks pass cleanly. Move that building three blocks east into a 5-unit pre-war R6 zone, and the same overcharge becomes invisible because of the `unitsres >= 6` floor — even though small-multifamily is exactly the cohort with the highest small-landlord noncompliance rate.

**Verdict:** Rule 2 transfers cleanly and the framework violates it. Every output should carry a coverage statement (which M-sources were consulted and which conclusion they returned). The current binary `GapResult | None` return type encodes "we found a problem" vs "we did not find a problem" but not "we cannot speak to this building."

---

## Rule 3 — Divergence detection ≠ solvency / scope model

**Public-co version:** a name passing divergence checks (every claim corroborated) can still fail for cash-burn reasons the framework is structurally blind to.

**Rent-stab equivalent:** the framework answers "does the listed rent exceed the estimated maximum legal stabilized rent under RSL §26-510?" — not "is this owner committing rent-related fraud." The latter requires checks the framework does not perform. Inventory of what's missed:

| Fraud category | Currently scored? | Why missed |
|---|---|---|
| **J-51 obligation while charging market rents** (Roberts v. Tishman Speyer territory) | **Half-no.** `J51_OBLIGATION` declared in `rules/__init__.py:21` but `implementation=None`. LLM-only path, never wired to compiled f. | Same shape as RSL_OVERCHARGE but predicate is "J-51 obligation in force" rather than "vintage-inferred RSL coverage." Cross-join on `j51_confirmed` × listing exists but no compiled f fires distinctly. |
| **IAI (Individual Apartment Improvement) inflation** | **No** | Requires DOB permits + contractor records + DHCR-registered IAI claims. None wired. |
| **Preferential rent rider misuse** — listing rent registered as "preferential," then snap-back to a higher legal rent on lease renewal | **No** | Requires DHCR registration history (consecutive years) + lease-renewal sequence |
| **Unlawful deregulation-on-vacancy claim** — pre-HSTPA the unit allegedly hit the $2,500 deregulation threshold during a vacancy; if the deregulation was actually invalid, current rent is overcharge | **No** | Requires DHCR registration year-over-year continuity check |
| **HSTPA-era deregulation** — any deregulation post-2019-06-14 is void ab initio per `rules/__init__.py:43` | **No.** `HSTPA_LOCK` declared `detectable=False` | Requires DHCR + listing cross-join showing post-2019 dropout from registration |
| **Pied-à-terre / short-term-rental conversion** of stabilized unit | **No** | Requires Airbnb / VRBO listing data joined to BBL |
| **SCRIE / DRIE benefit fraud** — collecting senior/disability freeze credit while charging unfrozen successor tenant | **No** | Requires HPD SCRIE/DRIE roster |
| **Section 8 HAP overcharge** — collecting voucher subsidy + side cash above the contract rent | **No** | Requires HUD HAP contract data |
| **Owner-occupancy false-pretense eviction** under §26-511(c)(9)(b) | **No** | Requires eviction case docket cross-joined to occupancy proxies (USPS NCOA, voter reg) |
| **MCI (Major Capital Improvement) claim inflation** | **No** | Requires DHCR MCI orders + DOB permits |

**Verdict:** Rule 3 transfers strongly. The framework is a divergence-detector for ONE specific f (listed_rent > estimated_legal_max). It systematically misses the broader fraud population. J-51-while-deregulated, IAI inflation, and preferential-rent snap-back are each likely to be 5-figure to 6-figure tenant-harm-per-unit categories, none currently wired to compiled f.

The structural fix is to populate `rules/` with additional compiled f-rules, each pulling from the same underlying buildings + a new M-source. Most are net-new triples in `candidate_triples.md`.

---

## Rule 4 — Subagent firewall for blinded cohort scoring

**Public-co version:** when analyst has outcome knowledge for some/all cohort items, hindsight contaminates query selection and scoring; spawn isolated subagents per item.

**Rent-stab application:** marginal at present. The framework has no scored cohort — it's a gap function over individual buildings, with no published rankings against an outcome-known list of HCR enforcement actions.

**Where the rule becomes operationally relevant going forward:**
- **Citywide landlord ranking.** If a future scan ranks the top-50 NYC landlords by aggregate overcharge exposure, and the analyst is already aware that (e.g.) Pinnacle, Croman, etc. have prior enforcement history, hindsight would contaminate severity-threshold tuning. Same risk as citywide property-tax overdue ranking in lasalle_v2.
- **Single-building forensic DD.** Per Layer 3 explicit carveout, single-asset adversarial probing does NOT need this — analyst should see everything. Most current rent-stab use looks like this mode.

**Verdict:** Rule 4 transfers in principle but is not operationally relevant until the vertical produces a ranked cohort. The discipline-rule itself does not currently change conclusions because there are no conclusions yet at the cohort level.

---

## Rule 5 — Stock-for-services / vendor-payable-to-equity = generic distress fingerprint

**Public-co version:** vendor invoices settled in shares = high-signal flag.

**Rent-stab application:** N/A. There's no equivalent of equity-for-services in residential rent.

**The closest analogue,** if forced: rent concessions that don't reduce the registered legal rent ("free month," gift cards, deferred-rent agreements). Owner registers the higher legal rent, which preserves the rent ceiling for next year, while the tenant's effective rent is lower. This is structurally similar to the public-co pattern (settle the obligation in something other than cash to manage the registered number) but in the opposite direction (here the owner is *understating* effective consideration, not the vendor settling for non-cash).

This pattern is detectable via DHCR registration vs effective-rent surveys but does not look like the public-co stock-for-services flag.

**Verdict:** Rule 5 does NOT transfer. The closest analogue is too oblique and runs in the opposite direction.

---

## Rule 6 — Calibration heuristics tuned on known cohorts are contaminated

**Public-co version:** scoring rules authored after seeing cohort outcomes carry hindsight even through subagent blinding; require strict train/test split.

**Rent-stab application — what does NOT transfer cleanly:**

The current calibration parameters are author-declared rather than cohort-tuned, but they have a different problem: they are *generic* in a way that hides blind spots rather than encodes them.

- `vacancy_bonus_factor = 1.5` (`jurisdictions/nyc/config.py:13`). A single multiplier applied to every unit, every borough, every vintage. The docstring says "1.5 = 50% over pure RGB (conservative upper bound that encompasses most legitimate increases)." But there's no observed cohort behind that 1.5 — it's an authored heuristic. For a unit that has had 1 vacancy in 50 years, 1.5× is wildly generous; for a high-turnover unit with documented IAI, 1.5× under-represents the legal max and produces false positives.
- `min_rent_delta = $500` (config.py:5). Hardcoded absolute threshold. A $400 overcharge on a $600 legal max (67%) is suppressed; a $501 overcharge on a $4,500 legal max (11%) fires. This is precision-recall calibration done by absolute floor rather than ratio.
- Severity weights in `scorer.py` (lines 35-65). 40 points for confirmed J-51, +10 for entity owner, +30 for >100% gap, etc. No documented derivation.

The honest framing in `gap.py:14-18` ("The estimate is conservative to minimise false positives. Signals here are leads for DHCR inquiry, not definitive legal findings") is **honest about the output tier** but does not address the underlying calibration question: is "conservative" the right setting for the actual goal? If the vertical is a lead-generator for tenant attorneys and DHCR investigators, false positives are fine and the threshold should be loose. If it's an underwriting tool for buyer-side DD on multifamily portfolios, false positives are expensive and the threshold should be tight. The single-multiplier doctrine prevents the framework from serving either user well, and the "conservative" framing hides that.

**What rent-stab has that property tax doesn't (per Rule 6 adjustments):**
- **Exemption universe is well-defined but legally complex.** RSL has co-op/condo conversion exemptions, owner-occupancy carveouts, hotel-class statuses, transient-occupancy reclassifications. The framework currently has a flat `"exempt"` status but no exemption taxonomy.
- **Penalty for the underlying violation is large** (treble damages + 6-year lookback under §26-516, per `rules/rsl_overcharge.py:43-45`) — much larger per-case stakes than property tax's $200 L-4260 fine. False-positive cost is high (litigation exposure for the named landlord); precision matters more than in property-tax screening.
- **Population is hundreds of thousands of small actors** — owners, not just buildings. False-positive cost per case scales to legal defense fees, not just a corrected tax bill. Calibration tradeoff is more sensitive than property tax.

**Verdict:** Rule 6 strongly applies. The current `vacancy_bonus_factor`, `min_rent_delta`, and `scorer.py` weights are generic heuristics, not held-out-validated. The "conservative to minimise false positives" framing is honest about the *tier* but obscures that the calibration itself is uncalibrated. A held-out cohort of buildings with known DHCR orders or settled overcharge claims would let the framework calibrate `vacancy_bonus_factor` per-vintage, per-borough, per-unit-size rather than as a single global multiplier.

---

## Summary table — rule transfer to rent stabilization

| Rule | Transfers? | Most important consequence |
|---|---|---|
| 1. Read the notes | **Yes** | DHCR Annual Apartment Registration is the unread "notes" — converts heuristic to measurement |
| 2. Coverage before absence | **Yes** | Four silent-`None` paths in `gap.py` conflate "no coverage" with "no overcharge" |
| 3. Divergence ≠ solvency / scope | **Yes (strongly)** | One f wired (RSL overcharge); 8+ sibling fraud categories unwired. J-51 and HSTPA SignalRules are declared but uncompiled |
| 4. Subagent firewall | **Marginal** | No scored cohort exists; becomes relevant if landlord-portfolio rankings are produced |
| 5. Stock-for-services | **No** | No analogue in residential rent |
| 6. Hindsight calibration | **Yes (strongly)** | `vacancy_bonus_factor = 1.5` and `min_rent_delta = $500` are generic, not cohort-tuned. "Conservative" framing hides this. |

**Net change to a typical building finding:** unchanged on direction (an over-asking-rent listing on a likely-stabilized building remains a real lead). Reduced confidence in any "no signal" output for buildings that fall outside PLUTO coverage thresholds. Significantly expanded scope per Rule 3 — the right question for citywide work is not "how many listings exceed the borough-baseline RGB-implied legal max?" but "how many forms of RSL non-compliance can the framework reach with currently-public M-sources?" J-51 enforcement and IAI / preferential-rent fraud are net-new high-ROI extensions.
