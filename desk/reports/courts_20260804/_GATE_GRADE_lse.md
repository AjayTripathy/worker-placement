# GATE GRADE — LSE shelf, flagged tier (WYN / SPR / CLBS / TFW)

**Court date** 2026-08-04 · **Cohort** the four names the LSE-shelf build lane marked with trap
flags in `desk/data/LSE_INTAKE_20260804.md` §2 rows 12–15 · **Shelf**
`verticals/generators/data/LSE_SHELF.json` (249 rows, generated 2026-08-04T17:27:45Z) ·
**Module** `verticals/generators/lse_shelf.py`

Two jobs: (a) a quick verdict per name, (b) grade the guard that flagged it. The BRZE lesson says
one costly-wrong per cohort is the norm. **There is one here, and it is CLBS, not TFW** — though
TFW is the cleaner *specimen* of a defective diagnostic.

---

## 0. THE FIRST FINDING: NOTHING IN THIS COHORT WAS ACTUALLY DEMOTED BY A GUARD

The brief describes these four as "the names the build lane's guards demoted." They were not.

| claim | how checked | authority | finding |
|---|---|---|---|
| WYN/SPR/CLBS/TFW were demoted from the printable shelf | re-ran the module's own demotion filter over the shelf JSON | `lse_shelf.py:1528-1529` — `printable = [r for r in shelf if not r["durability_suspect"] and not r["in_offer_period"]]` | **REFUTED.** All four have `durability_suspect=False` and `in_offer_period=False`. All four are **PRINTABLE**, ranked 12, 13, 14, 15 of 249 |

The only two fields that demote are `durability_suspect` and `in_offer_period`. `melting`,
`trough_anchored`, `trend_flattered`, net-debt ratio and EBIT sign **demote nothing** — and the
module says so explicitly at `lse_shelf.py:143-145`:

> "Informational, never a demotion: a trough multiple on a cyclical is the buy and on a structural
> decliner is the trap, and only a human reading the business can tell which."

**So the demotion happened in the intake prose, not in the code.** `LSE_INTAKE_20260804.md` §6
routes WYN to "Skip on execution alone regardless of multiple", CLBS to "Cash-shell lane, not the
value lane", and prints a per-name "Trap flags" column that is hand-composed on top of the module
fields. That column is the de-facto gate, it is unversioned, untested, and — as §1 shows — it
prints at least one flag the module did not fire.

**Grade: the guard layer is better than the report layer that consumes it.** The defect to fix is
that a hand-written routing paragraph is doing work the module deliberately refused to do.

---

## 1. TFW — THE GATE-DEFECT SPECIMEN: A FLAG THAT FIRES ON EVERY COMPOUNDER BY CONSTRUCTION

The brief's hypothesis was that the trough-anchor flag demoted a quality name for having had a
great 2021. The mechanism is different and worse.

`lse_shelf.py:1301`:

```python
m["trough_anchored"] = bool(len(eh_v) >= 3 and eh_v[-1] == min(eh_v))
```

`eh_v` is EBIT history newest-first, so `eh_v[-1]` is the oldest year. The test is *"is the oldest
year the smallest?"* — **which is true of every monotonically rising earnings series in
existence.** A company that grows EBIT every year for three years is tagged `trough_anchored` with
probability 1.

Measured on this shelf:

| test | result |
|---|---|
| rows with ≥3 years of EBIT history | 248 |
| rows whose EBIT rose in every year (the compounder shape) | 59 |
| of those, tagged `trough_anchored` | **59 — 100%** |
| rows tagged `trough_anchored` that are at or ABOVE their own EBIT peak | **69 of 111 (62%)** |

The flag has **zero discriminating power** against the shape it is most likely to be read as
condemning. TFW (`ebit_vs_peak` 1.05, `ebit_trend` 1.30, EBIT history 24.7 → 27.8 → 30.6 → ~32.1)
is tagged for the sole reason that its worst year of the last four was four years ago.

**The module got this right and the report got it wrong.** The composed flag `trend_flattered`
(line 1305) correctly requires `trough_anchored AND ebit_trend > 1.2 AND ebit_vs_peak < 0.8`, and
it is **False on TFW** — as it is on 57 of the 59 compounders. The module's own flag renderer
(line 1637) prints the label `"trough-anchor"` **off `trend_flattered`, not off `trough_anchored`**:

```python
("trough-anchor", r.get("trend_flattered")),
```

So the module would never have printed "trough-anchor" against TFW. The intake table did anyway.

