# GATE GRADE — tier-2 EXHAUSTED tail (DOCN SPSC GLBE BRZE LXRX ARIS MUX SII UMAC) | 2026-08-03

Third gate deliverable of the batch, accumulating onto `_GATE_GRADE_tier2_falling.md` and
`_GATE_TEST_GUIDE_DECEL.md`. Cohort = the queue's bottom nine by score (17.0 - 39.1), all flagged
**EXHAUSTED**. Price basis: IBKR daily closes 2026-08-03 (TRADES/RTH, ib_insync bars).

**Headline: the EXHAUSTED flag is the most useful of the three gates graded so far — 5 clean true
positives out of 9 and only one name nearly buried — but its second mode is defective in exactly
the way the FALLING flag was, and the factor-costume gate failed a second and third time by a
mechanism the sibling lane's proposed fix does not address.**

---

## What EXHAUSTED actually computes

`verticals/generators/quality_drawdown.py:196-199`:
```python
exhausted = (off_low52 > MAX_OFF_LOW and days_since_low < FRESH_LOW_DAYS) or \
            (off_low52 > HARD_OFF_LOW)          # MAX_OFF_LOW 0.35, FRESH_LOW_DAYS 90, HARD_OFF_LOW 0.50
```
Mode 1 (fresh-low bounce) is sound. **Mode 2 is a naked ">50% off any low" with no date term and,
critically, no distance-from-the-52-week-high term.** Penalty `raw *= 0.45` (L332).

---

## Scorecard — 9 names, hand-graded against the flag's stated meaning ("you are late")

| name | live | % off 52w low | days since low | % below 52w high | genuinely late? | gate verdict |
|---|---:|---:|---:|---:|---|---|
| **DOCN** | 127.17 | **+394%** | 364 | −29.9% | **YES** (+144% YTD, high is 7wks old) | **RIGHT** (mode 2) |
| **SPSC** | 75.54 | +51.4% | 82 | −34.8% | **YES** (+26% in a month post-print) | **RIGHT** (mode 1 — textbook) |
| **GLBE** | 40.20 | +46.0% | 82 | **−3.3%** | **YES** — it is at its 52w high | **RIGHT** — cleanest TP in the batch |
| **LXRX** | 2.33 | +122% | 354 | −11.7% | **YES** (+101% YTD) | **RIGHT** |
| **UMAC** | 23.08 | **+197%** | 253 | −30.9% | **YES** (momentum/attention name) | **RIGHT** |
| **BRZE** | 25.69 | +62.7% | **161** | **−29.0%** (−57% from 3y) | **NO** — mid-recovery, business inflecting | **WRONG — the near-miss** |
| **ARIS** | 14.39 | +113% | 346 | −36.6% | **NO** — closed **AT** its 60-day low | **MECHANICALLY WRONG** |
| **MUX** | 17.83 | +80.4% | 346 | −38.6% | **NO** — 6% off its 60-day low | **MECHANICALLY WRONG** |
| **SII** | 104.06 | +67.3% | 346 | −37.3% | **NO** — 0.2% off its 60-day low | **MECHANICALLY WRONG** |

**Tally: 5 right · 1 wrong-and-costly (BRZE) · 3 mechanically wrong (all three reject anyway, on a
better-stated reason).**

That is a better hit rate than FALLING (4/7) and far better than GUIDE-DECEL (1/7). **EXHAUSTED
earns its keep.** It is also doing something the other two gates are not: it is separating
*de-rate from a plateau* (what the frame wants) from *give-back from a spike* (what it does not).
Five of the nine are V-shaped melt-up give-backs where the "35% off the 3-year high" that admitted
them to the screen and the "+100-400% off the 52-week low" that damns them are **simultaneously
true** — because the 3-year high is only weeks or months old.

---

## FINDING 1 — mode 2 repeats the FALLING flag's defect, in the opposite direction

The sibling lane found FALLING is blind to 52-week structure. **Mode 2 of EXHAUSTED is blind to it
too.** BRZE is +63% off a five-month-old low *and still 29% below its 52-week high and 57% below its
3-year high, with revenue growth accelerating 23.8% → 25.4% → 30.2% and its operating loss margin
halving.* It received the same 0.45 penalty as GLBE, which is trading 3.3% below its 52-week high.

It is the same class of error twice: **a one-dimensional path statistic standing in for a
two-dimensional path.**

### Proposed replacement — three modes, all using fields already computed
```python
exhausted = (off_low52 > 0.35 and days_since_low < 90)          # 1. fresh-low bounce (unchanged)
         or (off_low52 > 0.50 and pct_below_52w_high < 0.15)    # 2. round-trip complete (replaces naked HARD_OFF_LOW)
         or (off_low52 > 1.50)                                  # 3. 12-month melt-up give-back (new)
```
**Validation on this cohort — the rule must reproduce the hand grading exactly:**

