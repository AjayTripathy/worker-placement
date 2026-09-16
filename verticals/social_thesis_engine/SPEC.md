# Social-Thesis Engine — "Be the Casino" · PRE-REGISTERED SPEC

**Status: LOCKED 2026-06-25, before any P&L is accrued.** Sibling to the frontrun pilots
(`verticals/frontrun_engine/*`), built with the same discipline: pre-register the hypothesis,
the universe, the decision rule, the controls, and the kill criteria *before* trading, and prove
edge forward (paper) before sizing a dollar. Negative result is still the finding.

## 0. Thesis

Retail social attention (WSB, r/biotech_stocks, r/options, …) is **not a buy list** — it is a
**universe generator + an implied-volatility pump detector.** The crowding that makes a directional
trade dangerous (squeeze risk — the thing `discovery_state` was built to catch) is the *same* force
that richens the options. So the engine treats social as a feed into a decision matrix and leads
with the arm that fits the framework's actual competency: **SignalOS detects overstatement, not
direction.** "This move is built on a lie / the readout won't hit / the marketed number is
store-level" maps directly to "the IV is overpriced — sell the wing." That is direction-agnostic:
you profit from the realized *range* being narrower than the crowd's panic, which is far easier to
be right about than timing. It is the SLS covered-call logic generalized into a strategy.

## 1. Hypothesis (pre-registered)

> For tickers surfaced by a social-attention spike, **selling defined-risk options premium** on the
> subset where (a) our two-mode diligence judges the move OVERDONE/overstated, (b) options are
> RICH (IV elevated vs realized HV and vs the name's own IV history), and (c) the conditioning layer
> shows the name is NOT squeeze-fueled, earns **positive risk-adjusted return net of costs**.
> Secondary arm: the rare intersection of a diligence-REAL thesis on an UNDISCOVERED name is a
> directional long/short. Confirmation requires the vol-selling arm's forward paper P&L to beat a
> matched short-vol control (selling the same structures on random non-social-surfaced names of like
> IV) — i.e., the *social + diligence + conditioning* selection must add value over "just sell vol."

## 2. Universe (objective, point-in-time)

- **Source:** daily pull of r/wallstreetbets, r/stocks, r/options, r/biotech_stocks (extensible),
  ranked by mention count + velocity (`reddit_mentions` connector). A ticker enters the candidate
  set when its mention count crosses an attention threshold (pre-set: ≥ name's own trailing mean +
  2σ, or top-15 cross-sectionally that day).
- **Liquidity gate:** the name must have a listed, tradeable options chain with non-trivial OI and a
  bid/ask we can actually transact (no penny-wide phantom quotes). Else EXCLUDED, logged.
- **Ticker resolution:** cashtags ($XYZ) + uppercase tokens validated against the SEC
  company_tickers universe, minus a stoplist of all-caps non-tickers (DD, YOLO, CEO, FD, ER, IV …).

## 3. The decision matrix (LOCKED)

For each candidate, cross **diligence verdict** × **conditioning regime** × **IV richness**:

| Diligence | Conditioning | IV | → Action |
|---|---|---|---|
| Overstated / move overdone | crowded, **no** squeeze fuel | RICH | **SELL premium** (defined-risk) — primary |
| Real thesis | **UNDISCOVERED** | any | Directional long/short — secondary, rare |
| Real thesis | crowded | RICH | Already priced — sell vol or pass |
| **Any** | crowded **+ squeeze fuel** (high SI% / FTD spike / low days-to-cover) | any | **HARD VETO** — no premium selling, no naive short |
| any | any | CHEAP (IV ≤ HV) | no vol sale; directional only if diligence-real |

The squeeze-fuel veto is absolute: never sell premium (or short) into a name `discovery_state`
flags squeeze-fueled. Pennies in front of a steamroller is the documented failure mode (GME/AMC).

## 4. Signals (pre-registered definitions)

- **Attention** = `reddit_mentions` (count, velocity, bull/bear lean) → feeds `discovery_state`.
- **Conditioning** = `discovery_state(ticker)` → regime + positioning_score + the squeeze-fuel
  drivers (short_interest_pct, days_to_cover, FTD). Already built; this is the veto + crowding read.
- **IV richness** = `iv_richness(ticker)`: IV vs 30d realized HV (IV/HV ratio) + IV percentile vs the
  name's own history. RICH = IV/HV ≥ 1.20 AND IV-percentile ≥ 70 (pre-set, tunable only with a
  logged amendment). CHEAP = IV ≤ HV.