**GRADE — trough-anchor: the composed guard `trend_flattered` is CORRECT and well-built (2 fires
across 59 compounders, both legitimately below 0.8× peak: MSI 0.79, ENOG 0.70). The raw
intermediate `trough_anchored` is a diagnostic, not a verdict, and surfacing it as a trap flag is
a report-layer defect.** Fix: mark `trough_anchored` internal-only, or rename it
`oldest_year_is_min` so it cannot be misread.

---

## 2. THE MELTING GUARD: DIRECTIONALLY RIGHT ON WYN, BUT HALF ITS FIRES EXPIRE ON THE CALENDAR

`melting = ebit_vs_peak < 0.5`, with the peak taken over a 3–4 year window.

The failure mode: when the peak is the **oldest** observation, the anchor sits at the edge of the
window and rolls out of it at the next annual report — so the flag switches off with no change in
the business.

| test | result |
|---|---|
| `melting=True` on the shelf | 54 |
| of those, peak == oldest observation (anchor at the window edge) | **27 (50%)** |

The 27 are dominated by oil & gas and commodity-exposed industrials whose peak is the 2022 energy
/ input-cost spike (GENL, KIST, SQZ, DEC, TLW, PHAR, PTAL, GKP, IBST, ECOR, PAGE, HAS…).

**WYN is exactly this shape and is fully worked below.** Its window is FY25 £8.69m / FY24 £7.18m /
FY23 £9.32m / **FY22 £21.70m** — and FY22 (year to Oct-2022) is the fertiliser-and-grain inflation
spike. When Wynnstay reports FY26 (Oct-2026, roughly three months from now) FY22 leaves the
window, the peak becomes ~£9.3m, and `ebit_vs_peak` jumps **0.42 → ~0.98 with zero change in the
business.** A guard whose verdict flips on the calendar is not measuring the business.

**GRADE — melting: CORRECT VERDICT ON WYN, FRAGILE MECHANISM.** It is right that Wynnstay's
earnings power has reset, but it is right for the wrong reason: the evidence is not the distance
from FY22, it is that FY23/24/25 are *flat at £7–9m with no recovery*. Fix: carry
`peak_is_window_edge` beside `melting`, and prefer a "no recovery in N years" test to a
distance-from-peak test on anything commodity-exposed.

---

## 3. TWO GUARDS THAT FAILED IN THE FLATTERING DIRECTION (worse than a false demotion)

### 3a. `wc_fcf` is conditioned on EBIT<0, so it cannot police a profitable inventory unwind

`verticals/deep_value/score.py:70`:

```python
r["wc_fcf"] = (fcf is not None and fcf > 0) and (ebit is not None and ebit < 0)
```

It fires only when free cash flow is positive **while EBIT is negative** — the DCGO
loss-making-receivable-liquidation mirage. It is structurally incapable of firing on the far more
common shape: a **profitable** business whose FCF is a one-time working-capital release.

| test | result |
|---|---|
| `wc_fcf` fired | 14 of 249 |
| profitable names with FCF > 1.2× EBIT — the guard cannot fire on any of them | **63 of 249 (25%)** |

**SPR is in that 63** (FCF 1.29× EBIT). Springfield's £31.6m of TTM FCF sits against an inventory
draw of **£20.4m** (£244.3m → £223.9m over FY25) — i.e. roughly two thirds of the 27% FCF yield
that put it on the shelf is land and WIP liquidation, not earnings. FCF yield is a scored
component of the composite, so on a quarter of the shelf that component is unaudited.

**GRADE — wc_fcf: UNDER-FIRES BY DESIGN. A real defect, and it flatters.** Fix: add a second arm —
FCF > EBIT while inventory or receivables fell materially — which fires regardless of EBIT sign.

### 3b. The shelf does not record whether a balance sheet is audited-annual or interim

Every balance-sheet metric — `ncash_r`, `pb`, `ev`, `ev/ebit`, `ncav_r` — is struck on `bs_date`,
whatever the vendor last filed. The schema carries **no fiscal-year-end field and no
annual-vs-interim flag** (checked: the only period-ish fields on the row are `fcfy`, `fy_stale`,
`in_offer_period`).

Measured directly, by comparing each row's `bs_date` against the set of annual balance-sheet dates
for the same ticker (random sample of 45, seed 7, all 45 resolved):

| | n | share |
|---|---|---|
| `bs_date` **is** an audited annual date | 27 | 60% |
| `bs_date` is an **unaudited interim** | **18** | **40%** |

**Three of this cohort's four names are in the 40%: SPR (2025-11-30 interim vs 2025-05-31 year
end), TFW (2025-12-31 interim vs 2024-06-30 latest annual on file), WYN (2026-04-30 interim vs
2025-10-31 year end).**

