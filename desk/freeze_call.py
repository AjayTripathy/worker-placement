"""freeze_call — the ENFORCED path for freezing predictions (doctrine 2026-07-06).

Born from the Brazil gap: a staged position (BBD) sat under a dated political binary with no
frozen call, no crowd price, no priced-in verdict — because calls were hand-written dicts and
the census was company-print-centric. This helper makes the discipline mechanical:

  from desk.freeze_call import freeze
  freeze(ticker=, cat_date=, our_p=, direction=, catalyst=, reasoning=, plain={...},
         event_type=, frame={"we_believe":.., "market_believes":.., "our_edge":.., "why_priced_in":..},
         px_at_pred=, priced_in="unpriced|partial|full: <dated evidence>")

THE 4-IDEA FRAME (required, standing rule 2026-07-13): every calendar prediction carries all four —
what WE believe, what the MARKET believes, why we might have an EDGE, why it might be PRICED IN.
The gap between belief #1 and #2 IS the trade; #3 and #4 are the bull and bear of that edge.

ENFORCES: (1) event_type in the closed enum (desk/events.py); (2) reasoning + the plain
{what/how/conclusion} block present; (3) for event types with venue_coverage != none, AUTO-
queries the prediction-market mapper — attaches market_p_current + source if a mapping exists,
else records market_p_checked="no venue market <date>" (the check itself is mandatory, the
market optional); (4) political_process/regulatory_decision/nat_cat_season calls REQUIRE the
priced_in field (the tape-decomposition verdict w/ dated evidence — sizing reads it);
(5) appends to the ledger; reminds about the resolution pack if cat_date <= +45d.
Frozen values are never revised — this is the WRITE path only.
"""
from __future__ import annotations
import json, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "desk" / "data" / "calibration_ledger.jsonl"
PRICED_IN_REQUIRED = {"political_process", "regulatory_decision", "nat_cat_season"}
VENUE_SEARCH_REQUIRED = PRICED_IN_REQUIRED  # same classes: always search the venues and RECORD the attempt


FRAME_KEYS = ("we_believe", "market_believes", "our_edge", "why_priced_in")


ANCHOR_TOL = 0.05        # anchor-and-adjust (2026-07-27): max unexplained deviation from an external anchor
NARRATIVE_TYPES = {"peer_read", "political_process"}


def base_effect_flag(prior_growth_pct: float, claimed_growth_pct: float) -> bool:
    """The FR.PA guard: an extreme prior-period base makes 'growth continues at X%' a
    mean-reversion long-shot (the GARP base-effect distortion, ported to predictions).
    Flags when the base ran at >=1.5x the claimed continuation rate — calibrated so the
    canonical miss (FY25 intake +38% vs a claimed +20% continuation = 1.9x) trips it."""
    try:
        return abs(prior_growth_pct) >= 1.5 * abs(claimed_growth_pct) and abs(prior_growth_pct) > 15
    except Exception:
        return False