- **Diligence verdict** = `signalos-quant-analyst` two-mode pass (Mode A claim-verification + Mode B
  disconfirmation; the honesty/overstatement detectors). Output ∈ {OVERSTATED, REAL, INCONCLUSIVE}.

## 5. Trade construction (LOCKED — risk discipline is the strategy)

- **DEFINED-RISK ONLY.** Vol sales are spreads / iron condors / cash-secured puts / covered calls —
  **never naked** short options. Max loss per trade is bounded and pre-computed.
- **Sizing:** each position risks ≤ a pre-set small % of the sleeve; the book is many small
  uncorrelated casino bets, not a few large ones (the house edge is in the law of large numbers).
- **Squeeze-fuel veto (§3)** is a hard gate, checked at entry AND before any add.
- **Borrow/assignment:** for CSPs/covered calls, assignment is acceptable (we'd own/sell the
  underlying we already diligenced); for spreads, defined max loss caps it.

## 6. Controls & how we prove it (the honest part)

- **No historical backtest** — point-in-time Reddit data barely exists (Pushshift dead, API gated),
  so a historical backtest would be survivorship-poisoned fiction. Instead we run **FORWARD, paper
  first:** a daily cron logs every candidate `(date, ticker, mentions, regime, squeeze_fuel,
  IV/HV, IV-pctile, diligence_verdict, matrix_action, the exact structure + entry credit)` to
  `outputs/social_thesis_log.jsonl`, then a scoring job stamps realized P&L at expiry. The track
  record is built prospectively and is survivorship-free by construction.
- **Matched short-vol control:** for every "SELL premium" candidate, the log also records the same
  structure on a RANDOM non-social, like-IV name. Edge = paper-P&L(engine) − paper-P&L(control). If
  the control matches the engine, the social+diligence+conditioning selection adds nothing → kill.
- **No fishing:** §2 thresholds, §3 matrix, §4 RICH cut, §5 risk rules are LOCKED pre-data.

## 7. Success / kill criteria (binary, pre-set)

- **Scale:** over ≥ 8 weeks of forward paper, the SELL-premium arm shows positive P&L net of modeled
  spread/slippage AND `edge(engine) − edge(control)` positive AND the squeeze-fuel veto recorded
  zero blow-through losses. Then size small real capital.
- **Kill:** engine ≈ control (no selection edge) OR the veto leaks (a squeeze-fueled name slipped
  through and gapped) OR realized vol ≥ implied on the sold names (IV wasn't actually rich). Negative
  result encodes the microstructure (social attention does/doesn't predict overpriced vol).

## 8. Phasing

- **Phase 0 (this spec):** LOCKED.
- **Phase 1 (THIS BUILD):** stand up `reddit_mentions` (social feed), `iv_richness` (IV vs HV +
  percentile), and `triage.py` (funnel: social → rank → `discovery_state` + `iv_richness` → decision
  matrix → log). Output a ranked, conditioned candidate list with the matrix action — *pre-diligence*.
- **Phase 2:** wire the `signalos-quant-analyst` diligence pass on the top candidates (fills the
  diligence-verdict column); begin the forward paper log + matched control.
- **Phase 3:** daily cron; accrue ≥ 8 weeks; evaluate §7. Size real only if it holds.