For a working-capital-cyclical business this is a systematic, sign-consistent distortion, and SPR
is the specimen — worked in §4.

**GRADE — a schema gap, not a guard failure, but it is the one with the widest blast radius.**
Fix: carry `fiscal_year_end` and `bs_is_interim`, and either annualise or footnote leverage struck
on an interim.

---

## 4. PER-NAME VERDICTS AND GUARD GRADES

Full workings in `WYN.md`, `SPR.md`, `CLBS.md`, `TFW.md` and the four
`desk/data/edge_classifications/*.json`.

| | verdict | E[FV] vs spot | the flag | **guard grade** |
|---|---|---|---|---|
| **SPR** Springfield Properties | **WATCH 5/10** | 113.5p vs 99.5p, **+14.1%** | "net debt 40% of cap" | **WRONG — the costly-wrong** |
| **TFW** F.W. Thorpe | **WATCH 5/10** | 281p vs 254p, **+10.6%** | "trough-anchored" | **guard CORRECT, report defective** |
| **WYN** Wynnstay Group | **REJECT 3/10** | 385p vs 367.5p, +4.8% (killed by a 408bp touch) | "melting 0.42x" | **right verdict, fragile mechanism** |
| **CLBS** Celebrus Technologies | **REJECT 2/10** + honesty **ELEVATE** | 110p vs 109p, +1.0% | "EBIT negative" | **CORRECT — and it survived an attempt to overturn it** |

### SPR — the costly-wrong, and it was knowable

The shelf struck "net debt 40% of cap" (£47.2m) on the **30-Nov-2025 unaudited interim** — the
seasonal peak of a May-year-end housebuilder's working-capital build. **Springfield announced on 4
June 2026 — two months before the shelf ran on 2026-08-04 — that it had eliminated its bank debt
and held ~£1m of net bank cash**, "significantly ahead of market expectations of year-end net bank
debt of £10m", down from a £93.4m peak in November 2023. Management confirms the seasonality
explicitly: *"the increase over the six-month period reflects the normal seasonality of the working
capital cycle."*

But the *company's* headline understates as badly as the screen overstates. Note 31 adds leases
(£5.5m) and Mactaggart & Mickel deferred consideration (£22.0m at May-2025, minimum £7.7m a year):

| basis | net obligations | % of cap |
|---|---|---|
| Shelf (Nov-2025 interim) | £47.2m | 40% |
| Company headline (May-2026, bank only) | −£1m | −1% |
| **Honest (May-2026, all claims)** | **~£19m** | **~16%** |

And the compensating error runs the other way: the **26.7% FCF yield is the 17-Feb-2025 sale of
2,500 plots to Barratt Redrow for £64m**. That single transaction produced the £20.4m inventory
draw, the FY25 gross-margin uplift *and* the cash that repaid the debt — counted three times, paid
for by shrinking the land bank. FY26 revenue is guided to ~£245m, down 12.7%.

**Two errors in opposite directions that roughly cancel is not "the screen was roughly right." It
means neither input was trustworthy and the net was luck.**

Also refuted: `provision_kind_hint` asserts Building Safety Act cladding remediation as the expected
content for a UK housebuilder. Springfield is **Scottish and has none** — zero full-text hits for
"building safety", "cladding", "fire safety" or "remediat" across the 7,699-line annual report. The
hint is England-specific and mislabels every Scottish issuer.

### CLBS — the one I tried hardest to overturn, and could not