| name | mode 1 | mode 2 | mode 3 | result | hand grade |
|---|---|---|---|---|---|
| DOCN | – | – | ✓ (+394%) | EXHAUSTED | RIGHT |
| SPSC | ✓ (82d) | – | – | EXHAUSTED | RIGHT |
| GLBE | ✓ (82d) | ✓ (−3.3%) | – | EXHAUSTED | RIGHT |
| LXRX | – | ✓ (−11.7%) | – | EXHAUSTED | RIGHT |
| UMAC | – | – | ✓ (+197%) | EXHAUSTED | RIGHT |
| BRZE | – | – | – | **clear** | RIGHT (de-flagged) |
| ARIS | – | – | – | **clear** | RIGHT (de-flagged) |
| MUX | – | – | – | **clear** | RIGHT (de-flagged) |
| SII | – | – | – | **clear** | RIGHT (de-flagged) |

9/9. Every de-flagged name still rejects, but on a correctly-stated reason: BRZE becomes the one
real candidate, ARIS/MUX become factor costumes, SII becomes a factor pass-through.

Mode 3 exists because DOCN and UMAC are 30% below their highs yet unambiguously late — the
distinguishing fact is the *velocity of the 12-month advance*, not the distance from the high.

---

## FINDING 2 (decisive) — the factor-costume gate failed twice more, by a NEW mechanism

The sibling lane found the gate ran the wrong *proxy* on CCJ (sector Energy → XLE instead of
industry Uranium → URA) and proposed an industry→proxy map. **That fix is necessary but not
sufficient. On ARIS and MUX the lookup was already correct and the gate still failed — because the
method is wrong.**

`quality_drawdown.py:271` computes `factor_costume` from the **3-year maximum residual drawdown**.
Compare that with an **episode decomposition** (drawdown-peak date → today, beta fitted on
pre-window data):

| name | episode window | screen's method (3y max resid DD) | episode method | verdict flip |
|---|---|---|---|---|
| **ARIS** | 2026-02-27 → 08-03, −41.1% | share **0.73** vs GDX → **no fire** | GDX beta 1.07, factor −37.0pp, residual −5.6pp, **share 0.90** | **miss → fire** |
| **MUX** | 2026-01-28 → 08-03, −40.5% | share **1.52-1.68** → **"anti-costume, do not demote"** | GDXJ beta 1.08, factor −37.6pp, residual **−1.0pp**, **share 0.93** | **certifies the OPPOSITE** |

MUX is the sharper case: the screen's method does not merely miss the costume, it **affirmatively
certifies MUX as idiosyncratic** — the same output the sibling lane correctly recorded as a valuable
*true* negative on COIN. Mechanism: MUX underperformed the gold complex badly in 2023-24, so its
3-year cumulative residual drew down *more* than its price ever did. **3y-max-residual-DD answers
"has this name ever underperformed the factor?", not "is THIS drawdown the factor?"**

### Combined fix (supersedes, does not replace, the sibling's fix)
1. **Industry→proxy map consulted before the sector map** (the sibling's fix — keep it, and add
   `Gold → GDXJ`, `Other Precious Metals & Mining → GDXJ`, `Silver → SIL`, `Asset Management + PM
   AUM → GDX` as a manual override).
2. **Compute the residual on the drawdown EPISODE window** (`hi3y_date → today`), with the beta
   fitted on data strictly *before* the window. Keep the 0.60 threshold.

Validation targets: CCJ 1.03 → 0.51 (sibling), **ARIS 0.73 → 0.90**, **MUX 1.54 → 0.93**. All three
then take the existing `raw *= 0.30` demote and none reaches the queue. Sanity anti-target: DOCN's
episode residual share must stay high (measured: **−0.15 vs IGV, 0.20 vs ^NDX** — IGV was *up* over
DOCN's drawdown window, so the drawdown is genuinely idiosyncratic; DOCN must NOT be demoted by this
gate, it must be rejected on price and on the AI-complex conflict).

---

## FINDING 3 — a third factor sub-class the gate cannot see at all: pass-through with a lag

**SII (Sprott)** passes both versions of the costume test — episode residual share 0.42-0.53, i.e. it
fell about *twice* its 0.57 price-beta to GDX. On the numbers it looks idiosyncratic.

It is not. Sprott's revenue is a fee struck on AUM dominated by physical precious-metals trusts, so
ex-flows **fee revenue moves ~1:1 with the metal while the share price beta to miners is only 0.57**
— the price beta systematically understates the *earnings* beta for a fee-gatherer on a commodity
asset base. The check that resolves it:

> GLD is **−25.1%** off its Jan-2026 high. SII's FY+1 consensus EPS is **−21.8%** over 90 days.
> **A 0.9 pass-through.** The "idiosyncratic" residual is the market re-rating a fee stream that
> mechanically tracks the same commodity, arriving later than the miners' price move.

**Detector implication:** a regression on prices cannot catch this; it needs the earnings channel.
Narrow, high-precision candidate — `factor_passthrough`: fires when (a) the name's revenue base is a
fee/royalty on a commodity-priced asset, and (b) |Δ FY+1 consensus EPS over 90d| / |Δ factor spot
over the same 90d| lies in 0.7-1.3. Fires on SII (0.87). Should NOT fire on SPSC, BRZE, GLBE, DOCN.
Consistent with the desk's standing doctrine: compose narrow detectors by union, never by weighted
average.

