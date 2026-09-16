"""thirteenf_diff — INSTITUTIONAL-positioning connector via EDGAR 13F (Conditioning Layer, Phase 2).

THE GOAL (do not lose it): the QoQ change in institutional ownership is the smart-money positioning
read — institutions PILING IN (more 13F filers holding, more shares) vs TRIMMING (fewer) tells you
whether the institutional base is crowding into or exiting a name. Combined with the options skew and
analyst density, it completes the institutional-crowding half of the gauge.

FEASIBILITY — HONEST (this is the fiddly one):
  A TRUE aggregate "% of shares held by 13F filers, this quarter vs last" requires parsing the
  INFORMATION TABLE of EVERY 13F-HR that holds the CUSIP (10k+ for a widely-held name) and summing
  sshPrnamt — NOT tractable in a single free-EDGAR pass. So we split the signal into two tiers:

  TIER 1 — VERIFIED (exact, cheap, the load-bearing signal):
    The COUNT of distinct 13F-HR filings reporting the CUSIP, quarter-over-quarter, via EDGAR
    full-text search (efts.sec.gov, free). This is the breadth of institutional ownership and its QoQ
    change. The count is exact (search 'total.relation' == 'eq'). A FALLING filer count = institutions
    EXITING (positioning_trim); RISING = institutions ADDING. This alone discriminates discovered
    (hundreds of holders) from undiscovered (single-digit holders).

  TIER 2 — UNVERIFIABLE / best-effort (sampled, flagged):
    Aggregate SHARE count from a SAMPLE of the most recent info-table filings (bounded N). We sum the
    sampled holders' shares and report it EXPLICITLY as a sample (sampled_filers / total_filers), and
    we DO NOT extrapolate it to a universe total. Flagged share_aggregate_status='UNVERIFIABLE
    (sampled subset, not full universe)'. We never fabricate a full-universe share number.

WHAT WE RETURN:
  - n_filers_current / n_filers_prior / n_filers_change / n_filers_change_pct : TIER-1 verified breadth
  - institutional_breadth : 'BROAD' (>=200) | 'MODERATE' (25-199) | 'NARROW' (1-24) | 'NONE'
  - positioning_direction : 'INSTITUTIONS_ADDING' | 'INSTITUTIONS_TRIMMING' | 'STABLE'
  - sampled_shares / sampled_filers : TIER-2 best-effort, flagged UNVERIFIABLE
  - cusip, windows used, lags

LAG: 13F-HR is filed up to 45 days after quarter-end, so the latest complete quarter is 45-135 days
stale vs asof. Windows are picked relative to asof and surfaced; never backfilled.

Inputs: entity_name = TICKER; extra={'cusip': '45784P101'} (REQUIRED — FTS keys on the security
CUSIP, which we cannot reliably derive from a ticker for free; caller supplies it). extra={'asof'}
to pick the two reporting windows; extra={'sample_n'} (default 0 = skip Tier-2) to enable the
sampled share aggregate.
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
    "summary": '13F institutional position deltas. Any public ticker.',
}

from datetime import datetime, timezone, date, timedelta
from typing import Any, Optional

from .base import BaseConnector, ConnectorObservation, ConnectorRequest, ConnectorResult, ErrorKind

_FTS = "https://efts.sec.gov/LATEST/search-index"
_UA = "SignalOS-BuysideDD research 4tripathy@gmail.com"
_BROAD = 200
_MODERATE = 25


def _q_filing_window(ref: date) -> tuple[str, str, str]:
    """Given a reference date, return (label, startdt, enddt) for the 13F-HR FILING window of the
    most recent reporting quarter whose 45-day filing deadline has passed on/before ref.

    13F-HR for quarter ending Q is due 45 days after Q-end; the bulk file in the ~5-week window after
    Q-end+15d. We bracket each quarter's filing window as [Qend+15d, Qend+50d]."""
    # quarter ends
    qends = [date(ref.year, 3, 31), date(ref.year, 6, 30), date(ref.year, 9, 30), date(ref.year, 12, 31),
             date(ref.year - 1, 12, 31), date(ref.year - 1, 9, 30)]
    qends = sorted(set(qends))
    # the most recent quarter whose filing deadline (Qend+45) <= ref
    eligible = [qe for qe in qends if qe + timedelta(days=45) <= ref]
    if not eligible:
        eligible = [min(qends)]
    qe = max(eligible)
    start = qe + timedelta(days=15)
    end = qe + timedelta(days=50)
    return (f"Q-ending-{qe.isoformat()}", start.isoformat(), end.isoformat())


