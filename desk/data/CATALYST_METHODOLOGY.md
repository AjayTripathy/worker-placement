# How SignalOS predicts catalysts

**What a "catalyst" is here.** A dated event that can re-rate a stock — an earnings print, a trial readout, a product launch, a regulatory decision, an index change, an order-book inflection. The question we answer isn't "what could happen" but *"does it resolve in our favor — and is that already in the price?"*

**1. We predict the outcome, we don't just list it.** For every catalyst we forecast three things, each tied to checkable evidence, not opinion:
- **Probability** it resolves favorably (shown as `p_favorable`, 0–100%).
- **Timing** — when it actually lands.
- **Magnitude** — how much of the price gap it would close.

The probability is built from *leading indicators*: management's guidance credibility (did they beat or miss last time), the order and production pipeline, peer read-across (competitors that report first), index rules and review dates, analyst-initiation timing, insider buying, and hard legal or contractual deadlines. We name the single **swing catalyst** that decides the outcome and the **tripwires** that tell us it's on-track versus breaking.

**2. We turn the probability into an edge.** We build three scenarios — bear / base / bull — each with a fair value and our own probability. From the *live price* we back out the probability the **market** is implying for the re-rate. The **edge** (shown in percentage points, "pp") is the gap between our probability and the market's. A positive edge means it's under-priced; a negative one means the market already pays for it. We also show **upside %** — our probability-weighted fair value versus the live price. Both must be meaningful: a big edge with tiny upside (a tight scenario spread) is not conviction.

**3. We try to kill every prediction.** Each call gets two independent passes — first verify the bull case against primary sources, then a skeptic that *assumes it's wrong* and hunts the disconfirming fact. A prediction only earns a position if it survives being attacked. That is why we surface the risks and the miss-case, not just the upside.

**4. We preview catalysts before they land.** Where peers report first, or leading data exists (production schedules, insider dealings, index thresholds), we update the probability *ahead* of the event instead of waiting for it — so by the time the catalyst prints, we already have a read.

**5. We keep ourselves honest.** Every catalyst call is scored after the fact — did the bullish ones go up and the bearish ones down — so we can see when we're miscalibrated or systematically too conservative, and correct it.

**When a catalyst becomes a BUY alert.** Only when three things line up at once: (a) a real probability **edge** (our odds clear the market's by a set margin), (b) the price is **in our buy band**, and (c) we are actually **constructive** — *not* a name we predict will MISS. A stock whose catalyst we expect to miss (low `p_favorable`) is never shown as a buy, even if its price falls into a technical band; it is flagged as a **conflict** instead, so a bearish call can never masquerade as "buy the dip."

*The numbers on these pages, in plain terms: `edge` is in percentage points — our probability minus the market's; `p_favorable` is our probability the catalyst resolves in our favor; "in band" means the live price has reached the level we'd actually buy at.*

**A position does not need an edge.** It is fine to own a name with NO claimed edge as long as we are roughly FAIRLY PAID to bear a risk we want at that size. "Fairly-paid risk" is the book's default allocation class; edge positions are the overlay on top. What a fair-carry buy still requires: the fairness is *verified* (the premium isn't hiding a trap — that's what the diligence is for), the tails are bounded (binary risks capped and unlevered, correlated names capped as one sleeve), and the label is honest — each name's explainer says plainly whether it's an edge claim or paid-to-bear carry. Being underpaid for a risk (a great company at too high a price) is still a pass.

---
**The full end-to-end discipline** — from idea generation through trap-screen, two-mode deep diligence, catalyst prediction, red-team, honest classification, pre-registration, sizing, propagation, execution, and resolution — is codified in `THESIS_PIPELINE.md` (canonical v1.0, 2026-07-02). Every stage names its executor, and the standing invariant is the separation of judgment from scoring: the analyst engine produces probabilities; deterministic modules freeze, monitor, and grade them. The generator never grades itself.
