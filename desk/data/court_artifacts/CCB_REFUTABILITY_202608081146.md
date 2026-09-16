## Context

CCB is not a cohort casualty — it is a single-name credit event with a named cause: a **$68.8M pre-tax charge on one CCBX banking-as-a-service partner** (Q2 print, 2026-07-30), which took the stock $70.66 → $39.91 in a day. The screen caught it on `dd52 -0.634`, but the drawdown is two-stage ($120.05 → $70.66 *before* the event, then −43.5% on it), so the "sold indiscriminately on one narrative" premise does not hold here. The decisive document — the 10-Q — was filed **2026-08-07, one day ago**.

| ticker | class | refuting metric | current value/trend (cited) | next print date | note |
|---|---|---|---|---|---|
| CCB | **DAMAGE-ARRIVING** | Credit-enhancement asset realization: the CE asset balance net of new enhancement income accrued (i.e. cash actually collected from partners), and its coverage by partner-pledged cash reserve accounts | CE asset **$180.6M (3/31/26) → $154.3M (6/30/26)** after a **$46.0M** write-down → implies **~+$19.7M net accretion ex-write-down**; pledged cash collateral **~$72M → ~$100M YoY**. Receivable is compounding faster than the collateral behind it. Q2 provision **$92.2M** offset by **$70.7M** of "BaaS credit enhancement" noninterest income ([company release, 2026-07-30](https://www.globenewswire.com/news-release/2026/07/30/3335871/0/en/Coastal-Financial-Corporation-Announces-Second-Quarter-2026-Results.html)) | **2026-10-29** — yfinance-derived, UNCONFIRMED | Damage is already printed, magnitude is not. Mgmt guides resolution "1–2 quarters to 12–18 months" on the ~$500M partner pool ([American Banker](https://www.americanbanker.com/news/how-concentration-risk-hit-one-banking-as-a-service-provider)) |

**Why not DAMAGE-ABSENT:** the narrative's predicted damage is *in* the numbers — $42.1M net loss, $(2.76) EPS, ~1pt of capital, and $46.0M of previously recognized income reversed.

**Why not STRUCTURAL:** the mechanism performed on the rest of the book — partners were contractually responsible for **98.0% of the $50.6M** of Q2 CCBX net charge-offs; every capital ratio remains above well-capitalized (Co. CET1 10.86%, Total RBC 13.30%); NII hit a record $89.4M and program income grew 10.3% QoQ.

**The structural tell that keeps it out of DAMAGE-ABSENT.** The enhancement asset is an **unsecured receivable from mostly private fintechs, with wrong-way risk** — the partner owes most exactly when its own book is worst, which is when it can least pay. Aggregate coverage looks fine (~$100M collateral vs $154.3M asset) but **collateral is partner-specific and non-fungible**: you cannot apply Partner B's reserve to Partner A's shortfall. That is precisely how a 24%-of-book partner blew through its own reserve while the aggregate read ~65% covered. Residual $154.3M = **33.7% of tangible common equity** ($30.05 TBV × ~15.25M sh ≈ $458M).

Second tell: management's assurance that "all other CCBX partners maintained ratings of Low/Moderate or better" is **self-graded, and the rating scale did not lead the loss** — the affected partner was presumably also rated acceptable ~90 days before a $68.8M charge. That statement carries near-zero information.

## COURT-WORTHY (damage-absent, ranked)

**NONE.** CCB classifies DAMAGE-ARRIVING, so it does not qualify for this list. It still escalates on court-worthiness below, for a different reason: valuation two-sidedness, not damage-absence.

## Court-worthiness

**COURT-WORTHINESS CCB: 6/10** — the sizing decision hinges on one undisclosed-but-possibly-derivable number (partner-level concentration of the $154.3M enhancement asset and its partner-specific collateral) sitting in a 10-Q that is one day old and almost certainly unread.

What makes it live: at **$43.93 vs $30.05 TBV = 1.46× tangible book**, this is *not* a distressed multiple — the −63% removed a growth premium (it was ~3.4× TBV at the high), it did not create a margin of safety. The court either finds the mechanism intact ex-one-partner (then 1.46× TBV on a franchise growing NII to records is cheap) or finds the receivable impaired (then TBV itself is overstated by up to 33.7%). Those two answers size very differently. **CEO Eric Sprink bought 10,000 shares at $44.45 on 2026-08-06** — post-charge, pre-10-Q, taking him to 173,238 shares ([Investing.com](https://uk.investing.com/news/stock-market-news/coastal-financial-ceo-eric-sprink-buys-444500-in-company-stock-93CH-4820674)) — a gradable signal from the model's architect.

What caps it at 6, not higher: the Street has already re-rated to roughly spot (TD Cowen $110 → **$47**; Raymond James $100 → **$50**, downgraded), securities-fraud investigations are announced (Holzer; BFA), so `discovery_state` is **DISCOVERING/CROWDED, not UNDISCOVERED** — which per doctrine gates the divergence. And CCB has never broken partners out individually, so the court carries real risk of returning "undisclosed → unresolvable."

**The court's single mandate should be:** rebuild the credit-enhancement asset rollforward from the 2026-08-07 10-Q — accrued vs. collected, and pledged reserve balance per partner if disclosed — plus entity-resolve the ~$500M partner (non-public, deteriorating through 2026) and check its solvency directly. Do not let it become a general re-litigation of the BaaS model.

## PRINT PROXIMITY

**PRINT PROXIMITY: 2026-10-29 — yfinance-derived, UNCONFIRMED.** ~57 trading days out, far outside the 5-day window, so no print-decisive reconstruction is mandated. CCB announces its date by 8-K about a week prior (it filed [that 8-K on 2026-07-23](https://www.globenewswire.com/news-release/2026/07/23/3332638/0/en/Coastal-Financial-Corporation-to-Report-Second-Quarter-2026-Results-and-Host-a-Conference-Call-on-July-30-2026.html) for the 7/30 print) — treat late October as unconfirmed until that 8-K lands.

**Position (book shows NO POSITION / NO ORDERS): FLAT.** Not because the bear case is proven, but because 1.46× TBV pays nothing for an unresolved counterparty receivable worth a third of tangible equity, on a ~12–18-month resolution clock. There is no entry premium here to capture; wait for the court's rollforward, or for a price that discounts the $154.3M rather than the $46M already taken.

## Two caveats on my own work

1. **SEC.gov 403'd every fetch** (browse-edgar, data.sec.gov, and the 10-Q at `Archives/.../ck1437958-20260630.htm`), and Bash is disabled this session, so I could not apply the usual full-Chrome-fingerprint workaround. Every figure above is from company-issued releases and the Q2 slide deck, not from my own read of the 10-Q. **The partner-level concentration table is the one thing I could not verify and the one thing that decides the case** — that gap is the reason for the escalation, not an incidental omission.
2. The **$70.7M** BaaS-credit-enhancement income is reported as a Q2 figure in one source and a six-months figure in another. The Q2 reading reconciles cleanly ($92.2M provision − $22.8M non-recoverable ≈ $69.4M offset), so I used it, but the court should confirm it off the income statement.

I also could not execute the standing closing step — ledger upsert, edge classification, entry plan, scanner re-run, `/api/everything` verify — because Bash is disabled here. **This triage is not yet reflected in the dashboard.**