def _prev_quarter_window(ref: date) -> tuple[str, str, str]:
    # step the reference back ~95 days to land in the previous quarter's filing window
    return _q_filing_window(ref - timedelta(days=95))


class ThirteenFDiffConnector(BaseConnector):
    source_id = "thirteenf_diff"
    rate_limit_per_min = 20
    user_agent = _UA

    def query(self, request: ConnectorRequest) -> ConnectorResult:
        sym = (request.entity_name or "").strip().upper()
        ex = request.extra or {}
        cusip = (ex.get("cusip") or "").strip().upper()
        if not cusip:
            return self._fail(request, ErrorKind.UNSUPPORTED,
                              "13F diff requires extra={'cusip': ...} (FTS keys on the security CUSIP; "
                              "deriving CUSIP from a ticker for free is unreliable). UNVERIFIABLE without it.")
        try:
            asof_dt = datetime.fromisoformat(str(ex.get("asof"))).date() if ex.get("asof") else date.today()
        except ValueError:
            asof_dt = date.today()

        cur_label, cur_s, cur_e = _q_filing_window(asof_dt)
        prv_label, prv_s, prv_e = _prev_quarter_window(asof_dt)

        sess = self._session()
        sess.headers.update({"User-Agent": _UA})

        def _count(start: str, end: str) -> tuple[Optional[int], Optional[str]]:
            url = (f"{_FTS}?q=%22{cusip}%22&forms=13F-HR&dateRange=custom"
                   f"&startdt={start}&enddt={end}")
            self._throttle()
            try:
                r = sess.get(url, timeout=self.timeout_s)
            except Exception as e:  # noqa: BLE001
                return None, f"network: {e}"
            if r.status_code == 429:
                return None, "FTS 429"
            if r.status_code >= 400:
                return None, f"http {r.status_code}"
            try:
                j = r.json()
                tot = j["hits"]["total"]
                return int(tot["value"]), tot.get("relation")
            except Exception as e:  # noqa: BLE001
                return None, f"parse: {e}"

        n_cur, rel_cur = _count(cur_s, cur_e)
        n_prv, rel_prv = _count(prv_s, prv_e)
        if n_cur is None and n_prv is None:
            return self._fail(request, ErrorKind.NETWORK,
                              f"EDGAR FTS unreachable for CUSIP {cusip} ({rel_cur} / {rel_prv})")

        change = (n_cur - n_prv) if (n_cur is not None and n_prv is not None) else None
        change_pct = (round(100.0 * change / n_prv, 1) if (change is not None and n_prv) else None)

        breadth = "NONE"
        if n_cur is not None:
            breadth = ("BROAD" if n_cur >= _BROAD else "MODERATE" if n_cur >= _MODERATE
                       else "NARROW" if n_cur >= 1 else "NONE")
        direction = None
        if change_pct is not None:
            direction = ("INSTITUTIONS_ADDING" if change_pct > 3 else
                         "INSTITUTIONS_TRIMMING" if change_pct < -3 else "STABLE")

        # Tier-2 sampled share aggregate (optional; explicitly UNVERIFIABLE as a universe total)
        sampled_shares = None
        sampled_filers = None
        sample_status = "skipped (extra.sample_n=0)"
        sample_n = int(ex.get("sample_n", 0))
        if sample_n > 0:
            sampled_shares, sampled_filers, sample_status = self._sample_shares(sess, cusip, cur_s, cur_e, sample_n)

        # exactness caveat: FTS 'gte' relation means the count is a floor (capped at 10000)
        exact_caveat = []
        if rel_cur and rel_cur != "eq":
            exact_caveat.append(f"current count is a FLOOR (FTS relation={rel_cur}, capped ~10k)")
        if rel_prv and rel_prv != "eq":
            exact_caveat.append(f"prior count is a FLOOR (FTS relation={rel_prv})")

        src = "EDGAR full-text search (efts.sec.gov) over 13F-HR info tables"
        obs = [
            ConnectorObservation(attribute="cusip", value=cusip, source_url=src),
            ConnectorObservation(attribute="n_filers_current", value=n_cur, source_url=src,
                                 extra={"window": cur_label, "filed_between": [cur_s, cur_e], "relation": rel_cur}),
            ConnectorObservation(attribute="n_filers_prior", value=n_prv, source_url=src,
                                 extra={"window": prv_label, "filed_between": [prv_s, prv_e], "relation": rel_prv}),
            ConnectorObservation(attribute="n_filers_change", value=change, source_url=src),
            ConnectorObservation(attribute="n_filers_change_pct", value=change_pct, source_url=src),
            ConnectorObservation(attribute="institutional_breadth", value=breadth, source_url=src,
                                 extra={"thresholds": {"BROAD": _BROAD, "MODERATE": _MODERATE}}),
            ConnectorObservation(attribute="positioning_direction", value=direction, source_url=src,
                                 extra={"rule": "filer-count QoQ: >+3% adding / <-3% trimming / else stable",
                                        "tier": "VERIFIED (exact filer count)"}),
            ConnectorObservation(attribute="sampled_shares", value=sampled_shares, source_url=src,
                                 extra={"sampled_filers": sampled_filers, "status": sample_status,
                                        "share_aggregate_status": "UNVERIFIABLE (sampled subset, NOT full "
                                        "universe; do not extrapolate)"}),
            ConnectorObservation(attribute="exactness_caveat", value=exact_caveat or None, source_url=src),
            ConnectorObservation(attribute="lag_note", value="13F-HR filed up to 45d after quarter-end; "
                                 "latest complete quarter is ~45-135d stale vs asof (surfaced, not backfilled)",
                                 source_url=src),
        ]
        return self._ok(request, obs, raw=f"cur={n_cur}({rel_cur}) prv={n_prv}({rel_prv})")

    def _sample_shares(self, sess, cusip, start, end, sample_n):
        """Best-effort Tier-2: pull up to sample_n recent 13F-HR docs, parse the info-table XML for
        this CUSIP, sum sshPrnamt. EXPLICITLY a sample — returned flagged UNVERIFIABLE."""
        import re
        url = (f"{_FTS}?q=%22{cusip}%22&forms=13F-HR&dateRange=custom"
               f"&startdt={start}&enddt={end}&from=0")
        try:
            self._throttle()
            j = sess.get(url, timeout=self.timeout_s).json()
            hits = j["hits"]["hits"][:sample_n]
        except Exception as e:  # noqa: BLE001
            return None, None, f"sample fetch failed: {e}"
        total = 0
        used = 0
        for h in hits:
            try:
                _id = h["_id"]                      # 'accession:filename'
                acc, _, fname = _id.partition(":")
                cik = h["_source"].get("ciks", [None])[0]
                if not cik:
                    continue
                acc_nodash = acc.replace("-", "")
                doc_url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc_nodash}/{fname}"
                self._throttle()
                txt = sess.get(doc_url, timeout=self.timeout_s).text
                # info-table rows: find the block(s) matching the CUSIP, grab the sshPrnamt
                # (handles namespaced + non-namespaced tags)
                blocks = re.split(r"(?i)</?infoTable>", txt)
                for b in blocks:
                    if cusip in b.upper():
                        m = re.search(r"(?i)<(?:\w+:)?sshPrnamt>\s*([\d,]+)\s*</", b)
                        if m:
                            total += int(m.group(1).replace(",", ""))
                            used += 1
            except Exception:  # noqa: BLE001
                continue
        if used == 0:
            return None, 0, "sampled but parsed 0 info-table rows (XML shape varied)"
        return total, used, f"SAMPLED {used} of {len(hits)} fetched filings (UNVERIFIABLE as universe total)"


if __name__ == "__main__":
    import sys
    t = sys.argv[1] if len(sys.argv) > 1 else "PODD"
    cu = sys.argv[2] if len(sys.argv) > 2 else "45784P101"
    res = ThirteenFDiffConnector().query(ConnectorRequest(entity_name=t, extra={"cusip": cu, "asof": "2026-06-24"}))
    if not res.success:
        print(f"{t}: FAIL {res.error_kind} {res.error_detail}")
    else:
        d = {o.attribute: o.value for o in res.observations}
        print(f"{t} ({cu}): filers {d['n_filers_prior']} -> {d['n_filers_current']} "
              f"({d['n_filers_change_pct']}%) breadth={d['institutional_breadth']} "
              f"direction={d['positioning_direction']}")
