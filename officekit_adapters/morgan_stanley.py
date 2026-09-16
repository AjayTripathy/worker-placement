"""morgan_stanley — first-class parser for the Morgan Stanley Prime Brokerage
statement family (the Parametric bundles land here: MS owns Parametric Portfolio
Associates, and the extracts are MS Prime report formats).

WHY THIS EXISTS: the same five report formats were being hand-parsed in two
places — the desk's parametric_sync.py and a separate msprime repo — each
re-deriving column maps and each carrying its own bugs (the desk read only the
newest bundle AND only the first gain/loss file per bundle; msprime assumed the
gain/loss files were cumulative when they are DAILY windows). This module is the
one place that knows the formats, so every consumer inherits the same correct
parse. It is the seed of the compounding statement library: a second broker's
report family is a sibling module following the same ReportSpec pattern.

THE REPORT FAMILY (a bundle is a dated zip of these CSVs, prefix = report code):
  MAC001X    Global Positions Extract        — point-in-time holdings snapshot
  CCAR001X   Open Taxlot Extract             — point-in-time open-lot snapshot
  CCAR002X   Daily Gain/Loss Summary Extract — a DAILY WINDOW of closed lots;
             YTD realized only reconstructs by MERGING every daily file across
             every bundle, keyed by taxlot (idempotent). A bundle carries
             several (different report dates + empty Count=0 stubs).
  MAC002TDX  Normalized Trade Date Activity  — per-trade activity (buy/sell,
             long/short side — the authority for book-side attribution)
  IN106MX    Daily Interest Summary          — per-currency debit/credit/MMF
             (note: TWO metadata header rows before the real column header)

stdlib-only by design (officekit ships without pandas). Read-only on the world.

    from officekit_adapters import morgan_stanley as ms
    bundle = ms.parse_bundle("~/Downloads/Bundle_09062026032524.zip")
    ledger = ms.RealizedLedger.load(path); ledger.merge_bundles(ms.find_bundles())
    rows = ms.positions_rows(bundle)          # -> the adapter row contract
"""
from __future__ import annotations

import csv
import io
import json
import re
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

DOWNLOADS = Path.home() / "Downloads"
BUNDLE_GLOB = "Bundle_*.zip"


def _num(x) -> float | None:
    """Tolerant numeric coercion: strips commas, accounting parens, unicode
    minus; returns None on a non-number (a blank or a T/F flag)."""
    if x is None:
        return None
    s = str(x).strip().replace(",", "").replace("−", "-")
    if s.startswith("(") and s.endswith(")"):
        s = "-" + s[1:-1]
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


# --------------------------------------------------------------- report specs

@dataclass(frozen=True)
class ReportSpec:
    code: str                       # filename prefix, e.g. "CCAR002X"
    name: str                       # human name
    columns: dict                   # canonical_name -> source header (exact)
    numeric: frozenset = frozenset()  # canonical names to coerce to float|None
    header_skip: int = 0            # metadata rows before the real header
    empty_sentinel: str | None = None  # raw substring meaning "no data" (Count=0)
    date_col: str | None = None     # canonical col that must be a real date to keep a row


