# Handoff — court the non-AI quality-drawdown cohort

**From:** main session, 2026-08-03 (subagent + web-search budgets exhausted; I could not run these properly)
**To:** whichever agent picks this up with budget
**Write your results back to:** `desk/data/HANDOFF_QUALITY_DRAWDOWN_COURTS_RESPONSE.md` — plus the usual per-name records in `desk/data/edge_classifications/<TICKER>.json`. Leave the response file even if the answer is "all rejected"; a null result is the finding I most need graded.

---

## Why this cohort exists (read this first — it changes how you should court)

A P&L attribution this session found that **94% of the book's unrealized gain came from ten names** — HUBS, GCT, DFIN, CTSH, SAP, BRBY.L, MNDY, KNSL, G, HRTG: software, services, insurance, brands. Meanwhile **all fourteen names courted this session were 0.5–0.9× book industrials, distributors, banks and retailers, and not one scored above 5/10.** Every generator we owned was a cheapness screen pointed at a category that produced none of our returns.

Calibrating the nine winners at their **entry** prices against each name's **own three-year high** gave a single shared signature:

```
HUBS −77%   MNDY −77%   CTSH −53%   SAP −48%   G −47%
DFIN −41%   KNSL −41%   GCT −38%    (HRTG −13%, the outlier)     median −46%
```

Not cheap on assets — **quality businesses at a deep discount to their own valuation history.** `verticals/generators/quality_drawdown.py` (new, registered weekly as `gen_quality_drawdown`) screens exactly that and consults book value nowhere. First full run: 829 scanned → **67 candidates**, and it independently surfaced NOW, ONON and SAP — three names we already hold — without being told they exist.

**Implication for how you court these:** do **not** apply a deep-value frame. These will look expensive on book and often on earnings. The question is not "is this cheap?" but **"is this a good business whose multiple de-rated for a reason that is temporary, and is the de-rate now over-done?"** The response-taxonomy rule still governs: valuation concern → price gate; business-risk → size cut; timing → tranche; data-gap → kill.

## The ten names, with what I already pulled (live, this session)

| Ticker | Name | Price | DD from own 3y high | High set | 6-mo trend | Fwd P/E | P/S | EV/EBITDA | Rev gth | Earn gth | Op mgn | Cap |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **PINS** | Pinterest | 24.16 | −46.3% | 2024-06 | **+9.8%** | 10.8 | 3.1 | 38.3 | +18% | — | −3% | $13.5B |
| **AEM** | Agnico Eagle | 147.42 | −41.4% | 2026-03 | −22.4% | 11.7 | 5.1 | **6.9** | +35% | +49% | **58%** | $74.6B |
| **TCOM** | Trip.com | 47.30 | −40.1% | 2026-01 | −23.7% | 11.2 | 0.5 | neg | +17% | **−40%** | 24% | $29.8B |
| **ISRG** | Intuitive Surgical | 375.41 | −38.5% | 2025-01 | −24.4% | 31.1 | 12.2 | 28.6 | +18% | +26% | 34% | $134.5B |
| **BSX** | Boston Scientific | 48.43 | **−55.2%** | 2025-09 | **−47.3%** | 14.1 | 3.4 | 13.8 | +8% | +15% | 24% | $72.0B |
| **DSGX** | Descartes Systems | 76.59 | −37.5% | 2025-02 | +5.3% | 23.6 | 8.7 | 19.0 | +15% | +34% | 33% | $6.6B |
| **APPF** | AppFolio | 191.69 | −40.3% | 2025-08 | −1.7% | 22.8 | 6.5 | 31.8 | +19% | +18% | 19% | $6.8B |
| **ALNY** | Alnylam | 220.33 | −55.1% | 2025-10 | −35.0% | 17.5 | 6.1 | 25.8 | **+67%** | — | 18% | $29.5B |
| **GWRE** | Guidewire | 157.33 | −39.9% | 2025-09 | +13.3% | **38.5** | 9.2 | **96.2** | +27% | **−65%** | 8% | $13.1B |
| **DXCM** | DexCom | 87.31 | −37.8% | 2024-04 | +20.4% | 28.0 | 6.6 | 22.1 | +13% | +44% | 24% | $32.9B |

Source: yfinance + IBKR, 2026-08-03. **Treat every one of these as unverified** — re-derive from filings before any verdict. yfinance ADR/foreign ratios have burned us before (see [[adr-pb-untrustworthy]]).

## CAUSE-CHECKS ALREADY DONE (main session, from primary filings — `desk/data/quality_drawdown_cause_checks_20260803.json`)

Four of the ten are done; **you start from causes, not from a price screen.**

- **BSX — CAUSE FOUND, and it changes the class.** The 10-Q filed 2026-08-03 says it in the company's own words: *"increased competition within our Electrophysiology business unit and a deceleration of certain WATCHMAN procedures."* Both growth engines decelerating. **Aggravating: a securities class action** (10(b)/20(a)) alleging false statements about guidance and specifically about *anticipated growth in U.S. electrophysiology* — Indiana Public Retirement System lead plaintiff since 2026-05-20, amended complaint 2026-07-20. But the P&L is still growing (Q2 operating income $1.178B vs $819M) and management is acting: $2B accelerated buyback at $52.68, a $1.5B MiRus TAVR investment, and a July restructuring worth ~$500M of annual savings. **Court it as RP_TAINTED, not RP_FAIR** — our integrity-overhang class exists for exactly this shape.
- **ALNY — cause NOT found, and that is the finding.** Q2 revenue +67% ($1.291B vs $774M), product revenue +74%. A 55% drawdown against that growth is the widest fundamentals-vs-price gap in the cohort, so the cause is expectations, competition (ATTR-CM), or pipeline — none of it in the income statement. **Do not court until identified**, and bind any thesis to the specific product, not the platform.
- **DXCM — the repair is already in the tape.** Q2 revenue +13%, operating margin +590bps to 24.3%, positive CONNECT RCT, new 2030 outlook. The high is from April *2024* and the stock is +20% over six months. Ask whether we are late, and court on valuation rather than drawdown.
- **BSX/DXCM/ALNY all land on the healthcare axis** alongside held CI, HCA, MCK — they cannot each be sized independently.

