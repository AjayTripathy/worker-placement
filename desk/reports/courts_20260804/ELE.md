# ELE — IDENTITY RESOLVED: Elemental Royalty Corporation | COURT_QUEUE_20260804 tier-2 (GUIDE-DECEL)
Court 2026-08-03. **Live basis: IBKR $16.06** (is_close=true, 08-03 close; 52w range 12.56-26.92).

## 0. IDENTITY FIRST (the muni-matcher lesson, applied)
The queue note asked whether ELE is "Estrella?" and told me to resolve before courting. Resolved to
a single entity by two independent identifier sources:
| source | result |
|---|---|
| IBKR `search_contracts("ELE")` | **ELEMENTAL ROYALTY CORP**, Nasdaq conid **831070874** (also TSX conid 831080962, and a legacy CORPACT line "ELEMENTAL ROYALTIES CORP" conid 579657496) |
| yfinance `ELE` longName / sector | "Elemental Royalty Corporation", **Basic Materials / Other Precious Metals & Mining**, Canada |
| corroborating corporate actions | "Elemental Royalty Corporation Rings the Opening Bell" (Nasdaq, 2026-02-26); Russell 3000/2000 and **S&P/TSX Global Gold Index** inclusion (2026-06-17) |
Disambiguated **against** ELE = Endesa SA (Bolsa de Madrid, conid 30314174) and against Estrella.
Cap $1.03B, gross margin 95.6%, 3y revenue CAGR +65% all match the queue's row exactly. **RESOLVED,
not UNRESOLVED** — but resolved to the wrong cohort.

## 1. COHORT MIS-MAPPING (finding #1)
ELE is a **precious-metals royalty company**. It was queued into the tier-2
**consumer/health/comm** batch. The 96% "gross margin" and 65% revenue CAGR that made it look like a
software-grade compounder are the ordinary signature of a royalty vehicle: royalties carry almost no
cost of revenue by construction, and the growth is portfolio acquisition plus the gold price.
The screen's own `info["sector"]` field already said "Basic Materials" — the cohort label was applied
upstream of a field that was available. **Log as a queue-construction defect.**

## 2. GATE TEST — INPUT REFUTED ON BOTH SIDES (finding #2)
Gate: FY+1 rev growth (+6.3%) / most-recent-quarter yoy (+109%) = 0.06 -> fires hardest in the cohort.
- **Denominator is inorganic.** Ordinary shares went **24,576,259 (2025-09-30) -> 63,829,995
  (2025-12-31)**, a **+160%** issuance, with total equity $205.5M -> $780.4M in the same quarter.
  Q1'26 revenue of $24.3M against Q1'25's $11.6M is therefore a **share-issuance base effect**, not
  organic growth — the "acquisition step-up" PEG-distortion mode from the GARP work, in its purest
  form. Deal flow confirms it: Vizsla Royalties acquisition (05-14), Chapi/Quilla royalty increase
  (07-15).
- **Numerator is a single analyst.** `numberOfAnalysts = 1` on both the FY0 and FY+1 revenue lines.
- **And the data itself is broken.** The current-quarter consensus revenue in the same feed is
  **$21,585,000,000** against an actual quarterly revenue of **$24.3M** — a **~900x error**, carried
  into the flag with no sanity check. Proposed guard: reject any consensus revenue more than 5x TTM
  actual revenue. (Filed in `_GATE_TEST_GUIDE_DECEL.md`.)

## 3. WHAT IS ACTUALLY TRUE HERE (the one real signal)
Estimates **are** collapsing, but for a reason the gate did not see: FY26e EPS 0.506 (90d ago) ->
**0.300** (**-40.7%**); FY27e 0.750 -> **0.468** (**-37.6%**). Meanwhile the company markets
"Record 128% Increase in Revenue, Exceeding Guidance for 2025" (03-24) and "Record Quarterly Revenue
and Adjusted EBITDA" (05-13).
**That is a genuine takeaway-vs-data divergence in shape** — record *absolute* revenue alongside a
40% cut to *per-share* earnings — and the mechanism is the 160% share issuance sitting in the
denominator. It is not concealment: the issuance is a disclosed, index-inclusion-driving corporate
action. **Disclosed = CLEAN.** But an investor reading only the "record revenue" headlines would form
the opposite view of per-share economics from the one the numbers support. Worth cataloguing as a
royalty-sector masking *channel* even though this instance is honest.
Q1'26 reality check: revenue $24.3M, operating income $6.7M, **net income $1.08M** (~$0.017/sh).

## 4. PATH / FACTOR
-40.3% from the 52w high $26.92; 52w low $12.56 (2025-11-21); **+27.9% off it**. Eight moves greater
than 7% in four months (-12.3%, +8.8%, -9.4%, -10.4%, ...). This is **metal-price beta**, i.e. the
factor-costume case the screen's own residual-drawdown gate exists to catch. Nothing about the
drawdown is a quality-at-own-history de-rate.
Next print 2026-08-11.

## 5. RULING — no scenarios, no band, no freezable call
**REJECT 2/10 — OUT OF FRAME.** The name is not a consumer/health/comm quality de-rate; it is a
gold/silver royalty vehicle whose drawdown is commodity beta and whose gate flag rests on a 160%
share issuance, a single analyst, and a 900x data error. Courting it further as a tier-2 quality
name would be courting the wrong question.
It is **not** disqualified as an investment in general — a royalty vehicle at 1.1x book with rising
reserves (Karlawinda +32%, 07-29) is a legitimate thing to own; it simply belongs in a metals sleeve
underwritten on gold-price beta, NAV per share and issuance discipline, none of which this frame
tests. **Recommend: re-queue to a materials/royalty lane, or drop.**

## 6. VERIFICATION NOTES / GAPS
- CONFIRMED: identity (two identifier sources plus corporate actions), sector, the share-count jump
  and equity jump from the quarterly balance sheet, the quarterly revenue and net-income series, the
  estimate collapse, the 900x consensus-revenue error, the price path.
- **UNVERIFIABLE:** NAV per share, gold-price sensitivity per royalty, the Vizsla/Chapi consideration
  split (cash vs shares), and whether the "in-kind XAUT token dividend" (06-18) has any structural
  implication. None were pursued — the name is out of frame.

## 7. KILLS
Not applicable — no position contemplated. The only standing action is the queue fix in section 1
and the data guard in section 2.
