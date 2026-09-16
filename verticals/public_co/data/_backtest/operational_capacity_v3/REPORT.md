# v3 Narrow-Screen Operational-Capacity Probe

_Probe run 2026-05-18. Universe: 14 chemistry-intensive mid-caps,
$390M-$2.57B mcap, where EPA permits SHOULD exist at material revenue
scale._

## What was tested

Hypothesis: the v2 probe didn't find alpha because its universe was
mostly chemistry-light micro-caps. A tighter universe of (a) chemistry-
intensive industries, (b) $500M-$2B mcap (institutionally-shortable),
(c) US manufacturing claims → would have higher base-rate EPA expectation
and produce cleaner divergence signals.

## Universe

| Category | Names | Why included |
|----------|-------|-------|
| Battery / lithium TARGETS | AMPX, EOSE, SLI | claim US chemistry-mfg ops |
| Specialty chem CONTROLS | SCL, IOSP, KOP, OEC, NGVT | established operators, confirm baseline |
| Industrial chem TARGETS | LXU, ASIX, TROX, AMSC | claim US chemistry plants |
| Non-chem CONTROLS | FOR (real estate), MTW (cranes) | expected low/zero EPA |

## Headline result

| TK    | industry                     | mcap   | rev    |  FRS | rev/FRS  | finding |
|-------|------------------------------|-------:|-------:|-----:|---------:|---------|
| SLI   | lithium (pre-production)     | $0.88B | $0.00B |   0  |    n/a   | **0 EPA — but tenant at Lanxess El Dorado** |
| FOR   | real estate (non-chem ctl)   | $1.30B | $1.71B |   0  |    n/a   | 0 EPA — expected baseline for real estate |
| ASIX  | caprolactam chemistry        | $0.58B | $1.55B |   8  | $193.8M  | within control band |
| OEC   | carbon black (control)       | $0.39B | $1.79B |  11  | $162.7M  | control |
| IOSP  | specialty chem (control)     | $1.95B | $1.79B |  16  | $111.9M  | control |
| NGVT  | activated carbon (control)   | $2.35B | $1.18B |  18  | $65.6M   | control |
| TROX  | titanium dioxide chemistry   | $1.26B | $2.92B |  50  | $58.4M   | within control band |
| EOSE  | battery zinc-bromide         | $2.57B | $0.16B |   3  | $53.3M   | **plants found at claimed Edison NJ + East Pittsburgh PA** |
| SCL   | surfactants (control)        | $1.13B | $2.34B |  45  | $52.0M   | control |
| AMSC  | superconductor wire          | $2.37B | $0.28B |   9  | $31.1M   | **plants found at claimed Ayer MA + Devens MA** |
| MTW   | industrial cranes (non-chem) | $0.43B | $2.26B |  81  | $27.9M   | many real Manitowoc Cranes sites |
| LXU   | nitrogen chemistry           | $1.01B | $0.64B |  26  | $24.6M   | found via "El Dorado Chemical" subsidiary |
| AMPX  | battery silicon anodes       | $2.21B | $0.09B |   4  | $22.5M   | **plants found at claimed Fremont CA** |
| KOP   | treated wood (control)       | $0.79B | $1.88B | 180  | $10.4M   | control |

## What I expected vs. what I found

**I expected:** at least 2-3 names in the target group showing materially
lighter footprint than controls, where the EPA absence couldn't be
explained by chemistry-bias or non-US operations.

**I found:** zero clean divergences. Every name that initially looked
divergent resolved to a benign explanation when probed properly.

### The closest thing to a finding — SLI — turns out to be a tenant case

Standard Lithium (SLI) returned 0 FRS / TRI / GHGRP hits under variants
"Standard Lithium", "Smackover Lithium", "TETRA Smackover". Location
audit at El Dorado AR (their stated project site): 1,015 total facilities
at that location, ZERO matched to Standard Lithium.

But: probing "Lanxess" in Arkansas returns **LANXESS CORP - CENTRAL PLANT
(El Dorado AR) + LANXESS CORPORATION BROMINE FACILITY (Emerson AR)**.
Standard Lithium operates as a **tenant at the Lanxess bromine plant** —
their entire Arkansas brine extraction is hosted on Lanxess's permitted
facility. Lanxess holds the EPA permit; SLI is the lithium-extraction
co-tenant.