REPORTS: dict[str, ReportSpec] = {
    "MAC001X": ReportSpec(
        code="MAC001X", name="Global Positions Extract", date_col="reporting_date",
        columns={
            "reporting_date": "Reporting Date", "main_account": "Main Account Number",
            "sub_account": "Sub Account Number", "symbol": "Symbol",
            "security_description": "Security Description", "cusip": "CUSIP",
            "quantity": "Current Quantity", "long_short_code": "Long/Short Code",
            "price_usd": "Price (USD)", "market_value_usd": "Market Value / Net Equity (USD)",
            "gross_market_value_usd": "Gross Market Value (USD)",
            "accrued_interest_usd": "Accrued Interest (USD)", "asset_class": "Asset Class",
            "product_type": "Product Type", "issue_currency": "Issue Currency"},
        numeric=frozenset({"quantity", "price_usd", "market_value_usd",
                           "gross_market_value_usd", "accrued_interest_usd"})),
    "CCAR001X": ReportSpec(
        code="CCAR001X", name="Open Taxlot Extract",
        columns={
            "reported_date": "Reported Date", "portfolio_id": "Portfolio Id",
            "cusip": "CUSIP", "symbol": "Symbol", "security_description": "Security Description",
            "strategy": "Strategy", "taxlot_id": "Taxlot ID", "date_acquired": "Date Acquired",
            "is_covered": "Is Covered", "days_held": "Days Held", "quantity": "Quantity",
            "unit_cost": "Base Unit Cost", "cost": "Base Cost",
            "issue_unit_cost": "Issue Unit Cost", "issue_cost": "Issue Cost",
            "issue_currency": "Issue Currency"},
        numeric=frozenset({"days_held", "quantity", "unit_cost", "cost",
                           "issue_unit_cost", "issue_cost"})),
    "CCAR002X": ReportSpec(
        code="CCAR002X", name="Daily Gain/Loss Summary Extract", empty_sentinel="Count=0",
        date_col="reported_date",
        columns={
            "reported_date": "Reported Date", "portfolio_id": "Portfolio Id", "cusip": "CUSIP",
            "symbol": "Symbol", "security_description": "Security Description",
            "strategy": "Strategy", "taxlot_id": "Taxlot ID", "date_acquired": "Date Acquired",
            "date_closed": "Date Closed", "quantity": "Quantity",
            "cost": "Base Cost", "proceeds": "Base Proceeds", "gainloss": "Base GainLoss",
            "issue_gainloss": "Issue GainLoss", "gainloss_type": "GainLoss Type",
            "loss_disallowed": "Loss Disallowed", "issue_currency": "Issue Currency"},
        numeric=frozenset({"quantity", "cost", "proceeds", "gainloss", "issue_gainloss"})),
    "MAC002TDX": ReportSpec(
        code="MAC002TDX", name="Normalized Trade Date Activity Extract",
        columns={
            "report_date": "Report Date", "main_account": "MainAccountNumber",
            "security_description": "Security Description", "symbol": "SYMBOL", "cusip": "CUSIP",
            "activity_category": "Activity Category", "transaction_desc": "Transaction Desc Long",
            "buy_sell": "Buy Sell", "long_short": "Long Short", "quantity": "Quantity",
            "price_usd": "Price USD", "principal_usd": "Principal USD",
            "net_amt_usd": "Net Amt USD", "trade_date": "Trade Date",
            "settle_date": "Settle Date", "product_type": "Product Type Desc"},
        numeric=frozenset({"quantity", "price_usd", "principal_usd", "net_amt_usd"})),
    "IN106MX": ReportSpec(
        code="IN106MX", name="Daily Interest Summary", header_skip=1,
        columns={
            "grandparent_account": "Grandparent Account", "grandparent_name": "Grandparent Name",
            "child_account": "Child Account", "currency": "Currency", "value_date": "Value Date",
            "net_debit_balance": "Net Debit Balance", "debit_rate": "Debit Rate",
            "debit_interest": "Debit Interest", "net_credit_balance": "Net Credit Balance",
            "credit_rate": "Credit Rate", "credit_interest": "Credit Interest",
            "money_market_balance": "Money Market Balance", "money_market_yield": "Money Market Yield",
            "money_market_accrual": "Money Market Accrual"},
        numeric=frozenset({"net_debit_balance", "debit_rate", "debit_interest",
                           "net_credit_balance", "credit_rate", "credit_interest",
                           "money_market_balance", "money_market_yield", "money_market_accrual"})),
}

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}|^\d{2}/\d{2}/\d{4}")


def detect_report(filename: str) -> str | None:
    """Report code from a filename (prefix match), or None if unrecognised."""
    stem = Path(filename).name.upper()
    for code in REPORTS:
        if stem.startswith(code):
            return code
    return None


