"""SEC fails-to-deliver (FTD) positioning connector — bi-monthly settlement-fails by ticker.

CONDITIONING LAYER (Positioning sub-layer). No-edge control: an FTD spike is a crowding/short-
pressure tell (persistent fails often track aggressive shorting, hard-to-borrow names, or
naked-short pressure). It is NOT a thesis — it's a "how crowded is the short already" gauge that
helps decide whether a short divergence is a fresh frontrun or already-discovered.

Source: SEC's "Fails-to-Deliver Data" (Reg SHO), bi-monthly ZIPs at
  https://www.sec.gov/files/data/fails-deliver-data/cnsfails<YYYYMM><a|b>.zip
  (a = settlement dates 1st-15th of month, b = 16th-end). Pipe-delimited:
  SETTLEMENT DATE|CUSIP|SYMBOL|QUANTITY (FAILS)|DESCRIPTION|PRICE. Free, no auth (UA header required).

LAG (disclosed, surfaced — never backfilled): the SEC publishes each half-month file with a ~2-4
WEEK delay, so the freshest FTD observation for an asof is typically 2-6 weeks stale. The connector
fetches the most recent available file <= asof and reports its true settlement-date span in
asof_lag_days so the aggregator can down-weight a stale positioning read.

What we extract:
  - max_daily_fails, mean_daily_fails over the file's settlement dates for the symbol
  - n_fail_days, latest_settlement_date, latest_price
  - ftd_spike (bool): max_daily_fails large in absolute terms (>= _SPIKE_SHARES) — the cross-section
    threshold is applied in the aggregator; here we surface the raw level + a coarse flag.

Inputs: entity_name = TICKER. extra={'asof': 'YYYY-MM-DD'} chooses which half-month file to read.
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
    "summary": 'Settlement fails-to-deliver positioning tell. Any public ticker.',
}

import io
import zipfile
from datetime import datetime, timezone

from .base import BaseConnector, ConnectorObservation, ConnectorRequest, ConnectorResult, ErrorKind, safe_get

_BASE = "https://www.sec.gov/files/data/fails-deliver-data/cnsfails{ym}{half}.zip"
_UA = "SignalOS-BuysideDD/0.1 conditioning-layer research (contact: research@signalos.example)"
_SPIKE_SHARES = 250_000   # coarse absolute flag; real percentile threshold applied in aggregator


def _candidate_files(asof: datetime) -> list[tuple[str, str, str]]:
    """Most-recent-first list of (year-month, half, label) candidate FTD files <= asof.
    Walk back up to ~4 months since the latest file may lag the asof by weeks."""
    out = []
    y, m, day = asof.year, asof.month, asof.day
    # current month: 'b' first only if we're past mid-month AND it's likely published (it usually
    # isn't for the just-ended half), then 'a'. We try both and skip 404s.
    for back in range(0, 5):
        mm = m - back
        yy = y
        while mm <= 0:
            mm += 12
            yy -= 1
        ym = f"{yy}{mm:02d}"
        if back == 0 and day < 16:
            halves = ["a"]
        else:
            halves = ["b", "a"]
        for h in halves:
            out.append((ym, h, f"{ym}{h}"))
    return out


class SecFtdConnector(BaseConnector):
    source_id = "sec_ftd"
    rate_limit_per_min = 20
    user_agent = _UA

    def query(self, request: ConnectorRequest) -> ConnectorResult:
        sym = (request.entity_name or "").strip().upper()
        if not sym:
            return self._fail(request, ErrorKind.UNSUPPORTED, "entity_name (ticker) required")
        asof = request.extra.get("asof")
        try:
            asof_dt = datetime.fromisoformat(str(asof)) if asof else datetime.now(timezone.utc)
        except ValueError:
            asof_dt = datetime.now(timezone.utc)
        asof_dt = asof_dt.replace(tzinfo=None)

        sess = self._session()
        sess.headers["User-Agent"] = _UA
        sess.headers["Accept"] = "application/zip,*/*"

        rows = None
        used_label = None
        tried = []
        for ym, half, label in _candidate_files(asof_dt):
            url = _BASE.format(ym=ym, half=half)
            self._throttle()
            r, ek, ed = safe_get(sess, url, timeout=60)
            tried.append(label)
            if r is None:
                if ek == ErrorKind.NOT_FOUND:
                    continue          # file not published yet; walk back
                if ek in (ErrorKind.RATE_LIMIT, ErrorKind.AUTH):
                    return self._fail(request, ek, f"{ed} (file {label})")
                continue
            try:
                zf = zipfile.ZipFile(io.BytesIO(r.content))
                txt_name = next(n for n in zf.namelist() if n.lower().endswith(".txt"))
                raw = zf.read(txt_name).decode("latin-1", errors="replace")
            except Exception as e:
                # a 404 sometimes returns an HTML body with 200; skip non-zip
                continue
            rows = _parse_for_symbol(raw, sym)
            used_label = label
            break

        if rows is None:
            return self._fail(request, ErrorKind.NOT_FOUND,
                              f"no FTD file available <= {asof_dt.date()} (tried {tried})")
        if not rows:
            # file read fine, symbol simply has no fails -> a clean/un-crowded positioning signal
            lag = _file_lag_days(used_label, asof_dt)
            return self._ok(request, [
                ConnectorObservation(attribute="max_daily_fails", value=0, source_url=_BASE.format(ym=used_label[:6], half=used_label[6:]),
                                     extra={"note": "no fails in latest file = no FTD crowding",
                                            "file": used_label, "asof_lag_days": lag}),
                ConnectorObservation(attribute="ftd_spike", value=False, source_url="sec_ftd"),
                ConnectorObservation(attribute="ftd_file", value=used_label, source_url="sec_ftd"),
                ConnectorObservation(attribute="asof_lag_days", value=lag, source_url="sec_ftd"),
            ], raw="0 rows")

        fails = [q for _, q, _, _ in rows]
        dates = sorted({d for d, _, _, _ in rows})
        max_fails = max(fails)
        mean_fails = sum(fails) / len(fails)
        latest = max(rows, key=lambda t: t[0])
        lag = _file_lag_days(used_label, asof_dt, latest_settlement=latest[0])
        url = _BASE.format(ym=used_label[:6], half=used_label[6:])

        obs = [
            ConnectorObservation(attribute="max_daily_fails", value=max_fails, source_url=url,
                                 extra={"file": used_label}),
            ConnectorObservation(attribute="mean_daily_fails", value=round(mean_fails), source_url=url),
            ConnectorObservation(attribute="n_fail_days", value=len(dates), source_url=url),
            ConnectorObservation(attribute="latest_settlement_date", value=latest[0], source_url=url),
            ConnectorObservation(attribute="latest_fail_price", value=latest[2], source_url=url),
            ConnectorObservation(attribute="ftd_spike", value=bool(max_fails >= _SPIKE_SHARES), source_url=url,
                                 extra={"abs_threshold_shares": _SPIKE_SHARES,
                                        "note": "coarse absolute flag; percentile vs cross-section in aggregator"}),
            ConnectorObservation(attribute="ftd_file", value=used_label, source_url=url),
            ConnectorObservation(attribute="asof_lag_days", value=lag, source_url=url,
                                 extra={"note": "SEC publishes FTD with a ~2-4wk delay; never backfilled"}),
        ]
        return self._ok(request, obs, raw="\n".join(f"{d}|{q}" for d, q, _, _ in rows[:20]))


def _parse_for_symbol(raw: str, sym: str) -> list[tuple[str, int, float, str]]:
    out = []
    for line in raw.splitlines():
        if "|" not in line:
            continue
        parts = line.split("|")
        if len(parts) < 5:
            continue
        if parts[2].strip().upper() != sym:
            continue
        try:
            qty = int(parts[3].strip() or 0)
        except ValueError:
            continue
        try:
            price = float(parts[5]) if len(parts) > 5 and parts[5].strip() else None
        except ValueError:
            price = None
        out.append((parts[0].strip(), qty, price, parts[4].strip()))
    return out


def _file_lag_days(label: str, asof: datetime, latest_settlement: str | None = None) -> int | None:
    """Staleness of the FTD read vs asof, measured from the latest settlement date in the file."""
    ref = latest_settlement
    if not ref and label:
        # end-of-half proxy
        ym = label[:6]
        ref = f"{ym}15" if label.endswith("a") else f"{ym}28"
    if not ref:
        return None
    try:
        d = datetime.strptime(ref, "%Y%m%d")
        return (asof - d).days
    except ValueError:
        return None


if __name__ == "__main__":
    for t in ["RCAT", "GME"]:
        res = SecFtdConnector().query(ConnectorRequest(entity_name=t))
        d = {o.attribute: o.value for o in res.observations}
        print(f"{t}: success={res.success} err={res.error_kind} max_fails={d.get('max_daily_fails')} "
              f"spike={d.get('ftd_spike')} file={d.get('ftd_file')} lag_days={d.get('asof_lag_days')}")
