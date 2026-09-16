"""options_positioning — INSTITUTIONAL-crowding connector via IBKR/TWS (Conditioning Layer, Phase 2).

THE GOAL (do not lose it): the Phase-1 layer caught RETAIL crowding (StockTwits/Trends/FTD/SI) but is
BLIND to INSTITUTIONAL crowding. The options tape is the single most direct read on whether the STREET
has already priced a risk: when a name's downside is being insured, the put side gets bid, IV rises,
and the 25-delta risk-reversal (put IV - call IV) goes positive/steep. That is the institutional
"fear/crowding signature." A flat skew + thin open interest = the risk is NOT yet priced.

This systematizes the SPCX-by-hand skew work:
  reqSecDefOptParams -> expirations+strikes -> pick nearest monthly ~30d out -> build the option chain
  around spot -> reqTickers(modelGreeks) -> read per-strike IV/delta/OI -> interpolate the 25-delta
  put and 25-delta call -> risk_reversal_25d = IV(25d put) - IV(25d call). Plus ATM IV and total
  put/call OI.

WHAT WE RETURN (per ticker):
  - atm_iv                : at-the-money implied vol (the level — how much move is priced)
  - rr_25d                : 25-delta risk reversal, put IV - call IV, in vol points (the SHAPE / fear)
  - put_oi_total / call_oi_total / pc_oi_ratio : open-interest crowding by side
  - elevated_put_skew     : bool — RR >= _RR_ELEVATED (downside already insured)
  - high_oi               : bool — total OI on the sampled expiry clears a liquidity/crowding floor
  - options_priced_risk   : bool — elevated_put_skew AND high_oi == the risk is institutionally priced
  - spot, expiry, n_strikes_used, source diagnostics

HONESTY / DEGRADATION:
  - TWS not running (port 7496 refused), API not enabled, no option chain, or no greeks returned
    => the whole connector returns success=False with a typed error. NEVER fabricate IV/OI.
  - Greeks come from IBKR's model (modelGreeks); on illiquid strikes IBKR returns NaN — those strikes
    are DROPPED, not imputed. If too few valid strikes survive to bracket 25-delta, rr_25d is None and
    we say so.
  - clientId default 145 (distinct from the muni 17/87/91/143 and the user's 71/72/143 options ids).
  - Lag: options tape is ~live during RTH; quote may be delayed/last-close after hours. Surfaced.

Inputs: entity_name = TICKER. extra={'asof','host','port','client_id','target_dte','exchange'}.
asof is informational only — IBKR serves the LIVE chain (you cannot reqTickers a historical greek
snapshot from TWS), so if asof != today we flag the read as live-not-asof and let discovery_state
down-weight. We do not pretend to point-in-time the options tape.
"""

from __future__ import annotations

# Knowledge-graph dispatch contract (see knowledge_graph/dispatch.py) — added 2026-07-29 gap-close.
APPLIES_TO = {
    "kind": 'm_source',
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": [],
    "asset_classes": ['public_equity', 'corporate_ipo_dd'],
    "applies_universally": True,
    "summary": 'Options OI/IV crowding via IBKR. Any optionable public ticker.',
}

import math
from datetime import datetime, timezone, date
from typing import Any, Optional

from .base import BaseConnector, ConnectorObservation, ConnectorRequest, ConnectorResult, ErrorKind

_HOST = "127.0.0.1"
_PORT = 7496           # live TWS (paper = 7497)
_CLIENT_ID = 145       # distinct from 17/71/72/87/91/143
_TARGET_DTE = 30       # aim for the nearest monthly ~30 days out
_EXCHANGE = "SMART"

# Crowding thresholds (vol points / share counts). Conservative, documented, tunable.
_RR_ELEVATED = 3.0          # 25d RR >= +3 vol points == downside being actively insured (put skew)
_OI_HIGH_TOTAL = 50_000     # >=50k contracts of OI on ONE sampled monthly == institutionally deep
_DELTA_TARGET = 0.25        # the 25-delta wings


