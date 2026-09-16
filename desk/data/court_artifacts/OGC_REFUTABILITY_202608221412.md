## Context

Cause-check first, per the template — and the trigger does not survive it. The event fields carry `sector: ""`, `industry: ""`, and `excess_dd` **exactly equal** to `dd52` (−0.361 both). That identity is the arithmetic signature of a missing sector median: the screen subtracted zero. There is no "−36.1pp excess vs cohort" — that number is an infra artifact, not a measurement. Rebuilt against a real external anchor (GDX, same close): **GDX −12.2% off its 52w high vs OGC −28.7%** — a real ~16pp gap, but a sixth of what fired the event. Tape cross-check: pack `px` 30.72 USD reconciles to the TSX close of CAD 42.75 at ~1.39 USD/CAD, and hi52/lo52 reconcile to CAD 59.20/22.71, so the pack's tape is sound (I could not re-poll IBKR directly — permission not granted this session).

| ticker | class | refuting metric | current value/trend (cited) | next print date | note |
|---|---|---|---|---|---|
| OGC | **DAMAGE-ABSENT** | Consolidated AISC margin/oz (realized gold − AISC) + FY guidance integrity | Q2'26 realized **$4,433/oz** vs AISC **$2,151/oz** = **$2,282/oz margin**; FY26 guidance **reaffirmed** (520–590koz, AISC $1,750–1,900, though mgmt flags **upper end**); net cash **$654.8M** vs $50.1M debt; TTM FCF **$737.8M**; buyback retired 231.1M→222.45M shares; $0.09 div payable Sep 18 ([Q2'26 results, 2026-08-06](https://oceanagold.com/news/oceanagold-reports-second-quarter-2026-results)) | **2026-11-04 (yfinance-derived, UNCONFIRMED)** — no company-named date found; Q2 landed 2026-08-06 | Margin-compression narrative is testably absent. Company deployed offense on 8/17: all-scrip acquisition of Ausgold, 6–8% dilution + up to A$194M cash pool ([SID PR, 2026-08-17](https://oceanagold.com/news/oceanagold-announces-acquisition-of-ausgold)) |

**COURT-WORTHY (damage-absent, ranked):**

1. **OGC** — damage-absent is genuinely verified against the print, but the dispersion has **already closed**, which is the finding that matters. OGC set its 52w high CAD 59.20 on **2026-03-02**, bottomed at CAD 31.05 in July, and closed **CAD 42.75 on 2026-08-21 against an August high of 43.80** — up ~38% off the July low and making multi-month highs. The screen fired 2026-08-18 on a `dd52` measured against a five-month-old peak, three days *after* the stock had already re-rated (px 27.55→30.72 USD in 3 sessions). You would be buying the recovery, not the dislocation.

The residual 16pp vs GDX also has named non-mispricing causes: OGC's 52w range ratio is 2.61 vs GDX's 2.02 (higher beta, so a deeper drawdown from a shared March peak is arithmetically expected), and **off the low OGC (+88%) has outperformed GDX (+77%)** — the signature of a high-beta name, not of a cohort member sold on one narrative.

Blue-teaming my own rejection: at EV ~$6.2B on TTM FCF $737.8M (~8.4x) with net cash, reaffirmed guidance, a 4%/yr buyback and a fifth asset added, the name is not expensive. But that is true of the entire GDX complex, and the market's actual bear case is the **sustainability of $4,400 gold** — which OGC's Q2 print cannot refute, because it confirms *realized* margin, not *forward* metal. The decisive variable sits outside the company's P&L, so company-level adversarial work cannot resolve it. That makes this a sector-beta/sleeve sizing question, not a court question — and a crowded one (mainstream coverage is already running "miners are finally catching up").

**COURT-WORTHINESS OGC: 4/10 — damage verifiably absent, but the entry has already closed (+38% off the July low, at multi-month highs) and the residual vs GDX is beta plus peak-timing, so a court would re-litigate a gold-price macro call it cannot settle.**

**PRINT PROXIMITY: 2026-11-04 — UNCONFIRMED (yfinance-derived; no OceanaGold PR or 6-K names a Q3 date; Q2 was released 2026-08-06, and no company-confirmed Q3 date appears in the filing record).** ~50 trading days out, well outside the 5-day window, so the print-decisive reconstruction is not triggered. The near-dated *dated* events are not earnings: dividend payable **2026-09-18**, Ausgold scheme booklet **late Oct**, shareholder meeting **late Nov** (75% approval threshold), implementation **Dec 2026**.

---

Two things worth acting on beyond the row:

**The screen has a live bug, and it will keep firing.** Any name reaching the class-dislocation stage with an empty `sector` gets `excess_dd = dd52`, which guarantees a maximal-looking excess score for every high-beta name in a normal drawdown. That is [beta-bleed dressed as dislocation] at the infra level. The fix is a preflight assertion that rejects the event when `sector` is empty or the sector-median cohort is under some minimum count, rather than silently defaulting the median to zero.

**The `dd52` trigger is stale by construction.** It measures against a 52-week peak with no recency weighting, so a name that fell in March and fully recovered by August still scores as maximally dislocated. OGC is the clean example: the event fired three days after the recovery was already underway. Adding a "drawdown from the trailing 20-day high" or a "% off the 52-week low" guard alongside `dd52` would have suppressed this one — OGC's `pct_off_low` of 0.835 was already sitting in the pack, contradicting the trigger.

Since the score is 4/10, this does not auto-escalate to a red/blue court.