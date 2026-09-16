# Bond-Desk Call Script — CA Muni HTM Book

_As of 2026-06-22 (universe re-marked to latest tape). Hold the **RFQ_BOOK** sheet open while you call (it has every CUSIP, the offer, and your par-capped test bid). Where to call: your brokerage's **fixed-income / municipal desk** (Vanguard, Fidelity, Schwab) — **not** IBKR, whose muni inventory is thin. Goal: live two-sided markets + offers **on your list**, and fills at your resting bids. ~$1.04M book, ~$40k/name, all DD-confirmed BUYs._

> **You are migrating out of VCLAX Admiral, not deploying cash.** Fund each fill by selling VCLAX shares to match — you stay duration-matched the whole way, so a rate move while you build washes out (the fund and the bonds move together). **No rush:** the bonds cost ~1–1.5 pt one-time in odd-lot markup, so payback on the switch is ~4–5 years — there is **zero penalty for being patient and every reason not to overpay to get in fast.** Buy a name only when it's clean and at/below your level; sell the matching slug of VCLAX that day.

---

## 0. Before you dial (30 seconds)
- RFQ sheet open · account number ready · this is a **hold-to-maturity** CA tax-exempt ladder
- Confirm you can **sell VCLAX same-day** to fund whatever fills (Admiral shares settle T+1; line up the cash so you're not buying on margin)
- Mindset: **you are not being pitched** — you are bringing a worked list and asking *them* to show markets on *your* names.

## 1. Open
> "Hi, this is **[name]**, account **[#]**. I'm building a **hold-to-maturity California municipal ladder** and I have a **bid-wanted list — 26 CUSIPs, about $1 million total, roughly $40,000 a name.** Can you work it and show me markets?"

If they start suggesting other bonds:
> "Appreciate it, but I've already done the credit work on these specific names. I want **two-sided markets and offers on my list**, not new ideas — at least to start."

## 2. The ask (say this once, up front)
> "For each name I want three things: **(1)** a live two-sided market, **(2)** can you **source the offer at $40k**, and **(3)** where you can **fill at my resting bid.** I'll read them in maturity order."

## 3. Per name (read from the RFQ sheet)
> "**CUSIP [xxxxx], [issuer], [coupon] of [maturity]** — it last traded customer around **[offer px]**. My resting bid is **[test-bid px] / a [+X bp] concession**. Can you hit that, or show me your best offer?"

**Decision rules as they answer:**
- **Offer ≤ your test bid** → *"Done — lift $40k, pending my written confirm."*
- **Offer a touch above** (≤ ~5 bp) on a name you like → *"I can pay up to [offer]. Fill it."*
- **Offer well above your bid** → *"That's [X] back of where it traded customer last week — is that the real market, or can you do better?"* Then hold your level or pass.
- **Bid-only / "can't show an offer"** → *"Then I can't buy it today — skip it, next."* (No offer = not acquirable.)

> **⚠ CALL DISCIPLINE — never break this.** Every name is callable at **PAR (100)**; 21 within ~2 years. **Do NOT bid above par on any name.** Paying a premium on a near-par-callable makes your yield-to-WORST the call (well below the coupon) and forfeits the premium when it's redeemed. Three names show offers **above par** right now — **769076VE7 (Riverside 5s), 271014D58 & 271014D66 (EBMUD 5s)** — your bid on those is **capped at 100.0; let them come to you or pass.** Where the market is above par, we wait. We do not chase.

## 4. The thin / no-market names (manage expectations)
- **Palo Verde CCD (697479CB7)** is the one genuinely thin name — *"On the thin ones I'll pay a wider concession or wait; just tell me which you **simply can't source** so I'm not resting a dead bid."*
- **18 names have no recent customer *sell* on the tape** — there's no observed two-sided market, so for those: *"Confirm there's an offer to lift at all before I rest anything."*
- **~13 names are SELF-DIRECTED-liquid** — you can hit a posted offer yourself online without the desk; use the desk for the thinner dozen + Palo Verde.

## 5. Book-level questions (before you hang up)
1. *"Any **odd-lot penalty** at the $40k clip — names where the price gets punitive small?"*
2. *"Any **better relative value** — same maturity, zone, credit quality — at a tighter spread I should swap into?"*
3. *"**Settlement** terms, and can you put the agreed levels **in writing** (email or on the platform)?"*

## 6. Close (say this every time — the discipline line)
> "**Don't execute anything until I confirm each one back to you.** Send me the levels in writing, I'll go name by name, and I'll approve the fills. These are all subject to my sign-off."

---

## Listen for (red flags)
- **Wide market** (> ~1 point bid/offer) = thin → only pay up if you really want it
- **"Can't show it"** = drop it, don't chase
- **Pushing alternative names hard** = they're moving inventory → be skeptical, verify before buying
- **Pressure to execute on the call** = decline; you confirm in writing, on your timeline
- **Any offer above 100.0** on a near-par-callable = the call-trap → bid par or pass

## Remember
- It's **hold-to-maturity** — every rung matures at par. Don't overpay to fill a name *today*; wait for your level.
- You're **funding from VCLAX** — sell the matching slug only as fills confirm; never run cash-dry or buy on margin (margin interest on a muni purchase is non-deductible under §265).
- **Nothing is committed until you confirm in writing.**

---

## Optional — duration-shortening adds (NOT in the core list)
Four short-dated names were EMMA-verified this cycle (tax-exempt + pledge). They **shorten** the ladder (6.7–7.6 yr) — only relevant if you want to pull duration down toward a fund-like 7.5 yr, which is the *opposite* of the 11yr-payout lean. Two are clean (**27677SCM3** Eastern MWD — sister to a book holding; **778389FS0** Ross Valley SD GO). Two are **credit-DD-pending — do not bid yet**: **764507DT3** (Richmond Wastewater) and **95942THD2** (W. Riverside Water) still need DSCR + supply underwrite. Keep these off the desk call until cleared.