def _nan(x) -> bool:
    try:
        return x is None or math.isnan(float(x))
    except (TypeError, ValueError):
        return True


def _interp_iv_at_delta(points: list[tuple[float, float]], target_abs_delta: float) -> Optional[float]:
    """points = list of (abs_delta, iv). Linearly interpolate IV at target_abs_delta.
    Returns None if the target can't be bracketed by valid points."""
    pts = sorted((d, iv) for d, iv in points if not _nan(d) and not _nan(iv) and 0 < d < 1)
    if len(pts) < 2:
        return None
    # exact / out-of-range handling
    if target_abs_delta <= pts[0][0]:
        return pts[0][1]
    if target_abs_delta >= pts[-1][0]:
        return pts[-1][1]
    for (d0, iv0), (d1, iv1) in zip(pts, pts[1:]):
        if d0 <= target_abs_delta <= d1:
            if d1 == d0:
                return iv0
            w = (target_abs_delta - d0) / (d1 - d0)
            return iv0 + w * (iv1 - iv0)
    return None


class OptionsPositioningConnector(BaseConnector):
    source_id = "options_positioning"
    rate_limit_per_min = 30
    user_agent = "SignalOS-BuysideDD/0.1 conditioning-layer options"

    def query(self, request: ConnectorRequest) -> ConnectorResult:
        sym = (request.entity_name or "").strip().upper()
        if not sym:
            return self._fail(request, ErrorKind.UNSUPPORTED, "entity_name (ticker) required")
        try:
            from ib_insync import IB, Stock, Option
        except Exception as e:  # noqa: BLE001
            return self._fail(request, ErrorKind.UNSUPPORTED, f"ib_insync not importable: {e}")

        ex = request.extra or {}

        # ── MCP underlying-level fallback ─────────────────────────────────────
        # The per-strike 25-delta skew needs the TWS API socket. When that socket is down (busy/
        # locked TWS), the IBKR MCP get_price_snapshot still serves UNDERLYING-LEVEL option data
        # (annual IV, IV-percentile-of-52wk, total option call/put volume, historical vol). That is
        # a real, live institutional read — coarser than the per-strike RR, but NOT fabricated. The
        # caller (discovery_state / a tool-equipped agent) pulls it from MCP and injects it here so
        # it flows through this same connector contract, clearly labelled underlying_level=True and
        # rr_25d=None (skew UNAVAILABLE). We never synthesize a skew we didn't measure.
        if ex.get("mcp_underlying"):
            return self._from_mcp_underlying(request, sym, ex["mcp_underlying"], ex.get("asof"))

        host = ex.get("host", _HOST)
        port = int(ex.get("port", _PORT))
        client_id = int(ex.get("client_id", _CLIENT_ID))
        target_dte = int(ex.get("target_dte", _TARGET_DTE))
        exchange = ex.get("exchange", _EXCHANGE)
        asof = ex.get("asof")

        # ib_insync needs an asyncio loop in this thread; create one if absent.
        try:
            import asyncio
            try:
                asyncio.get_event_loop()
            except RuntimeError:
                asyncio.set_event_loop(asyncio.new_event_loop())
        except Exception:  # noqa: BLE001
            pass

        ib = IB()
        # IMPORTANT: ib_insync's high-level IB.connect() runs a startup SYNC (reqExecutions +
        # account/positions updates) that HANGS on a busy/locked TWS session even though the API
        # socket itself is healthy (observed live 2026-06-24: handshake completes, managedAccounts
        # returns, then reqExecutionsAsync times out and TWS drops the socket). We therefore connect
        # via the LOW-LEVEL client.connectAsync, which performs only the handshake and skips the
        # account sync we don't need for an options-chain read.
        try:
            from ib_insync import util
            util.run(ib.client.connectAsync(host, port, clientId=client_id))
        except Exception as e:  # noqa: BLE001
            return self._fail(request, ErrorKind.NETWORK,
                              f"TWS connect failed at {host}:{port} cid={client_id} ({e}). "
                              f"Is TWS open with API enabled (live 7496 / paper 7497)? "
                              f"-> options channel UNAVAILABLE (degraded, not fabricated)")
        # give the handshake a beat; if TWS is going to drop us it does so within ~3s
        ib.sleep(1.0)
        if not ib.client.isConnected():
            return self._fail(request, ErrorKind.NETWORK,
                              f"TWS dropped the API socket right after handshake (cid={client_id}); "
                              f"likely a TWS-side session lock / 'Accept connection?' dialog / master "
                              f"client-id restriction -> options channel UNAVAILABLE (degraded)")
        try:
            return self._do_query(ib, request, sym, exchange, target_dte, asof)
        except Exception as e:  # noqa: BLE001
            return self._fail(request, ErrorKind.UNKNOWN, f"options query raised: {e}")
        finally:
            try:
                ib.disconnect()
            except Exception:  # noqa: BLE001
                pass

    def _from_mcp_underlying(self, request, sym, m: dict, asof) -> ConnectorResult:
        """Build the connector result from an IBKR-MCP underlying-level snapshot.

        Expected (any subset) of MCP get_price_snapshot fields, passed as a flat dict:
          last_price, annual_iv (fraction), hist_vol_annual (fraction),
          iv_pctile_52w (0-1, IV-percentile-of-52wk-range), call_volume, put_volume,
          avg_call_volume, avg_put_volume, ytd_change_pct, low_52w, high_52w.
        This is UNDERLYING-LEVEL: it gives the IV *level* and an IV-percentile crowding read, plus
        an option-volume read — but NOT a per-strike 25-delta skew. rr_25d is None and flagged.
        """
        src = "IBKR/MCP get_price_snapshot (underlying-level option data)"
        spot = m.get("last_price")
        annual_iv = m.get("annual_iv")
        hist_vol = m.get("hist_vol_annual")
        iv_pctile = m.get("iv_pctile_52w")          # 0..1 within the 52-week IV range
        call_vol, put_vol = m.get("call_volume"), m.get("put_volume")
        avg_call, avg_put = m.get("avg_call_volume"), m.get("avg_put_volume")

        atm_iv_pct = round(annual_iv * 100, 2) if annual_iv is not None else None
        hv_pct = round(hist_vol * 100, 2) if hist_vol is not None else None
        iv_hv = round(annual_iv / hist_vol, 3) if (annual_iv and hist_vol) else None

        # total option volume today (a coarse OI-stand-in: this feed serves volume, not chain OI)
        total_opt_vol = None
        if call_vol is not None or put_vol is not None:
            total_opt_vol = (call_vol or 0) + (put_vol or 0)
        avg_opt_vol = None
        if avg_call is not None or avg_put is not None:
            avg_opt_vol = (avg_call or 0) + (avg_put or 0)
        vol_vs_avg = round(total_opt_vol / avg_opt_vol, 2) if (total_opt_vol and avg_opt_vol) else None
        pc_vol = round(put_vol / call_vol, 3) if (put_vol is not None and call_vol) else None

        # Crowding read at the UNDERLYING level (no per-strike skew available):
        #  - elevated IV regime  = IV percentile-of-52wk high AND IV >= HV (vol bid up, not decaying)
        #  - high option activity = today's option volume running hot vs its average
        elevated_iv_regime = bool(iv_pctile is not None and iv_pctile >= 0.70
                                  and iv_hv is not None and iv_hv >= 1.0)
        high_option_activity = bool(vol_vs_avg is not None and vol_vs_avg >= 1.5)
        # options_priced_risk requires BOTH the vol being bid AND activity — neither alone clears it.
        options_priced_risk = bool(elevated_iv_regime and high_option_activity)

        today_iso = date.today().isoformat()
        live_not_asof = bool(asof and str(asof)[:10] != today_iso)

        obs = [
            ConnectorObservation(attribute="spot", value=spot, source_url=src),
            ConnectorObservation(attribute="atm_iv_pct", value=atm_iv_pct, source_url=src,
                                 extra={"note": "underlying annual IV (level), not a per-strike ATM read"}),
            ConnectorObservation(attribute="hist_vol_pct", value=hv_pct, source_url=src),
            ConnectorObservation(attribute="iv_over_hv", value=iv_hv, source_url=src,
                                 extra={"interp": "<1 = IV BELOW realized (vol decaying, fear fading); "
                                                  ">1 = IV bid above realized (fear premium)"}),
            ConnectorObservation(attribute="iv_pctile_52w", value=iv_pctile, source_url=src,
                                 extra={"interp": "where current IV sits in its own 52-week range (0-1)"}),
            ConnectorObservation(attribute="rr_25d_vol_pts", value=None, source_url=src,
                                 extra={"status": "UNAVAILABLE", "reason": "per-strike 25-delta skew needs "
                                        "the TWS API socket (down at read time); underlying-level feed has "
                                        "no per-strike greeks. NOT fabricated."}),
            ConnectorObservation(attribute="total_option_volume", value=total_opt_vol, source_url=src,
                                 extra={"call_volume": call_vol, "put_volume": put_vol,
                                        "note": "OI not available on this feed; today's option VOLUME used"}),
            ConnectorObservation(attribute="option_volume_vs_avg", value=vol_vs_avg, source_url=src),
            ConnectorObservation(attribute="pc_volume_ratio", value=pc_vol, source_url=src),
            ConnectorObservation(attribute="elevated_iv_regime", value=elevated_iv_regime, source_url=src,
                                 extra={"rule": "iv_pctile_52w>=0.70 AND iv_over_hv>=1.0"}),
            ConnectorObservation(attribute="high_option_activity", value=high_option_activity, source_url=src,
                                 extra={"rule": "option_volume_vs_avg>=1.5"}),
            ConnectorObservation(attribute="options_priced_risk", value=options_priced_risk, source_url=src,
                                 extra={"definition": "elevated_iv_regime AND high_option_activity "
                                        "(underlying-level proxy for the per-strike priced-risk flag)"}),
            ConnectorObservation(attribute="underlying_level", value=True, source_url=src,
                                 extra={"note": "coarse underlying-level read; per-strike skew degraded"}),
            ConnectorObservation(attribute="live_not_asof", value=live_not_asof, source_url=src,
                                 extra={"asof_requested": asof, "tape_date": today_iso}),
        ]
        return self._ok(request, obs, raw=str(m)[:2048])

    def _do_query(self, ib, request, sym, exchange, target_dte, asof) -> ConnectorResult:
        from ib_insync import Stock, Option

        # 1) qualify the underlying + get a spot
        stk = Stock(sym, "SMART", "USD")
        q = ib.qualifyContracts(stk)
        if not q:
            return self._fail(request, ErrorKind.NOT_FOUND, f"could not qualify stock {sym}")
        stk = q[0]
        tick = ib.reqMktData(stk, "", False, False)
        ib.sleep(2.0)
        spot = None
        for cand in (tick.marketPrice(), tick.last, tick.close):
            if not _nan(cand):
                spot = float(cand)
                break
        if spot is None:
            return self._fail(request, ErrorKind.NOT_FOUND,
                              f"no spot for {sym} (market closed + no last/close)")

        # 2) option params: expirations + strikes
        params = ib.reqSecDefOptParams(stk.symbol, "", stk.secType, stk.conId)
        chain = next((p for p in params if p.exchange == "SMART"), params[0] if params else None)
        if not chain or not chain.expirations or not chain.strikes:
            return self._fail(request, ErrorKind.NOT_FOUND, f"no option chain for {sym}")

        # nearest monthly expiry >= target_dte/2 out, preferring ~target_dte
        today = date.today()
        exps = sorted(chain.expirations)
        def _dte(e: str) -> int:
            try:
                return (datetime.strptime(e, "%Y%m%d").date() - today).days
            except ValueError:
                return 9999
        future = [(e, _dte(e)) for e in exps if _dte(e) >= 3]
        if not future:
            return self._fail(request, ErrorKind.NOT_FOUND, f"no future expirations for {sym}")
        expiry = min(future, key=lambda t: abs(t[1] - target_dte))[0]
        chosen_dte = _dte(expiry)

        # strikes within +/-25% of spot (covers both 25-delta wings comfortably)
        strikes = sorted(s for s in chain.strikes if 0.75 * spot <= s <= 1.25 * spot)
        if len(strikes) < 4:
            # widen if the chain is sparse
            strikes = sorted(s for s in chain.strikes if 0.6 * spot <= s <= 1.4 * spot)
        if len(strikes) < 2:
            return self._fail(request, ErrorKind.NOT_FOUND, f"too few strikes near spot for {sym}")

        # 3) build calls + puts, request greeks + OI
        opts = []
        for right in ("C", "P"):
            for k in strikes:
                opts.append(Option(sym, expiry, k, right, exchange, tradingClass=chain.tradingClass or sym))
        opts = ib.qualifyContracts(*opts)
        if not opts:
            return self._fail(request, ErrorKind.NOT_FOUND, f"no qualified option contracts for {sym}")

        # genericTick 101 = option OI (call/put OI fields)
        tickers = ib.reqTickers(*opts) if False else None  # reqTickers doesn't carry OI; use reqMktData
        rows = []
        mds = []
        for o in opts:
            md = ib.reqMktData(o, "101,106", False, False)  # 101=OI, 106=impl vol
            mds.append((o, md))
        ib.sleep(4.0)  # let greeks + OI populate

        for o, md in mds:
            mg = md.modelGreeks
            iv = mg.impliedVol if mg and not _nan(mg.impliedVol) else None
            delta = mg.delta if mg and not _nan(mg.delta) else None
            # OI: callOpenInterest / putOpenInterest depending on right
            oi = None
            if o.right == "C":
                oi = getattr(md, "callOpenInterest", None)
            else:
                oi = getattr(md, "putOpenInterest", None)
            if _nan(oi):
                oi = None
            rows.append({"right": o.right, "strike": float(o.strike), "iv": iv,
                         "delta": delta, "oi": oi})
            try:
                ib.cancelMktData(o)
            except Exception:  # noqa: BLE001
                pass

        calls = [r for r in rows if r["right"] == "C"]
        puts = [r for r in rows if r["right"] == "P"]

        # 4) ATM IV (strike nearest spot, average call+put IV where present)
        def _atm_iv(side):
            valid = [r for r in side if r["iv"] is not None]
            if not valid:
                return None
            return min(valid, key=lambda r: abs(r["strike"] - spot))["iv"]
        atm_c, atm_p = _atm_iv(calls), _atm_iv(puts)
        atm_iv = None
        if atm_c is not None and atm_p is not None:
            atm_iv = (atm_c + atm_p) / 2.0
        else:
            atm_iv = atm_c if atm_c is not None else atm_p

        # 5) 25-delta risk reversal: IV at 25d put - IV at 25d call
        call_pts = [(abs(r["delta"]), r["iv"]) for r in calls if r["delta"] is not None and r["iv"] is not None]
        put_pts = [(abs(r["delta"]), r["iv"]) for r in puts if r["delta"] is not None and r["iv"] is not None]
        iv_25c = _interp_iv_at_delta(call_pts, _DELTA_TARGET)
        iv_25p = _interp_iv_at_delta(put_pts, _DELTA_TARGET)
        rr_25d = None
        if iv_25c is not None and iv_25p is not None:
            rr_25d = (iv_25p - iv_25c)  # in vol fraction; convert to points below

        # 6) OI totals
        put_oi = sum(r["oi"] for r in puts if r["oi"] is not None) or None
        call_oi = sum(r["oi"] for r in calls if r["oi"] is not None) or None
        total_oi = (put_oi or 0) + (call_oi or 0)
        pc_oi = None
        if put_oi is not None and call_oi:
            pc_oi = round(put_oi / call_oi, 3)

        # convert IV fractions -> percent points for human-readable output + thresholds
        def _pct(x):
            return round(x * 100, 2) if x is not None else None
        atm_iv_pct = _pct(atm_iv)
        rr_25d_pts = _pct(rr_25d)
        iv_25c_pct = _pct(iv_25c)
        iv_25p_pct = _pct(iv_25p)

        elevated_put_skew = (rr_25d_pts is not None and rr_25d_pts >= _RR_ELEVATED)
        high_oi = total_oi >= _OI_HIGH_TOTAL
        options_priced_risk = bool(elevated_put_skew and high_oi)

        n_valid_greeks = sum(1 for r in rows if r["iv"] is not None and r["delta"] is not None)

        # asof honesty: TWS only serves the LIVE chain
        today_iso = date.today().isoformat()
        live_not_asof = bool(asof and str(asof)[:10] != today_iso)

        src = "IBKR/TWS reqSecDefOptParams+reqMktData(modelGreeks,OI)"
        obs = [
            ConnectorObservation(attribute="spot", value=round(spot, 4), source_url=src),
            ConnectorObservation(attribute="expiry", value=expiry, source_url=src,
                                 extra={"dte": chosen_dte, "target_dte": target_dte}),
            ConnectorObservation(attribute="atm_iv_pct", value=atm_iv_pct, source_url=src,
                                 extra={"call_atm_iv_pct": _pct(atm_c), "put_atm_iv_pct": _pct(atm_p)}),
            ConnectorObservation(attribute="rr_25d_vol_pts", value=rr_25d_pts, source_url=src,
                                 extra={"iv_25d_put_pct": iv_25p_pct, "iv_25d_call_pct": iv_25c_pct,
                                        "definition": "IV(25d put) - IV(25d call); >0 = put skew = downside insured",
                                        "n_call_delta_pts": len(call_pts), "n_put_delta_pts": len(put_pts)}),
            ConnectorObservation(attribute="put_oi_total", value=put_oi, source_url=src),
            ConnectorObservation(attribute="call_oi_total", value=call_oi, source_url=src),
            ConnectorObservation(attribute="total_oi", value=total_oi, source_url=src),
            ConnectorObservation(attribute="pc_oi_ratio", value=pc_oi, source_url=src),
            ConnectorObservation(attribute="elevated_put_skew", value=elevated_put_skew, source_url=src,
                                 extra={"rr_threshold_pts": _RR_ELEVATED}),
            ConnectorObservation(attribute="high_oi", value=high_oi, source_url=src,
                                 extra={"oi_threshold": _OI_HIGH_TOTAL}),
            ConnectorObservation(attribute="options_priced_risk", value=options_priced_risk, source_url=src,
                                 extra={"definition": "elevated_put_skew AND high_oi == street has priced the risk"}),
            ConnectorObservation(attribute="n_valid_greeks", value=n_valid_greeks, source_url=src,
                                 extra={"n_strikes_sampled": len(strikes), "n_contracts": len(rows)}),
            ConnectorObservation(attribute="live_not_asof", value=live_not_asof, source_url=src,
                                 extra={"note": "TWS serves the LIVE chain only; cannot point-in-time historical greeks",
                                        "asof_requested": asof, "tape_date": today_iso}),
        ]
        return self._ok(request, obs, raw=str(rows[:8])[:2048])


if __name__ == "__main__":
    import sys
    t = sys.argv[1] if len(sys.argv) > 1 else "PODD"
    res = OptionsPositioningConnector().query(ConnectorRequest(entity_name=t))
    if not res.success:
        print(f"{t}: UNAVAILABLE err={res.error_kind} :: {res.error_detail}")
    else:
        d = {o.attribute: o.value for o in res.observations}
        print(f"{t}: spot={d['spot']} exp={d['expiry']} ATM_IV={d['atm_iv_pct']}% "
              f"RR25={d['rr_25d_vol_pts']}pts putOI={d['put_oi_total']} callOI={d['call_oi_total']} "
              f"P/C={d['pc_oi_ratio']} priced_risk={d['options_priced_risk']}")