---

## FINDING 4 — two screen-corruption guards the tail proved are missing

**(a) Accounting-basis guard — UMAC.** The lane brief predicted warrant-mark net income. **Warrant
marks REFUTED** (`ClassOfWarrantOrRightOutstanding` went to **0** at 2026-03-31; the FV adjustment is
de minimis). **The same corruption class CONFIRMED through a different channel:** Q1-2026 revenue
$8.10M, operating income **−$7.26M**, operating cash flow **−$17.41M**, yet net income **+$10.28M** —
driven entirely by `NonoperatingIncomeExpense` **+$17.54M** ($9.49M unrealized + $7.26M realized
investment gains) on a portfolio funded by a $150.0M equity offering. **Net income exceeds revenue.**
→ Guard should key on the *ratio*, not the warrant tag:
`NonoperatingIncomeExpense / abs(OperatingIncomeLoss) > 1.0` ⇒ accounting-basis reject.

**(b) Absolute revenue floor — UMAC, and a revenue-QUALITY test — LXRX.**
- UMAC: TTM revenue **$17.25M** against a **$1.10B** cap = **64x sales**; `rev3y` is `None` because
  there is no three-year history (reverse merger). **`MIN_REV_CAGR_3Y` could not evaluate `None` and
  silently passed it.** Add: TTM revenue ≥ $100M **or** cap/TTM-revenue ≤ 15x, evaluated *before* the
  GM and CAGR gates; and treat `rev3y is None` as a reject, not a pass.
- LXRX: `rev3y +610%` and `gm 94%` both scored as quality. The underlying quarterly series is
  **1.6 / 1.8 / 1.3 / 28.9 / 14.2 / 21.1 $M** — collaboration and milestone lumps, not a launch, and
  the 94% margin exists because there is barely a product. **A growth gate with no revenue-quality
  test reads a licensing lump as hypergrowth.** Candidate guard: flag when the quarterly revenue
  coefficient of variation over eight quarters exceeds ~0.8.

**(c) Sector carve-out.** `MIN_GROSS_MARGIN 0.35` passed MUX by 1.5 points. For extractive
industries gross margin is a spot-price artifact, not a quality signal. The gate should not run on
Basic Materials at all.

---

## FINDING 5 — entity resolution: a recycled ticker

NYSE `ARIS` is **Aris MINING Corp** (IBKR conid 588206703, dual-listed TSE:ARIS 588206705) — a
Colombia/Guyana gold producer. **Aris Water Solutions survives only as `ARIS.OLD` plus four
`CORPACT` tender lines** (`ARIS.STK / ARIS.MIX / ARIS.CSH / ARIS.PRO`): it was acquired by tender
and the symbol reassigned. The lane brief carried "ARIS = produced-water midstream," which is what a
stale ticker→name map produces.

**Any price history spliced across the tender boundary mixes two different companies.** Add a
ticker-recycling check to entity resolution (a `CORPACT` tender line or an `.OLD` suffix on the same
root is the tell), alongside the TCOM currency-basis and ADIG when-issued lessons.

---

## Batch outcome

9 courted · **0 at ≥6/10 — no red team required** · 1 at 4/10 with a below-market band (BRZE) ·
2 at 3/10 WATCH (SPSC, GLBE) · 6 rejects (DOCN 2, LXRX 2, SII 2, ARIS 1, MUX 1, UMAC 0).

**Print calendar dominated the lane — 6 of 9 are print-blocked:** DOCN **08-04 pre-market**,
MUX 08-05, SII 08-05 pre-market, LXRX 08-06, UMAC 08-06, GLBE 08-12. Only SPSC (printed 07-30,
next 10-29), BRZE (09-03) and ARIS (printed 07-29) have a clear window — and of those only BRZE is
a candidate.

**One honesty finding (review_flag, not ELEVATE): SPSC.** Every headline read "beats Q2 and *lifts*
EPS outlook" and the stock ran 26% in a month; the actual release **cut FY26 revenue guidance ~$10.5M**
and GAAP operating income fell **68%**, because the company sold the 3P Revenue Recovery unit for
$9.5M at a **~$20M loss, 17 months after buying it inside Carbon6**. Non-GAAP EPS rises precisely
*because* the discarded unit was margin-dilutive. Every datum is disclosed — the divergence is
framing, so it grades as a review flag, not a masking finding.

**Meta-observation for the generator.** All nine tail names are, structurally, the same object: a
big 12-month advance that gave back 30-40% from a *recent* high. That is what the intersection of
"35-78% off the 3-year high" and "score in the bottom decile" selects for. The tail of this queue is
not a pile of ignored quality — it is a pile of momentum give-backs, three commodity trackers and
one accounting artifact. **The one real business in it (SPSC) is fairly priced, and the one real
setup (BRZE) was flagged by mistake.** Worth deciding whether the tail is worth courting at all
before the next queue is cut.