Secondary reporting framed FY26 as an accounting artefact ("Revenue Decline Masks ARR Growth as
Accounting Change Hits FY26 Figures"), which would have made the EBIT-negative flag the cohort's
costly-wrong. **The decisive test settles it against that reading: contract liabilities rose only
$1,708k while revenue fell $15,084k — the recognition change explains at most ~11%.**

85% of the fall is Third Party Products ($16,101k → $3,335k), and note 5 shows **Customer 1 — 59.3%
of FY25 revenue — fell $15,340k, more than the entire group decline, with its Celebrus Software line
going to exactly zero.** Adjusted PBT fell from $8.7m to $0.2m; NRR went to 96.7% from 104.1%.

**The honesty finding is the product here.** Every datum above is disclosed in note 5 — so this is
not re-detecting disclosed bad news. What diverges is the *takeaway*: management cites "increased
deferred revenue" as evidence of quality, asserts **"there was no loss of customers during the
year"** without ever reconciling it to the Customer-1 table, and **declines to publish a
like-for-like revenue bridge in the one year framed entirely around an accounting change it chose
to make.** The withheld bridge is the masking channel; the signal channel is note 5; the
signal-to-price latency is that the market re-rated **+44% off the low** on the headline before the
note was digested.

*A guard that survives a deliberate attempt to overturn it is worth more than one never tested.*

---

## 5. WHAT TO CHANGE, RANKED BY BLAST RADIUS

| # | fix | affects | severity |
|---|---|---|---|
| 1 | Carry `fiscal_year_end` and `bs_is_interim`; footnote or annualise leverage struck on an interim | **40% of the shelf** (18/45 sampled), incl. 3 of these 4 names | **HIGH — produced the costly-wrong** |
| 2 | Refresh against RNS published *after* the vendor balance-sheet date before printing a leverage flag | any name with a post-interim trading update | **HIGH — SPR's refutation was public 2 months early** |
| 3 | Add a second arm to `wc_fcf`: FCF > EBIT while inventory or receivables fell materially, **regardless of EBIT sign** | 63 of 249 profitable names the guard cannot see | HIGH — flatters |
| 4 | Mark `trough_anchored` internal-only or rename it `oldest_year_is_min`; never surface it as a trap flag | 111 tagged, incl. 59 of 59 compounders | MEDIUM — false demotions |
| 5 | Carry `peak_is_window_edge` beside `melting`; prefer "no recovery in N years" on commodity-exposed names | 27 of 54 melting flags expire on the calendar | MEDIUM |
| 6 | Make the intake's "Trap flags" column and §6 routing render **from module fields only**, with the field named | the whole report layer | MEDIUM — it is the de-facto gate and it is unversioned |
| 7 | Jurisdiction-gate `provision_kind_hint` (Building Safety Act is England-only) | every Scottish/NI issuer | LOW |
| 8 | Reconcile share counts to the **filing**, not to three vendor estimates of each other | TFW's true gap was 2.7–6.6% against a reported 1.4% | MEDIUM |
| 9 | Net committed redemption / deferred-consideration liabilities before any net-cash claim | TFW £9.4m, SPR £22.0m — both in the notes, neither on the screen | MEDIUM — the THX shape, twice |
| 10 | Run the PFIC asset test on the **FMV** basis as governing, book as secondary | CLBS mislabelled MED when FMV is 0.464, under the line | LOW |

---

## 6. EXECUTABILITY — 4 MORE CONIDS RESOLVED (the shelf had 4 of 249)

| TIDM | conid | exchange | IBKR quote |
|---|---|---|---|
| WYN | 790402910 | LSE | close-only, no bid/ask |
| SPR | 292597291 | LSE | close-only, no bid/ask |
| CLBS | 90366471 | LSE | close-only, no bid/ask |
| **TFW** | **132919882** | LSE | **LIVE two-sided (`is_close=false`)** |

**Refinement to the standing doctrine.** The desk note says IBKR close-only quoting is muni-specific
and that foreign equities stream live. On thin AIM lines that is **not** reliable: three of these
four returned `is_close=true` with an empty bid/ask, and only TFW streamed. The venue is permitted
and the line is executable in all four cases — but **pre-trade price discovery must come from the
exchange touch, not from IBKR, on AIM names.** Verify per line, as the addendum requires.

*Not written to `lse_conids.json` — that store belongs to the generator lane and the contract
forbids cross-lane writes. Hand these to the principal to merge.*

---

## 7. SCOREBOARD

- **Guards that fired correctly: 2 of 4** (CLBS EBIT-negative; WYN melting, on a fragile mechanism).
- **Guards that were wrong: 1 of 4** (SPR net debt — stale, seasonally mis-struck, and refuted by a
  public document older than the shelf).
- **Flags that the module never fired and the report invented: 1 of 4** (TFW trough-anchor).
- **Names actually demoted by the code: 0 of 4.** All four were printable, ranked 12–15.
- **Guards that failed silently in the flattering direction: 3** (`wc_fcf` on SPR; net cash on TFW
  and SPR; share count on TFW) — these are worse than a false demotion, because nothing prompts a
  reader to check them.
- **Net effect on deployable capital:** two starters surfaced (SPR, TFW) that the intake's routing
  paragraph had sent to "skip" or left uncourted, and two rejections confirmed — one of them
  upgraded from a rejection into a **positive honesty finding** (CLBS ELEVATE).

**One self-correction recorded:** the WYN court's first draft argued the exceptional add-back was a
recurring operating cost. Primary sources refuted it (FY23 non-recurring was £82k; H1 FY26 was
nil; the FY25 charge's net cash cost was £2.0–2.5m). The REJECT survives on business quality and
execution; the reasoning that produced it did not.