def parse_report(raw: str, spec: ReportSpec) -> list[dict]:
    """Parse one report's CSV text into canonical-keyed dicts. Empty
    (Count=0) files yield []. Numeric columns coerce to float|None; the rest
    stay stripped strings. Unknown source columns are ignored; missing ones
    are simply absent from each row."""
    if spec.empty_sentinel and spec.empty_sentinel in raw:
        return []
    rows = list(csv.reader(io.StringIO(raw)))
    rows = rows[spec.header_skip:]
    if len(rows) < 2:
        return []
    src_idx = {h.strip(): i for i, h in enumerate(rows[0])}
    # canonical -> column index, only for headers actually present
    idx = {canon: src_idx[src] for canon, src in spec.columns.items() if src in src_idx}
    ncols = len(rows[0])
    out = []
    for r in rows[1:]:
        if not any(c.strip() for c in r):
            continue
        rec = {}
        for canon, i in idx.items():
            v = r[i].strip() if i < len(r) else ""
            rec[canon] = _num(v) if canon in spec.numeric else v
        if spec.date_col and not _DATE_RE.match(str(rec.get(spec.date_col) or "")):
            continue                        # drop trailing "Count=N"/summary rows
        out.append(rec)
    return out


# --------------------------------------------------------------------- bundle

@dataclass
class Bundle:
    """A parsed Morgan Stanley statement bundle. `records[code]` is the
    concatenation of every file of that report type in the zip (a bundle can
    carry several dated gain/loss files — all are kept and merged downstream)."""
    path: Path
    as_of: str | None
    records: dict = field(default_factory=dict)   # report_code -> list[dict]

    def positions(self) -> list[dict]:
        return self.records.get("MAC001X", [])

    def taxlots(self) -> list[dict]:
        return self.records.get("CCAR001X", [])

    def gainloss(self) -> list[dict]:
        return self.records.get("CCAR002X", [])

    def trades(self) -> list[dict]:
        return self.records.get("MAC002TDX", [])

    def interest(self) -> list[dict]:
        return self.records.get("IN106MX", [])


def _as_of_from_name(name: str) -> str | None:
    m = re.search(r"(\d{2})(\d{2})(\d{4})", name)            # Bundle_MMDDYYYY...
    if m:
        mm, dd, yyyy = m.groups()
        return f"{yyyy}-{mm}-{dd}"
    return None


# point-in-time SNAPSHOT reports: a bundle may ship several report-date copies of
# these in one zip (e.g. 28/29/30 Aug open-taxlot + positions extracts). They are
# snapshots, NOT windows — concatenating them TRIPLES market value and the harvest
# loss surface (the 2026-09-10 "much larger loss" bug). Keep only the latest.
_SNAPSHOT_CODES = {"MAC001X", "CCAR001X"}
_MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}


def _file_report_date(name: str) -> str:
    """The report date embedded in a bundle filename ('08Sep2026' -> '2026-09-08'),
    or '' — used to pick the latest copy of a snapshot report."""
    m = re.search(r"(\d{1,2})([A-Za-z]{3})(\d{4})", name)
    if not m:
        return ""
    dd, mon, yyyy = m.groups()
    mi = _MONTHS.get(mon.lower())
    return f"{yyyy}-{mi:02d}-{int(dd):02d}" if mi else ""


def parse_bundle(path) -> Bundle:
    """Parse every recognised CSV in a bundle zip. SNAPSHOT reports (positions,
    open taxlots) keep only their latest report-date copy — a bundle is ONE point
    in time, so multiple copies must never be summed. Overlapping gain/loss
    windows are unioned by lot key (idempotent). Unrecognised files ignored."""
    path = Path(path).expanduser()
    by_code: dict[str, list] = {}                    # code -> [(name, rows), ...]
    with zipfile.ZipFile(path) as z:
        for name in z.namelist():
            if not name.lower().endswith(".csv"):
                continue
            code = detect_report(name)
            if not code:
                continue
            raw = z.read(name).decode("utf-8-sig", errors="replace")
            by_code.setdefault(code, []).append((name, parse_report(raw, REPORTS[code])))

    records: dict[str, list] = {}
    for code, items in by_code.items():
        if code in _SNAPSHOT_CODES and len(items) > 1:
            # several report-date copies of a point-in-time snapshot -> latest only
            _, rows = max(items, key=lambda it: _file_report_date(it[0]))
            records[code] = rows
        elif code == "CCAR002X" and len(items) > 1:
            # overlapping daily/MTD gain-loss windows -> union of unique closes
            seen = {}
            for _, rows in items:
                for r in rows:
                    seen[_lot_key(r)] = r
            records[code] = list(seen.values())
        else:
            records[code] = [r for _, rows in items for r in rows]
    return Bundle(path=path, as_of=_as_of_from_name(path.name), records=records)


