# Federal-Registry Operational Test — Probe across 21 names

_Probe run 2026-05-18. EPA Envirofacts (FRS + TRI + GHGRP) with thorough
subsidiary-name variants + skepticism-step location audit for 0-hit
targets._

## What was tested

Thesis: a small-cap that claims US industrial operations at scale but
has materially fewer EPA-permitted facilities than industrial controls
at comparable revenue is a tradable short signal — because the
operational claim doesn't match the federal-registry reality.

For each target, probe FRS / TRI / GHGRP across **multiple subsidiary-
name variants** (parent + common suffixes + known subsidiary names),
plus a location-audit step for any target showing zero hits.

## Raw results

| TK    | industry          | rev      | FRS  | TRI | GHG | rev/FRS  | notes |
|-------|-------------------|---------:|-----:|----:|----:|---------:|-------|
| LIN   | control gas       | $33.0B   | 1814 | 153 |  29 | $18.2M   | Linde — but FRS heavily noise-padded by "Linder" matches |
| APD   | control gas       | $12.0B   |  472 |  71 |  33 | $25.4M   | Air Products — real |
| ALB   | control lithium   |  $9.6B   |  195 |  11 |   6 | $49.2M   | Albemarle — real |
| HDSN  | control refrig    | $290M    |   19 |   9 |   2 | $15.3M   | Hudson Tech — real |
| **PLUG** | hydrogen       | $891M    |   16 |   0 |   0 | **$55.7M** | **2× sparser than worst control** |
| BE    | hydrogen          | $1.4B    |   38 |   1 |   0 | $36.8M   | Bloom — within control band |
| BLDP  | hydrogen          | $102M    |    3 |   1 |   0 | $34.0M   | Ballard — within control band (after subsidiary discovery!) |
| FCEL  | hydrogen          | $123M    |   50 |   2 |   0 | $2.5M    | dense — well-permitted |
| HYZN  | hydrogen          | $0.3M    |    1 |   0 |   0 | n/a      | pre-revenue |
| MVST  | battery           | $306M    |    2 |   0 |   0 | $153M    | sparse — but real plants in Tennessee/Colorado |
| ENVX  | battery           | $7M      |    3 |   0 |   0 | $2.3M    | pre-revenue scale |
| SLDP  | battery           | $17M     |    4 |   0 |   0 | $4.2M    | pre-revenue (but **3 of 4 hits are "Solid Power Corp" in NY — different company**) |
| QS    | battery           | $0       |    5 |   1 |   0 | n/a      | 4/5 are "FAA QSV..." — substring noise |
| SES   | battery           | $3M      |    4 |   0 |   0 | $0.8M    | found via "Solidenergy Systems" subsidiary — Woburn MA |
| LAC   | lithium           | $0       |    3 |   0 |   0 | n/a      | found via "Thacker Pass" variant — Orovada NV |
| AIRO  | defense           | $84M     |  385 |   7 |   2 | $0.2M    | **385 is ~100% substring noise (AIRO Graphics, etc.); real ≈ 0** |
| WKHS  | EV                | $13M     |   13 |   3 |   0 | $1.0M    | Workhorse Custom Chassis Union City IN — real |
| BLNK  | EV                | $140M    |    0 |   0 |   0 | n/a      | **NO_FOOTPRINT (loc-audit confirms 0)** |
| QBTS  | quantum           | $9M      |    0 |   0 |   0 | n/a      | NO_FOOTPRINT (Burnaby BC mfg — outside US) |
| IONQ  | quantum           | $41M     |    7 |   0 |   0 | $5.9M    | 5/7 are "VisionQuest" substring noise; real ≈ 2 |
| RGTI  | quantum           | $11M     |    4 |   0 |   0 | $2.8M    | 2 real (Berkeley, Fremont CA), 1 surname noise |

## What I expected vs. what I found

I expected: lots of NO_EPA_FOOTPRINT signals on small-caps claiming
industrial scale → tradable short signals.

