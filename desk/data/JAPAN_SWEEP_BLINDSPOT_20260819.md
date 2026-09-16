# Japan dislocation coverage is an INFRASTRUCTURE result, not an observation (2026-08-19)

## The question
"Any dislocations to look at here?" — after a Nikkei -3.16% session driven by the AI de-rate
(SoftBank -10.34%, Hitachi -5.24%, Lasertec -4.89%, Disco -4.15%, Tokyo Electron -3.05%).

## The answer for Japan: WE CANNOT SEE. Do not read the silence as "no dislocations".
`intl_dislocation_sweep` carries 1,228 Japanese (.T) names — the third-largest cohort in an 8,131
name universe. Today's run produced **ZERO .T fires**. That looks like a clean negative. It is not.

Yesterday's persisted run (2026-08-18) priced **1,480 of 8,131** and degraded 6,651, of which
**1,040 were .T — 85% of the entire Japanese shelf**. The sweep's own docstring names this exact
failure: "a sweep that priced 300 of 1,200 names and reported a quiet tape is WRONG, and the
failure is INFRASTRUCTURE, not an observation."

## It is NOT a symbol-format problem, and NOT absent data
The degraded .T names are overwhelmingly well-formed 4-digit codes (1,012 of 1,040). Decisive test:
of the 13 Japanese names priced BY HAND in this session, **6 appear in yesterday's "no data"
degraded list** — 5408.T, 6229.T, 6857.T, 7222.T, 7735.T, 8104.T. Same symbols, same source, same
format; they return full history on a single request.

The likely mechanism is THROUGHPUT, not availability: the sweep requests 8,131 symbols, Yahoo rate-
limits, and the failures land in a bucket named `unpriced_no_data`. A direct bulk attempt during
this session returned `YFRateLimitError: Too Many Requests` — the same wall, reached the same way.
So the counter is mislabeled: it reports "Yahoo has no data" for names Yahoo serves fine.

This is the session's recurring disease in infrastructure form — **a number measuring something
other than what it is named after.** `unpriced_no_data` measures OUR request budget, not the data.

## Why it matters now
We HOLD six Japanese positions (3388, 5408, 6229, 7222, 8104, 8750). The screen that would tell us
whether a Japanese name had detached from the Nikkei is blind to ~85% of the shelf, and it reports
that blindness as a quiet tape.

## What IS established for Japan today (hand-checked, not swept)
- The move was uniform beta. Our own six fell -2.06% value-weighted vs the index -3.16%: the four
  deep-value names OUTPERFORMED (-0.4% to -2.2%), having zero AI exposure.
- NO BOJ-path repricing. Bank excess-vs-Nikkei is inconsistent in SIGN across the cohort — Tokio
  Marine +1.40pt today but -5.63pt/21d; Mizuho -1.79pt today but +0.40pt/21d; MUFG -1.19/-1.21;
  SMFG -1.65/-4.12. A genuine policy repricing moves the rate-sensitive cohort together in one
  direction. This is dispersion noise around a beta move, so there is no rate-driven dislocation to
  buy in Japanese financials.
- The one idiosyncratic Japanese move in our book is 6229 Okumura, and it is the 8/14 Q1 print
  (graded separately), not today.

## Fix required before the next Japan answer
1. Rate-limit-aware pricing: batch/throttle/retry with backoff, and a session-level budget.
2. Split the counter — `unpriced_rate_limited` must never be booked as `unpriced_no_data`.
3. Per-shelf coverage floor: if a shelf prices <50% of its names, the sweep must report that shelf
   as UNSCREENED rather than contributing silence to a global "no fires" line.

---

# UPDATE — IBKR tested as the substitute; it CANNOT serve Japan. Yahoo retries can (partly).

## IBKR is connected and still cannot price Japan — an ACCOUNT ENTITLEMENT, not a bug
Tested both paths on the six names we hold:
- **Local gateway** (port 4001 OPEN, contracts qualify, conIds match the positions cache exactly —
  3388->131087833, 5408->14016035, 6229->455186679): every symbol returns
  **`Error 354: Requested market data is not subscribed`**. 6/6 swept, 0 priced.
- **Hosted IBKR API** `get_price_history` on conid 455186679 / TSEJ: **`{"error":"No market data
  permissions"}`**.

So the sweep's gateway fallback ladder can NEVER rescue the Japan shelf on this account. Note the
gateway probe is in any case only a LIVENESS/QUOTE check by design ("cannot give us a 5d/21d move"),
so even with entitlements it would not produce the excess-move the screen needs. Fixing Japan means
fixing the Yahoo path, or buying TSE data.

## The Yahoo path is NOT broken — it is under-retried
`batch_history` already batches (150/call, 0.6s pause). Diagnostic: a 10-name Japanese batch printed
`10 Failed downloads: YFRateLimitError` and then returned **10/10 with full, correct date/close/
volume series** — the retry succeeds and the failure line is first-attempt noise.

Re-run of the FULL 1,228-name Japanese shelf with `retries=3, pause=1.2`:
**415 priced (34%) in 26 seconds**, against yesterday's 188 (15%). More than double the coverage for
~1 extra second per batch. The remaining 66% fail FAST, which is rate limiting, not slow timeouts —
so a longer budget with backoff should recover much more.

## The Japan answer, at 34% coverage and labelled as such
412 usable names (>=22 bars), measured as excess vs a DATE-ALIGNED Nikkei, sweep thresholds
(excess5 <= -8 or excess21 <= -15; HIGH at -12/-20) with the raw-drop guard: **16 fires.**

  HIGH  3133.T -31.1pp/21d | 4316.T -28.0 | 4419.T -21.2 (-19.8%/5d) | 1491.T -13.8pp/5d (Chugai Mining)
  MED   3686.T -19.0 | 4425.T -18.5 | 4179.T -17.6 | 4265.T -17.4 | 4598.T -17.2 | 7271.T -17.1
        2586.T -17.1 | 1812.T -16.7 | 6824.T -15.6 | 4901.T -15.5 | 6254.T -10.9 | 3374.T (see caveat)

**NONE of the sixteen is a name we hold.** Our six are not dislocated — consistent with the
hand-check that they fell -0.4% to -2.2% against an index -3.16%.

**NONE of them is TODAY'S event.** The damage is overwhelmingly 21-day: 3686, 4265, 4598, 7271, 1812
and 4901 are all FLAT-to--3.4% over 5 days while -13% to -17% over 21. These are pre-existing slides
the screen had not surfaced because it could not price them — not products of the AI de-rate.
Today's session was uniform beta, which is why it manufactured no dislocations.

CAVEATS, stated rather than buried: 3374.T is up **+23% over 21 days** and gave back 11.7% in 5 — a
momentum give-back that passed the 5d leg of the raw-drop guard and should be treated as noise, not
a dislocation. Several fires are sub-Y110 microcaps (3133 Y75, 4316 Y79, 3686 Y58, 2586 Y78, 4598
Y105) where an unadjusted corporate action is the likeliest explanation and must be ruled out first.
And 66% of the shelf is still unpriced, so this list is a floor, not an inventory.