def find_bundles(directory=None) -> list[Path]:
    """Every bundle zip in a directory, oldest-first (mtime). Defaults to the
    module DOWNLOADS, read at call time (so it stays monkeypatch-friendly)."""
    d = Path(directory or DOWNLOADS).expanduser()
    return sorted(d.glob(BUNDLE_GLOB), key=lambda p: p.stat().st_mtime) if d.is_dir() else []


def newest_bundle(directory=None) -> Path | None:
    bs = find_bundles(directory)
    return bs[-1] if bs else None


# ------------------------------------------------------- realized-lot ledger

def _lot_key(rec: dict) -> str:
    # the SAME lot closes in multiple partial pieces per day, so qty+gl are part
    # of the key; idempotent whether the source file is a daily window or a
    # cumulative re-list (re-writing the same key is a no-op).
    return "|".join(str(rec.get(k, "")) for k in ("taxlot_id", "date_closed", "quantity", "gainloss"))


@dataclass
class RealizedLedger:
    """The cumulative realized-gain/loss ledger, merged from the daily gain/loss
    windows across every bundle. Split by HOLDING PERIOD (GainLoss Type — what
    Schedule D wants). Book-side (long-book vs short-book) is a DIFFERENT axis
    that lives in the trade activity, not this extract — see book_side_split()."""
    lots: dict = field(default_factory=dict)

    @classmethod
    def load(cls, path) -> "RealizedLedger":
        p = Path(path)
        if p.exists():
            d = json.loads(p.read_text())
            return cls(lots=d.get("lots", {}))
        return cls()

    def merge_bundle(self, bundle: Bundle) -> int:
        before = len(self.lots)
        for rec in bundle.gainloss():
            gl = rec.get("gainloss")
            if gl is None or not rec.get("taxlot_id"):
                continue
            dis = str(rec.get("loss_disallowed") or "").strip()
            self.lots[_lot_key(rec)] = {
                "sym": rec.get("symbol", ""), "closed": rec.get("date_closed", ""),
                "acquired": rec.get("date_acquired", ""), "qty": rec.get("quantity"),
                "gl": round(gl, 2), "type": rec.get("gainloss_type", ""),
                "disallowed": _num(dis) or 0.0, "wash_flag": dis.upper() == "T"}
        return len(self.lots) - before

    def merge_bundles(self, paths) -> int:
        return sum(self.merge_bundle(parse_bundle(p)) for p in paths)

    def summary(self, note: str = "") -> dict:
        lots = self.lots.values()
        st = sum(l["gl"] for l in lots if str(l["type"]).startswith("SHORT"))
        lt = sum(l["gl"] for l in lots if str(l["type"]).startswith("LONG"))
        return {
            "n_lots": len(self.lots), "st_net": round(st), "lt_net": round(lt),
            "net": round(st + lt),
            "st_loss": round(sum(l["gl"] for l in lots if str(l["type"]).startswith("SHORT") and l["gl"] < 0)),
            "lt_loss": round(sum(l["gl"] for l in lots if str(l["type"]).startswith("LONG") and l["gl"] < 0)),
            "wash_disallowed": round(sum(l.get("disallowed") or 0 for l in lots)),
            "wash_flagged_lots": sum(1 for l in lots if l.get("wash_flag")),
            "axis": "holding_period (ST/LT tax term); book-side needs a trades join",
            "note": note}

    def book_side_split(self, bundle: Bundle) -> dict:
        """BEST-EFFORT long-book vs short-book split, joining each closed lot to
        the position's Long/Short Code by symbol (the gain/loss extract carries
        no side field). Approximate: a symbol traded on both sides over the year
        maps to its latest snapshot side. Honest-labeled, never presented as the
        authority — the trade activity (MAC002TDX Long Short) is."""
        side = {}
        for p in bundle.positions():
            sym = p.get("symbol")
            if sym and p.get("long_short_code"):
                side[sym] = str(p["long_short_code"]).upper()[:1]   # 'L' / 'S'
        long_gl = sum(l["gl"] for l in self.lots.values() if side.get(l["sym"], "L") != "S")
        short_gl = sum(l["gl"] for l in self.lots.values() if side.get(l["sym"]) == "S")
        return {"long_book_net": round(long_gl), "short_book_net": round(short_gl),
                "matched_symbols": len(side),
                "note": "approximate: closed lots joined to latest position side by symbol"}

    def save(self, path, note: str = "") -> dict:
        summ = self.summary(note)
        Path(path).write_text(json.dumps({"lots": self.lots, "summary": summ}, indent=1))
        return summ


