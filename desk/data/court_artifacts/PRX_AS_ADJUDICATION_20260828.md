# PRX.AS — ADJUDICATION (Fable tier, 2026-08-28)
**Benches:** RED 202608280748 (REJECT, 8/10) / BLUE 202608280841 (overturned red's two headline proofs, sustained the conclusion on repaired grounds, 8/10). The 8/27 rubber-stamp ("OWNABLE — ~35% holding discount...") was reverted; this adjudication replaces it.

## Tape (adjudication-tier, live AEB)
**€38.605 LIVE** (Amsterdam intraday, conid 382625193; prior close €38.01); 52w €36.17–63.94, −39.6% off the high, +6.7% off the low — a live downtrend, not a stale dislocation; ADV-90d **$150.9M/day**. 1y bar-computed: PRX −25.9% vs Tencent (0700.HK) −22.5% — the wrapper underperformed its own driver, direction confirming both benches.

## THE DECISIVE FINDING, CONFIRMED AT THE COMPANY PRIMARY THIS TIER (blue's A — both benches initially missed it)
Prosus's own NAV page (27-Aug-2026, fetched at source): NAV **$150.4bn**, NAV/share **€61.5**, Tencent **$117.0bn** (2,049.1m sh @ HK$447.8), listed ex-Tencent **$7.6bn**, **unlisted $32.8bn**, net debt **$7.0bn**, shares 2,102.0m. The unlisted footnote verbatim: *"The valuations of unlisted assets are derived from the average estimates of sellside analysts, post-money valuations on transactions where analyst consensus is not available, and internal valuation for any remaining assets as at 30 June 2026."*
**21.8% of the NAV is sell-side marks.** Live discount at €38.605 = **37.2%**. Re-struck: unlisted at half-mark → ~29.8%; **unlisted at zero → ~20% discount to hard assets** (Tencent + listed − debt). Those marks throw $275m of ex-Tencent-dividend FCF — a **0.84% cash yield on the $32.8bn**. The headline discount is therefore part asset-discount, part wager on the same sell-side complex that quotes the discount. **NOVEL — the court's operative kill.**

## Findings adjudicated (blue's audit adopted)
- **F1 "discount flat" — REFUTED on repaired proof**: red's 48%-vs-35% "widening" was a denominator switch inside one MS note (PT-basis vs traded-basis) — the III artifact; the honest series is ~28–30% (Jun) → **37.2% (today, company NAV)**. Widening confirmed, red's evidence overturned. CONSENSUS.
- **F2 gearing arithmetic — SUSTAINED, red understated**: PRX is a **1.25×-geared Tencent proxy** (Tencent 77.8% of NAV; mcap 0.85× the stake net of debt). Constant-discount expected return −19.0% vs observed −29.75% ⇒ **~9.5pp of realized discount drift in 12m**, against buyback accretion of **+2.4%/yr** (4.5% of shares retired at a ~35% discount). **Carry loses to drift ~4:1** — the compounding term is currently negative. NOVEL.
- **F3 FCF pass-through — SUSTAINED as SIZING**: headline "record FCF $1.5bn" is $1.2bn Tencent dividends + **$275m ex-dividend**; the venue divergence (media release vs deep-dive) FIRED `multi_venue_disclosure_consistency`. Blue's strike of red's "liquidating distribution" clause adopted (a dividend on a retained stake is yield; the share SALES are the liquidation).
- **F4 NAV bridge — resolved by the primary**: net debt $7.0bn, discount 37.2% — red's direction right, arithmetic superseded by the company's own page.
- **F5 "GS owns our mechanism" — REDUCED to TIMING**: GS is Neutral €41 (+6% above spot) on a 30%-vs-40%-historical read — that is an external anchor we do not beat, not a bear case we're late to.
- **F7 flow gate — PARTIALLY OVERTURNED** (blue right: a standing corporate bid at 5% of mcap/yr is fill support, not predicted forced selling; Naspers permanent control sustains as the structural half). CONSENSUS.

## VERDICT: FLAT / REJECT-AS-THESIS at €38.61 — and the answer to the principal's original question, stated plainly:
PRX **is** the cleanest "Chinese growth under Dutch governance" instrument on any exchange we reach — but at today's structure you are paying a 37% headline discount of which only ~20 points are discount-to-hard-assets, for a 1.25×-geared Tencent claim whose +2.4%/yr buyback accretion has been outrun 4:1 by discount drift, with 22% of the "N" in NAV set by the sell-side. Tencent-with-friction is ownable at the right price; the right price is defined below, not here.
**Re-court gates (any one):**
1. **Discount ≥45% on the company's own NAV series** with Tencent stable (≈ €33.8 at current NAV/share — at that level even zero-value unlisted leaves a >30% hard-asset discount). Court-on-touch, NOT auto-entry.
2. **HY FY27 (~24–25 Nov, UNCONFIRMED)**: FCF ex-Tencent-dividends >$1bn — the ecosystem cash-validation red demanded.
3. **FY26 Annual Report**: audited unlisted carrying values vs the $32.8bn consensus mark (the same document closes the JET common-control WATCH and the Dutch participation-exemption tax note — three opens, one pull).

## Proposed tripwire (PROPOSED-NOT-STAGED, §BANDS-OVER-RESTING-GTC)
Ledger `alert_below` **34.00** with self-explaining gate_basis: on touch, RECOMPUTE the live discount from prosus.com/NAV — **≥45% → court-on-touch (full re-court, not entry)**; <45% (NAV fell with the price — the Tencent-drawdown state) → no action, the gate did its job. Nothing rests; no native alert until the parent ratifies (this is a court trigger, not an entry).

## Kills census: 4 NOVEL (marks-circularity A; gearing/drift F2; embedded-negative-ecosystem B; carry-vs-drift C) / 2 CONSENSUS (F5 anchor, F7 control). Named kills defeat the minimum-starter default.

## Pre-mortem (v1.7, for the file)
**"If this position loses money, the most likely reason will be that we bought a 37% discount of which only 20 points were real — the unlisted marks deflated toward their 0.84% cash yield, Tencent fell with China, and the 1.25× gearing delivered both at once while the buyback's +2.4% a year never caught the drift."** Tripwire-less unknown: a Naspers-level control-stack decision (cross-holding collapse, new structure) — announced, never telegraphed; class: controller-initiated perimeter change.

## KG rulings
- blue `analyst_consensus_mark_nav_circularity` — **ACCEPT-PRIORITY, desk-gold, primary-verified at this tier** (the footnote is on the issuer's own NAV page; the re-strike test at 50%/0% marks is mechanical).
- red `associate_dividend_passthrough_fcf_masking` — **ACCEPT-AMENDED** (strike the "liquidating distribution" clause per blue; the <40%-of-headline threshold stands; fired here at 18%).

## Calibration (parent to freeze)
**PRX-HYFCF**: "HY FY27 FCF ex-Tencent-dividends > $1bn" — p=0.25, cat 2026-11-24-UNCONFIRMED, px 38.61. (0.25 = the $275m base needs ~4× in a year; the informative outcome is a HIT, which reopens the file bullishly.)

## Unverified ledger (parent to file)
FY26 AR audited unlisted carrying values vs the $32.8bn consensus mark; Dutch participation-exemption confirmation (Tencent disposal tax — decides how much of the discount is tax artifact vs closable friction); JET common-control business-combination note; computed monthly discount series (owed once IBKR history permission covers AEB).