I found: mostly confirmation that the small-caps DO have US footprint
when you probe subsidiary names thoroughly. The 0-hit cases (BLNK, QBTS)
are mostly explained by either non-chemistry operations (EV charging
doesn't require EPA permits) or non-US manufacturing (QBTS in Canada).

This is a sobering empirical result.

## The genuine findings

### 1. PLUG is unusually sparse relative to controls

PLUG at $55.7M revenue/FRS facility is **2× sparser than the worst
control** (HDSN at $15.3M; ALB at $49.2M). All other industrial-claim
names are inside the control band.

But caveats:
- PLUG's electrolytic hydrogen genuinely doesn't trigger TRI / GHGRP
  thresholds (electrolysis of water doesn't generate TRI chemicals or
  direct GHGRP-scale emissions). So a thin TRI/GHGRP footprint is
  *expected*; only FRS is a fair comparison.
- Sample of 1 controls-comparable industrial claim. n=1 isn't evidence.
- The 16 FRS facilities for PLUG include several offices / warehouses,
  not all production plants.

### 2. AIRO's "Phoenix AZ industrial facility" claim is hollow

Despite 385 FRS hits under loose substring matching, **virtually none
are AIRO Group Holdings facilities** — they're "AIRO Graphics" sign
shops, "Cairo Cooperative" agriculture, "Sinclair Operating" oil & gas,
etc. After word-boundary strict filtering, AIRO's real EPA-registered
count is approximately **zero**.

This matches the framework's existing AIRO-8 RED_FLAG_NEGATIVE
(stock-for-services + ICFR weakness disclosure pattern). The federal-
registry test corroborates the disclosure-quality signal: AIRO claims
a Phoenix AZ industrial drone-manufacturing facility, but EPA doesn't
recognize any such operation. Tier-2 evidence for the existing short
thesis.

### 3. BLNK and QBTS have zero footprint but the signal isn't diagnostic

BLNK (Blink Charging, $140M rev): 0 FRS hits anywhere, location audit
on Bowie MD + LA also turns up nothing. **But EV charging
infrastructure typically doesn't require federal EPA permits** — it's
installation + utility-grade electrical, not chemistry. Absence here
is the expected baseline, not a divergence.

QBTS (D-Wave, $9M rev): 0 FRS hits at Palo Alto (2,777 unrelated
facilities at that location). **But D-Wave's actual manufacturing is
in Burnaby, BC, Canada** — outside EPA jurisdiction. Absence is the
expected baseline.

## Why this didn't generate basket-level alpha

Three structural reasons the federal-registry test doesn't scale into
a tradable signal across this universe:

1. **Subsidiary-name asymmetry is the dominant failure mode.** Without
   thorough variant probing, you'd miss BALLARD FUEL CELL SYSTEMS
   (Bend OR), SOLIDENERGY SYSTEMS (Woburn MA — that's SES), THACKER
   PASS (Orovada NV — that's LAC), WORKHORSE CUSTOM CHASSIS (Union
   City IN — that's WKHS). All four would naively show "0 footprint"
   under a parent-name-only probe. The signal isn't "0 = short", it's
   "0 after thorough subsidiary probe = short" — and that requires
   per-name research that doesn't fit a screen.

2. **Chemistry bias.** The small-cap universe is heavily weighted
   toward chemistry-light operations: EV charging (BLNK), quantum
   computing (QBTS / IONQ / RGTI), software-heavy mfg (BBAI, KSCP).
   These genuinely don't require EPA permits at material scale. EPA
   absence isn't diagnostic for them.

3. **Substring noise is severe.** The naive variant-probe yields 385
   hits for AIRO (real ≈ 0), 7 hits for IONQ (real ≈ 2), 5 hits for
   QS (real ≈ 1), 4 hits for SLDP (3 are an unrelated NY company
   named "Solid Power Corp"). A non-skeptical probe would inflate
   facility counts dramatically.

## Where this signal might actually work

The federal-registry test plausibly produces real alpha on a tighter
sub-universe:

- **Chemistry-intensive small-cap claimants**: battery cathode
  manufacturers (specialty chem precursors), hydrogen reforming
  plants (uses methane → triggers GHGRP), specialty pharma APIs
  (TRI chemicals required), industrial coatings, mining processors.
  These industries should have EPA permits at material revenue scale.
- **Names with specific named plant addresses in 10-K**: when a
  company says "our 250,000 sq ft Penang facility" or "our 577,000 sq
  ft Clarksville plant", the address claim is testable. The diagnostic
  is whether *anyone* permitted by EPA is at that exact address, and
  whether the permit-holder is the focal company or a tenant /
  predecessor.
- **Larger-cap fakes**: a $500M-$2B mcap industrial claimant with
  sparse footprint is a stronger signal than a $50M-$100M one,
  because institutional shorts CAN actually trade it.

This isn't a screen-able universe-wide signal. It's a per-name
verification tool that complements disclosure-quality signals
(AIRO-8 style RED_FLAG_NEGATIVE patterns).

## Net read on the alpha question

**The federal-registry test is real research value, not basket alpha.**
It catches AIRO-style hollow operational claims when applied carefully,
but it doesn't generate enough cleanly-positive signals across a small-
cap industrial universe to anchor a strategy. The cases where it
appeared to fire (BLNK, QBTS, naively AIRO) either reflect known
non-EPA-relevant chemistries or were substring artifacts.

What this teaches the Signal OS framework:
- **Use this as a per-claim verification step, not a screen.** When
  the planner emits a `physical_facility` claim with a named US
  address, the EPA v2 connector should test it. When the planner
  emits any other category of claim, EPA isn't diagnostic.
- **Subsidiary discovery is the bottleneck.** A v3 connector needs
  a `name_patterns: list[str]` parameter and ideally an auto-pull
  from 10-K Exhibit 21 (List of Subsidiaries).
- **Substring noise needs explicit filtering.** Word-boundary regex,
  not naive `CONTAINING` substring.