This is the same "co-located tenant" pattern we identified earlier for
PLUG at Wacker Polysilicon (Charleston TN). The EPA permit holder is the
host; the partner with the operational claim doesn't appear in EPA
records but is still operating at the address. **Location audits return
"0 affiliated" without distinguishing tenant from genuine absence.**

### Two findings the probe correctly confirmed

- **EOSE plants found at claimed Edison NJ + East Pittsburgh PA**
  (matches Turtle Creek PA claim — Turtle Creek is a borough of greater
  East Pittsburgh)
- **AMSC plants found at claimed Ayer MA + Devens MA + Westborough MA**
  (corroborates their superconducting-wire manufacturing claims)
- **AMPX plants found at claimed Fremont CA + Menlo Park CA + Sunnyvale
  CA** (corroborates silicon anode chemistry mfg)

These are the most relevant cases: small-cap battery/specialty
chemistry claimants whose operational claims COULD have been hollow.
They're not. The plants exist where they say they do, in EPA registry.

### The control range is too wide to use as a screen

Established chemistry mid-caps span **$10.4M (KOP) to $193.8M (ASIX)
rev/FRS-facility** — a 19× spread driven by operational structure
(KOP has 180 distribution yards for treated wood; ASIX has 8 large
chemistry plants). This range is wider than the divergence we'd hope
to detect. A "high rev/FRS = sparse footprint" screen would flag ASIX
and OEC as suspicious, when both are established operators with real
permitted plants.

## Quantitative divergence scores vs chemistry controls

Z-scored against the 5-name chemistry-control distribution
(SCL, IOSP, KOP, OEC, NGVT):

- Control `log10(rev/FRS)`: μ=7.762, σ=0.459 → **~$57.9M revenue per FRS-permitted facility, ±0.46 dex**
- Control `log10(n_FRS)`: μ=1.482, σ=0.487 → **~30 facilities per name, ±0.49 dex**

```
TK    bkt   mcap   rev   n_FRS  rev/FRS  z_rpf  z_nf  exp_n  act/exp  flag
KOP   CTRL  0.79B  1.88B  180   10.4M    -1.62  +1.59  32.5   5.54    DIVERGE  ← control artifact
SCL   CTRL  1.13B  2.34B   45   52.0M    -0.10  +0.35  40.4   1.11
IOSP  CTRL  1.95B  1.79B   16  111.9M    +0.62  -0.57  30.9   0.52
OEC   CTRL  0.39B  1.79B   11  162.7M    +0.98  -0.90  30.9   0.36
NGVT  CTRL  2.35B  1.18B   18   65.6M    +0.12  -0.46  20.4   0.88
---
ASIX  TGT   0.58B  1.55B    8  193.8M    +1.14  -1.19  26.8   0.30
TROX  TGT   1.26B  2.92B   50   58.4M    +0.01  +0.45  50.5   0.99
LXU   TGT   1.01B  0.64B   26   24.6M    -0.81  -0.14  11.1   2.35
EOSE  TGT   2.57B  0.16B    3   53.3M    -0.08  -2.06   2.8   1.08   DIVERGE_n (low-rev)
AMSC  TGT   2.37B  0.28B    9   31.1M    -0.59  -1.08   4.8   1.86
AMPX  TGT   2.21B  0.09B    4   22.5M    -0.89  -1.81   1.6   2.57   DIVERGE_n (low-rev)
SLI   TGT   0.88B  0.00B    0     --      n/a    n/a    --     --    ZERO_FRS (tenant case)
---
MTW   NCHEM 0.43B  2.26B   81   27.9M    -0.69  +0.88  39.1   2.07
FOR   NCHEM 1.30B  1.71B    0     --      n/a    n/a   29.6   0.00
```

What the divergence scores tell us:

1. **The control band itself isn't tight.** KOP is z=-1.62 on rev/FRS
   *as a control* because its 180 distribution yards swamp the
   chemistry-mfg signal. The screen would flag a real chemistry operator
   as "suspiciously sparse-revenue-per-facility" — that's a false-
   positive direction we don't want.