# ------------------------------------------------- scorecard generation
# (migrated from desk/parametric_sync.py 2026-09-10 — the harvest-health scorecard
# is a MS-bundle-derived artifact, so it belongs in the bundle library; the office
# now GENERATES it instead of reading desk/data. See desk-deprecation ruling.)
FEES = {"parametric_pct": 0.0051, "mfo_pct": 0.0040}   # all-in 0.91%/yr (user 2026-07)


def scorecard_from_bundle(bundle: "Bundle", realized_summary: dict,
                          prev_card: dict = None, our_book=frozenset(), today=None):
    """Harvest-health scorecard from a parsed bundle: gross/net structure, the
    harvestable loss surface, embedded G/L, the lot-age (ossification) clock, and
    the realized-YTD summary. Pure over the bundle's canonical records (which are
    already snapshot-deduped in parse_bundle)."""
    import datetime as _dt
    today = today or _dt.date.today()
    longs = shorts = cash = 0.0
    px, netpos = {}, {}
    for p in bundle.positions():
        v = p.get("market_value_usd")
        sym = (p.get("symbol") or "").strip()
        if v is None or not sym:
            continue
        if sym == "USD" or str(p.get("product_type") or "").upper().replace(" ", "") == "CASH":
            cash += v
            continue
        if p.get("price_usd") is not None:
            px[sym] = p["price_usd"]
        netpos[sym] = netpos.get(sym, 0) + v
        longs += v if v > 0 else 0
        shorts += v if v < 0 else 0
    net = longs + shorts + cash
    overlap = {s: round(v) for s, v in netpos.items() if s in our_book}

    mv = gl = loss_mv = loss_amt = short_harv = 0.0
    n_loss = n_lots = 0
    ages = {"lt1y": 0.0, "y1to3": 0.0, "gt3y": 0.0}
    for lot in bundle.taxlots():
        sym = (lot.get("symbol") or "").strip()
        q, uc = lot.get("quantity"), lot.get("unit_cost")
        if sym not in px or not q or uc is None:
            continue
        try:
            da = _dt.date.fromisoformat(str(lot.get("date_acquired"))[:10])
        except (ValueError, TypeError):
            continue
        lmv = q * px[sym]
        lgl = lmv - q * uc
        if q > 0:
            n_lots += 1
            mv += lmv
            gl += lgl
            age = (today - da).days
            ages["lt1y" if age < 365 else ("y1to3" if age < 1095 else "gt3y")] += lmv
            if lgl < -50:
                n_loss += 1
                loss_mv += lmv
                loss_amt += lgl
        elif lgl < -50:
            short_harv += lgl

    card = {"asof": today.isoformat(), "bundle": bundle.path.name,
            "structure": {"gross_long": round(longs), "gross_short": round(shorts), "cash": round(cash),
                          "net": round(net), "ratio": f"{longs/net*100:.0f}/{abs(shorts)/net*100:.0f}" if net else "?"},
            "harvest": {"long_loss_lots": n_loss, "long_harvestable": round(loss_amt),
                        "short_harvestable": round(short_harv),
                        "total_surface": round(loss_amt + short_harv),
                        "surface_pct_of_mv": round((loss_amt + short_harv) / mv * 100, 2) if mv else None},
            "embedded": {"long_mv": round(mv), "long_gl": round(gl), "gl_pct": round(gl / mv * 100, 1) if mv else None},
            "ossification_clock": {k: round(v) for k, v in ages.items()},
            "our_book_overlap": overlap,
            "realized_ytd": realized_summary,
            "fees": {"all_in_pct": round((FEES["parametric_pct"] + FEES["mfo_pct"]) * 100, 2),
                     "annual_usd": round(net * (FEES["parametric_pct"] + FEES["mfo_pct"])),
                     "parametric_usd": round(net * FEES["parametric_pct"]),
                     "mfo_usd": round(net * FEES["mfo_pct"])},
            "prior": {k: prev_card.get(k) for k in ("asof", "harvest", "embedded")} if prev_card else None}
    return card