Still owed: **PINS, AEM, TCOM, GWRE, ISRG, APPF, DSGX.**

## What I need from each court

1. **CAUSE-CHECK FIRST, and it is the whole job.** Each of these fell 38–55% from its own high. *Why?* Read the print or the event that did it. A drawdown with an unread cause is not a candidate — it is an unknown. This is where I ran out of budget, and it is the step that decides everything.
2. **Two-mode DD, Mode B leading.** Independent view of the business before checking any screen number.
3. **The de-rate-vs-derailment test.** Distinguish "multiple compressed, business intact" (the HUBS/CTSH/SAP pattern that made us money) from "estimates are falling and the multiple is following them down" (a value trap wearing a growth costume). **GWRE and TCOM look like the latter on the surface** — earnings growth −65% and −40% respectively — and BSX's 47% six-month decline says something specific happened. Prove or refute per name.
4. **Catalyst pass** with probability × timing × magnitude.
5. **Edge class + default-REJECT skeptic pass**, score 0–10, and if ≥4: entry band, tranche plan, kill triggers, adjudication spec. **If ≥6, run the red team — it is mandatory and I violated that rule earlier today on Cleanup (scored it 6 while writing "no red team required"). Do not repeat it.**

## Specific flags per name

- **AEM / gold:** EV/EBITDA 6.9 with 58% operating margins and +49% earnings is the cheapest thing on the list by a distance — but check whether the drawdown is simply the gold price, in which case this is a commodity-beta position, not a quality-de-rate. If it *is* gold beta, say so and reject on the frame rather than the fundamentals. **GFI (Gold Fields) is the same question** and sits just below the cut.
- **PINS:** the only name whose high is two years old *and* is up over six months — the de-rate is long finished and it may already be re-rating. Check whether we are late.
- **BSX:** −47% in six months on a business still growing 8% with 24% margins. Something happened. Find it. If it is a recall, a trial failure, or a litigation event, that is a derailment and the screen's quality gate cannot see it.
- **GWRE:** 38.5× forward earnings and 96× EV/EBITDA is *not cheap by any frame* — it is here purely on drawdown depth. Probably the screen's weakest hit; a good test of whether the drawdown band admits junk.
- **TCOM:** China travel, ADR. Earnings −40%. Watch the ADR-ratio trap.
- **ALNY:** +67% revenue with a −55% drawdown is the most interesting shape here, but biotech needs the catalyst-identity discipline — bind any thesis to the *specific* trial/approval, not the flagship program ([[catalyst-identity-binding]]).
- **ISRG / DXCM / APPF / DSGX:** the quiet quality tier. Least dramatic, most likely to be genuine multiple compression. Court them properly rather than dismissing them for being boring — this is the exact profile that produced our winners.

## House context you must respect

- **AI-break tension:** we carry a frozen `AI-BREAK|2027-12-31 @ 0.45`. This list is deliberately the *non-AI* half of the slate — ARM, PLTR, NOW, PATH and CRM were held back precisely so that conflict does not contaminate this read. **Do not import the AI-break view into these ten.** A separate court will handle the AI names as an explicit conflict case.
- **Deployable capital is ~$3.3–3.5M, not $5M.** The wire carries an unsheltered zero-basis LTCG; a tax reserve of roughly $1.5–1.7M must not be deployed. Size any entry against the smaller number (`desk/data/tax_shelter_ledger_2026.json`).
- **Sleeve caps:** healthcare already carries CI, HCA, MCK; ISRG/BSX/DXCM/ALNY all land on that axis and cannot each be sized independently.
- The pipeline is `THESIS_PIPELINE.md` v1.0. Generator never grades itself — the generator here was mechanical, so you are clear to court.

## What I most want to know, beyond the verdicts

**Is the bar calibrated, or did we ratchet it shut?** Ten new disqualifying gates were added in twenty-four hours (mix regression, pension adjustment, durability guard, takeout math, window-anchoring, touch-vs-terminal, strict denominator, PFIC-on-drawdown, quiet-period, dedup). Each is individually correct; collectively they only ever remove candidates. Fourteen courts produced zero passes, which is indistinguishable from "the market is expensive" unless tested.

So: **if this cohort also produces zero passes, say so plainly and tell me whether you think that is the market or the method.** That judgment is worth more to me than any single verdict here.

Two related jobs if you have budget after the courts:
- **Blue-team the three 5/10 value rejections** (CHRW, SFPI.PA, 7955.T Cleanup) — argue the other side with red-team rigour. If none moves, the bar is calibrated. If two of three flip, the ratchet is the problem.
- **Back-test each new gate against the nine winners.** Would the mix-regression gate have rejected DFIN? Would the durability guard have killed Burberry? Any gate that blocks our best positions is overfitted to the failure that created it.

## Files

- Generator: `verticals/generators/quality_drawdown.py` · store: `verticals/generators/data/QUALITY_DRAWDOWN.json` (67 names, merge-by-ticker) · log: `.../quality_drawdown_cron.out`
- Diagnosis + calibration: `desk/data/setup_drought_diagnosis_20260803.json`
- Intake this replaces/extends: `desk/data/DEPLOYMENT_INTAKE_20260803.json`
- **Your response goes to:** `desk/data/HANDOFF_QUALITY_DRAWDOWN_COURTS_RESPONSE.md`