2. **No target diverges on `z_rpf` at |z|≥1.5.** The most extreme is
   ASIX at +1.14 (high concentration, 8 plants supporting $1.55B rev) —
   the opposite direction from "hollow." LXU at -0.81 is the only
   target on the "sparse" side, and the 26 FRS hits there are real
   (via "El Dorado Chemical" subsidiary).

3. **AMPX and EOSE diverge on `z_nf` (low total count)** but the
   `act/exp` ratio is ABOVE 1 for both — at their actual revenue, the
   control rev/FRS rate would predict ~1.6 and ~2.8 facilities
   respectively. They have 4 and 3. So they have *more* facilities
   per revenue than controls, not fewer. The low-`z_nf` is a small-
   revenue artifact, not evidence of hollowness.

4. **SLI is the only target with `n_FRS = 0`** — the tenant-case
   already documented above.

5. **MTW (non-chem control) hits 81 FRS** with z_nf=+0.88 — i.e., the
   screen would also fire on non-chemistry industrials, so even the
   "high-permit-count" direction isn't chemistry-specific.

The divergence numbers say the same thing the qualitative review said,
with cleaner failure modes labeled: **the screen has neither
discriminating power on the `rev/FRS` axis (controls too noisy due to
operational structure), nor on the absolute-count axis (low-rev targets
artifactually flag, real chemistry operators don't).**

## Verdict on the federal-registry alpha thesis (combined v2 + v3)

Across **35 names** probed thoroughly (21 in v2, 14 in v3), the
federal-registry operational test produces:

1. **Zero clean alpha-generating divergences** when accounting for:
   - Subsidiary-name asymmetry (BLDP, SES, LAC, WKHS all found under
     subsidiary names)
   - Tenant / co-location relationships (PLUG@Wacker, SLI@Lanxess)
   - Chemistry that doesn't trigger EPA permits (BLNK EV charging,
     QBTS quantum)
   - Non-US operations (BLDP Canada, QBTS Canada)
2. **One useful per-name verification result**: AIRO's 385 raw hits
   collapse to ~0 real after word-boundary filtering. Their claimed
   "Phoenix AZ industrial drone facility" doesn't appear in EPA
   registry under any name. This corroborates the framework's existing
   AIRO-8 RED_FLAG_NEGATIVE (stock-for-services + ICFR weakness) —
   adds Tier-2 evidence to an already-emit ed short, but doesn't
   independently generate new shorts.

The signal is real *as research methodology* — it catches AIRO-style
hollow claims when applied carefully — but it doesn't generalize into
a tradable factor. The fundamental problem is that the small-cap
industrial-claimant universe is dominated by:
- Pre-production stages (where 0 EPA is expected baseline)
- Tenant relationships (where the host holds the permit)
- Chemistry-light operations (where EPA absence proves nothing)

A universe where the test would actually fire usefully would need to
be: chemistry-intensive + post-production + sole-tenant + small-enough-
to-short. That intersection is essentially empty in the public-market
universe — by the time a company hits all those criteria, it's either
big enough to be on factor models (>$3B) or it's been delisted.

## What this means for Signal OS

The federal-registry probe should stay in the framework's toolkit but
be repositioned:

- **Not a screen / factor**: don't expect basket-level alpha.
- **A per-claim verification step**: when the planner extracts a
  `physical_facility` claim with a named US address, the v3 EPA
  connector should probe (a) all subsidiary name variants from 10-K
  Exhibit 21, (b) the named address, (c) cross-reference for tenant
  relationships ("does another EPA-permitted entity at this address
  appear in the focal company's filings as host?"). The result is one
  M-source contribution to the larger multi-source claim adjudication
  — not an independent signal.
- **Strongest use case**: corroborating an already-emitting short
  (like AIRO) where the disclosure-quality signature is the primary
  thesis and the operational-claim absence is the supporting evidence.

The honest read: the framework's real value is NOT in this connector
alone but in the aggregation across many connectors. Whether that
aggregation produces alpha is the question that hasn't been tested
yet — and would require a multi-year forward test of the *full
framework's* emitted bets, not single-signal screens.