def build_scorecard(directory=None, our_book=frozenset(), prev_card=None):
    """Generate the full Parametric scorecard from the bundles on disk: realized YTD
    merged across EVERY bundle (idempotent by lot key), structure + harvest surface
    from the newest. Returns the card dict, or None if no bundle is present. This is
    the office-side generator — no desk/data dependency."""
    bundles = find_bundles(directory)
    if not bundles:
        return None
    ledger = RealizedLedger()
    ledger.merge_bundles(bundles)
    summ = ledger.summary("accumulated across every bundle (holding-period split)")
    newest = parse_bundle(bundles[-1])
    if not newest.positions() or not newest.taxlots():
        return None
    return scorecard_from_bundle(newest, summ, prev_card=prev_card, our_book=our_book)


# ------------------------------------------------- adapter row projection

# MS product_type code -> the adapter row's sec_type. Classify off product_type,
# NOT asset_class: MS labels equities held in a cash (vs margin) account
# "Cash Securities", which a loose "CASH" substring match wrongly reads as cash
# (live bug 2026-09-07 — 519 stocks booked as cash). Real cash is product_type
# "CASH" / symbol "USD".
_PRODUCT_SEC = {"EQTY": "STK", "ETF": "STK", "MF": "STK", "ADR": "STK",
                "CASH": "CASH", "MMF": "CASH",
                "BOND": "BOND", "FI": "BOND", "FIXEDINCOME": "BOND",
                "OPT": "OPT", "FUT": "FUT"}


def positions_rows(bundle: Bundle, base="USD") -> list[dict]:
    """Project the Global Positions snapshot onto the adapter row contract
    (symbol/qty/value/description/account/ccy/sec_type). Market value is
    ALREADY USD in the MS extract ('Market Value / Net Equity (USD)') — no FX
    conversion, unlike the live IBKR feed. Cash = symbol 'USD' or product_type
    'CASH' (a short-book financing leg is a NEGATIVE cash row — kept signed)."""
    rows = []
    for p in bundle.positions():
        sym = (p.get("symbol") or "").strip()
        if not sym:
            continue
        acct = p.get("main_account") or p.get("sub_account") or "Morgan Stanley"
        pt = str(p.get("product_type") or "").upper().replace(" ", "")
        val = p.get("market_value_usd") or 0
        if sym == "USD" or pt == "CASH":
            rows.append({"symbol": "CASH", "qty": p.get("quantity") or 0, "value": val,
                         "ccy": p.get("issue_currency") or base, "sec_type": "CASH",
                         "account": acct, "description": f"MS cash balance ({acct})"})
            continue
        rows.append({"symbol": sym, "qty": p.get("quantity") or 0, "value": val,
                     "ccy": p.get("issue_currency") or base,
                     "sec_type": _PRODUCT_SEC.get(pt, "STK"), "account": acct,
                     "description": p.get("security_description") or sym})
    return rows


# ---------------------------------------------------------------- adapter

def register():
    """Register the MS bundle as a first-class import adapter. Called at package
    import; kept as a function so tests can register into a fresh registry."""
    from officekit_adapters import adapter

    @adapter("morgan_stanley_bundle", label="Morgan Stanley Prime Brokerage (statement bundle)",
             kind="file")
    def _ms_bundle():
        def detect(ctx):
            bs = find_bundles()
            if not bs:
                return {"found": False, "status": "absent",
                        "detail": f"no {BUNDLE_GLOB} in {DOWNLOADS}",
                        "guidance": "drop a Morgan Stanley / Parametric statement bundle in Downloads"}
            newest = bs[-1]
            return {"found": True, "status": "ready",
                    "detail": f"{len(bs)} bundle(s); newest {newest.name} "
                              f"({_as_of_from_name(newest.name) or '?'})"}

        def fetch(ctx):
            b = newest_bundle()
            if not b:
                raise RuntimeError("no Morgan Stanley bundle found")
            return positions_rows(parse_bundle(b))

        return {"detect": detect, "fetch": fetch}

    return _ms_bundle