def freeze(ticker: str, cat_date: str, our_p: float, direction: str, catalyst: str,
           reasoning: str, plain: dict, event_type: str, frame: dict, px_at_pred: float | None = None,
           priced_in: str | None = None, kind: str = "scenario", market_p: float | None = None,
           detectors: list | None = None, mechanism: str | None = None, reaction_driver: str | None = None,
           disconfirm: str | None = None, base_comp: dict | None = None) -> dict:
    from desk.events import EVENT_TYPES, coverage
    assert event_type in EVENT_TYPES, f"event_type '{event_type}' not in the closed enum — extend desk/events.py deliberately or pick the right type"
    assert reasoning and len(reasoning) > 40, "reasoning required (which premises, FOR and AGAINST)"
    assert isinstance(plain, dict) and all(k in plain for k in ("what", "how", "conclusion")), "plain {what,how,conclusion} required"
    assert 0.0 < our_p < 1.0, "our_p must be a probability, not a certainty"
    # THE 4-IDEA FRAME (standing rule 2026-07-13, user directive): every calendar prediction MUST
    # carry all four — what WE believe, what the MARKET believes, why we might have an EDGE, and why
    # it might be PRICED IN. The gap between (1)&(2) is the trade; (3)&(4) are the bull/bear of the edge.
    assert isinstance(frame, dict) and all(frame.get(k) and len(str(frame.get(k))) > 15 for k in FRAME_KEYS), \
        f"frame requires all 4 non-trivial ideas {FRAME_KEYS} — the standing 4-idea rule (we_believe / market_believes / our_edge / why_priced_in)"
    if event_type in PRICED_IN_REQUIRED:
        assert priced_in, f"{event_type} calls REQUIRE priced_in ('unpriced|partial|full: <dated tape evidence>') — the Brazil-gap rule"
    rec = {"ticker": ticker, "cat_date": cat_date, "kind": kind,
           "made": datetime.date.today().isoformat(), "our_p": our_p, "market_p": market_p,
           "event_type": event_type, "status": "OPEN", "resolution": None,
           "px_at_pred": px_at_pred, "direction": direction, "catalyst": catalyst,
           "reasoning": reasoning, "plain": plain, "frame": frame, "detectors": detectors or []}
    if priced_in:
        rec["priced_in"] = priced_in
    # the mandatory crowd check for coverable types
    cov = coverage(event_type)
    if market_p is None and not cov.startswith("none"):
        try:
            from desk.prediction_markets import MAPPINGS, _poly_price
            spec = MAPPINGS.get(f"{ticker}|{cat_date}")
            if spec:
                q = _poly_price(spec["slug_search"], spec.get("prefer_end"))
                if q:
                    rec["market_p_current"] = q["yes_p"]
                    rec["market_p_source"] = f"{spec['venue']}: {q['question']} ({spec['match']})"
            else:
                # ACTIVE SEARCH, not just the curated map — the CMS-2449 lesson (2026-07-07):
                # a passive "no mapping" hid a live, decomposable combo market
                try:
                    from desk.prediction_markets import _poly_price
                    terms = [w for w in (catalyst or "").replace("(", " ").replace(")", " ").split() if len(w) > 4][:4]
                    searched = " ".join(terms[:3]) or ticker
                    hit = _poly_price(searched)
                    if hit:
                        rec["market_p_checked"] = f"no curated mapping; ACTIVE SEARCH '{searched}' found: {hit['question'][:90]} @ {hit['yes_p']} — ADD TO MAPPINGS + decompose before relying"
                    else:
                        rec["market_p_checked"] = f"no venue market found (active search '{searched}' + curated map, {rec['made']})"
                except Exception:
                    rec["market_p_checked"] = f"no venue mapping as of {rec['made']} (coverage class: {cov}); active search unavailable"
        except Exception as e:
            rec["market_p_checked"] = f"mapper unavailable at freeze ({type(e).__name__}) — re-check via market_p_refresh"
    # REACTION-CLASS ANCHOR (2026-07-27, from the Brier-book decomposition): a stock-reaction
    # freeze without a market anchor is scorekeeping that can never feed the sizing gate. If the
    # underlying is US-optionable, stamp the options-implied P(up-by-window-end) at freeze time —
    # the genuine external anchor the n>=20 gate is starved for. Add-only; never overrides a
    # market_p passed by the caller.
    if rec.get("market_p") is None:
        try:
            from desk.implied_binary import is_reaction, implied_up_prob
            if is_reaction(rec):
                we = (datetime.date.fromisoformat(cat_date) + datetime.timedelta(days=7)).isoformat()
                res = implied_up_prob(ticker, we, px_at_pred)
                if res:
                    rec["market_p"] = res["p"]
                    rec["market_p_source"] = (f"{res['source']} | exp {res['expiry']} | "
                                              f"{res['method']} | anchor {res['anchor']}")
                else:
                    rec["market_p_checked"] = (rec.get("market_p_checked") or "") + \
                        " | no usable option chain for the implied-binary anchor at freeze"
        except Exception:
            pass
    # ═══ ANCHOR-AND-ADJUST + CLASS GATES (2026-07-27, from the Brier-book decomposition:
    # ops_data 0.126 / narrative 0.256 / reaction 0.382 — the weak classes froze UNANCHORED numbers) ═══
    if mechanism:
        rec["mechanism"] = mechanism
    # (1) REACTION class: name the driver, attach the context block, defer to the implied anchor
    try:
        from desk.implied_binary import is_reaction, reaction_context
        if is_reaction(rec):
            assert reaction_driver and len(str(reaction_driver)) > 15, \
                "reaction freeze requires reaction_driver — name what the stock will TRADE ON " \
                "(guide/policy/backlog/mix), never 'the quarter' (the HCA-STK lesson)"
            rec["reaction_driver"] = reaction_driver
            ctx = reaction_context(ticker, px_at_pred)
            if ctx:
                rec["reaction_context"] = ctx
            anchor_p = rec.get("market_p")
            if anchor_p is not None and abs(our_p - anchor_p) > ANCHOR_TOL:
                assert mechanism and len(str(mechanism)) > 30, \
                    f"our_p {our_p} deviates >±{ANCHOR_TOL} from the implied anchor {anchor_p} — " \
                    f"anchor-and-adjust: in a class with NO measured skill the anchor is the default; " \
                    f"a deviation needs a named mechanism citing OUR data source (which connector/nowcast " \
                    f"knows something the options market doesn't)"
    except ImportError:
        pass
    # (2) POLITICAL class: the venue price is the prior, same deviation rule
    if event_type == "political_process":
        venue_p = rec.get("market_p") if rec.get("market_p") is not None else rec.get("market_p_current")
        if venue_p is not None and abs(our_p - venue_p) > ANCHOR_TOL:
            assert mechanism and len(str(mechanism)) > 30, \
                f"our_p {our_p} deviates >±{ANCHOR_TOL} from the venue price {venue_p} — politics is " \
                f"the thick-crowd class with no connector advantage (the CIB-0.42 lesson); name the mechanism"
    # (3) NARRATIVE classes at conviction: the Mode-B rule — one documented disconfirming check
    if event_type in NARRATIVE_TYPES and (our_p >= 0.60 or our_p <= 0.40):
        assert disconfirm and len(str(disconfirm)) > 30, \
            "narrative freeze at conviction requires disconfirm — ONE documented primary-source check " \
            "that could have killed the call (the discipline pitch claims get; FR.PA froze 0.65 without one)"
        rec["disconfirm"] = disconfirm
    # (4) BASE-EFFECT guard: growth-continuation claims must carry the comp math
    import re as _re
    claim_text = f"{catalyst} {plain.get('what', '')}"
    if event_type == "peer_read" and _re.search(r"\d+\s*%", claim_text):
        assert isinstance(base_comp, dict) and "prior_growth_pct" in base_comp and "claimed_growth_pct" in base_comp, \
            "peer_read with a %-continuation claim requires base_comp={prior_growth_pct, claimed_growth_pct} — " \
            "the FR.PA guard (froze 'intake +20% continues' at 0.65 against a +38%/+47% base)"
        rec["base_comp"] = base_comp
        if base_effect_flag(base_comp["prior_growth_pct"], base_comp["claimed_growth_pct"]) and our_p > 0.55:
            assert mechanism and len(str(mechanism)) > 30, \
                f"BASE-EFFECT FLAG: prior {base_comp['prior_growth_pct']}% >= 2x the claimed " \
                f"{base_comp['claimed_growth_pct']}% — extreme bases mean-revert; our_p {our_p} > 0.55 " \
                f"needs a mechanism or a haircut toward the coin"
    with LEDGER.open("a") as f:
        f.write("\n" + json.dumps(rec))
    days = None
    try:
        days = (datetime.date.fromisoformat(cat_date) - datetime.date.today()).days
    except Exception:
        pass
    if days is not None and days <= 45:
        print(f"[freeze_call] {ticker} {cat_date} frozen at {our_p} — cat_date is {days}d out: WRITE THE RESOLUTION PACK NOW (packs guard will flag at 30d)")
    else:
        print(f"[freeze_call] {ticker} {cat_date} frozen at {our_p}")
    return rec
