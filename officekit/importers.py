"""importers — deterministic statement importers for officekit intake.

Phase 1 ships ONE importer: a brokerage positions CSV (Fidelity/Vanguard/Schwab-style
export). It classifies each row into a sleeve category via a ticker table, pools
same-category funds into one sleeve per (category, style, account), splits any
CONCENTRATED single stock (>= 20% of the statement) into its own sleeve, and pools
the rest of the individual stocks with a holdings list. Values come straight off
the statement (confidence 'known'); classification is ours (a note says so).

Unknown symbols are NEVER silently guessed into a risky bucket: anything
unclassifiable lands in the pooled-stocks sleeve and is listed by name.
PDFs and messy statements go through the LLM intake agent instead — see
officekit/INTAKE_AGENT.md — which emits the same answers-JSON the wizard takes.
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

from officekit.betas import assign_betas

# ticker -> (category, style). The common-fund table; extend freely.
FUND_MAP = {
    # US total-market / S&P index
    "VTI": ("public_equity", None), "VTSAX": ("public_equity", None), "VOO": ("public_equity", None),
    "SPY": ("public_equity", None), "IVV": ("public_equity", None), "ITOT": ("public_equity", None),
    "FXAIX": ("public_equity", None), "FSKAX": ("public_equity", None), "SWTSX": ("public_equity", None),
    "SCHB": ("public_equity", None), "VFIAX": ("public_equity", None),
    # tech-tilted
    "QQQ": ("public_equity", "tech"), "QQQM": ("public_equity", "tech"), "VGT": ("public_equity", "tech"),
    # international / EM
    "VXUS": ("public_equity", "intl"), "VEA": ("public_equity", "intl"), "VGK": ("public_equity", "intl"),
    "VWO": ("public_equity", "intl"), "VEMAX": ("public_equity", "intl"), "VTIAX": ("public_equity", "intl"),
    "IEFA": ("public_equity", "intl"), "IEMG": ("public_equity", "intl"), "EFA": ("public_equity", "intl"),
    # bonds
    "BND": ("fixed_income", None), "VBTLX": ("fixed_income", None), "AGG": ("fixed_income", None),
    "BNDX": ("fixed_income", None), "FXNAX": ("fixed_income", None), "TLT": ("fixed_income", None),
    "VGSH": ("fixed_income", "short_duration"), "SHY": ("fixed_income", "short_duration"),
    # munis
    "VTEB": ("municipal_credit", None), "MUB": ("municipal_credit", None),
    "VCLAX": ("municipal_credit", None), "VWIUX": ("municipal_credit", None),
    # cash & equivalents
    "SGOV": ("cash", None), "BIL": ("cash", None), "VMFXX": ("cash", None), "SPAXX": ("cash", None),
    "SWVXX": ("cash", None), "VUSXX": ("cash", None), "FDRXX": ("cash", None),
}

CASH_DESC = re.compile(r"money market|cash|sweep|settlement", re.I)
TARGET_DATE = re.compile(r"target\s*(retire|date)|20[3-6]0|20[3-6]5", re.I)
# a pooled fund named without a ticker (401k collective trusts, mutual funds). Kept
# TIGHT so a single stock with "Trust" in its name (e.g. Northern Trust) is NOT caught.
FUND_NAME = re.compile(r"\b(index fund|mutual fund|fund|collective (investment )?trust|c\.?i\.?t\.?)\b"
                       r"|\b\d{4}\s*tr\b", re.I)
SKIP_ROW = re.compile(r"^(account\s*)?total|^pending activity|^\s*$", re.I)

CATEGORY_RISKS = {
    "public_equity": ["Market drawdown", "Cap-weight concentration"],
    "fixed_income": ["Rate duration", "Inflation erosion of fixed coupon"],
    "municipal_credit": ["Duration / rate sensitivity", "Issuer credit concentration"],
    "cash": ["Reinvestment / cash drag", "Inflation erosion"],
    "single_name_equity": ["Single-name idiosyncratic", "Concentration — sized position"],
}

CONCENTRATION_SPLIT = 0.20   # a single stock >= 20% of the statement gets its own sleeve


def _money(x):
    s = str(x or "").strip().replace("$", "").replace(",", "")
    if not s or s in ("-", "--", "n/a", "N/A"):
        return None
    neg = s.startswith("(") and s.endswith(")")
    s = s.strip("()")
    try:
        v = float(s)
    except ValueError:
        return None
    return -v if neg else v


def _find_columns(header):
    """Map semantic fields to column indexes from a header row (case/space tolerant)."""
    cols = {}
    for i, h in enumerate(header):
        k = re.sub(r"[^a-z ]", "", str(h).lower()).strip()
        if k in ("symbol", "ticker", "symbolcusip") and "symbol" not in cols:
            cols["symbol"] = i
        elif ("description" in k or k in ("name", "security", "security name", "investment")) and "desc" not in cols:
            cols["desc"] = i
        elif ("value" in k and "gain" not in k and "cost" not in k) and "value" not in cols:
            cols["value"] = i
        elif k in ("quantity", "shares", "qty") and "qty" not in cols:
            cols["qty"] = i
    return cols if ("symbol" in cols or "desc" in cols) and "value" in cols else None


def _classify(symbol, desc, extra_map=None):
    """-> (category, style) or ('__stock__', None) for an individual equity.
    extra_map overlays FUND_MAP with human-CONFIRMED mappings (answers
    fund_map / fund_map_learned.json) — confirmed beats built-in."""
    sym = (symbol or "").upper().strip()
    if extra_map and sym in extra_map:
        return tuple(extra_map[sym])
    if sym in FUND_MAP:
        return FUND_MAP[sym]
    # OFX / 401(k) exports put the fund's NAME where a ticker would be (e.g. symbol
    # "Target Retire 2055 Tr"), so match fund/cash patterns on symbol AND desc, not
    # desc alone — else a named fund falls through to __stock__ (2026-09-10).
    text = f"{symbol or ''} {desc or ''}"
    if CASH_DESC.search(text) or sym in ("CASH", "USD"):
        return ("cash", None)
    if TARGET_DATE.search(text):
        return ("public_equity", "target_date")
    if FUND_NAME.search(text):                        # collective trust / mutual fund named, no ticker
        return ("public_equity", None)
    # mutual-fund tickers are 5 letters ending in X — classify unknown ones as
    # plain public equity rather than a single-name bet
    if re.fullmatch(r"[A-Z]{5}", sym) and sym.endswith("X"):
        return ("public_equity", None)
    return ("__stock__", None)


def read_positions_csv(path):
    """Parse a positions CSV -> raw rows [{symbol, desc, value}] (no classification)."""
    rows = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        cols = None
        for raw in reader:
            if cols is None:
                cols = _find_columns(raw)
                continue
            if not raw or SKIP_ROW.match(str(raw[0])):
                continue
            get = lambda key: raw[cols[key]] if key in cols and cols[key] < len(raw) else ""
            val = _money(get("value"))
            if val is None or val == 0:
                continue
            rows.append({"symbol": str(get("symbol")).strip(), "desc": str(get("desc")).strip(), "value": val})
    if cols is None:
        raise ValueError(f"{path}: could not find a header row with symbol/description + value columns")
    return rows


def parse_positions_csv(path, account="brokerage", extra_map=None):
    """Parse a positions CSV -> list of BalanceSheet-v1 sleeves (values statement-sourced)."""
    return classify_positions(read_positions_csv(path), account=account, source=str(path),
                              extra_map=extra_map)


def unknown_symbols(rows, extra_map=None):
    """The AI-1 classification fallback's work queue: symbols with no CONFIRMED
    or table mapping — both the ones that would pool as individual stocks AND
    the ones the 5-letters-ending-in-X heuristic coarsely guesses (a muni fund
    guessed as public equity is exactly what the fallback should catch).
    Deterministic; no model."""
    out = []
    for r in rows:
        sym = str(r.get("symbol", "")).strip().upper()
        desc = str(r.get("desc", ""))
        if not sym or sym in out:
            continue
        if extra_map and sym in extra_map:
            continue
        if sym in FUND_MAP or sym in ("CASH", "USD"):
            continue
        if CASH_DESC.search(desc) or TARGET_DATE.search(desc):
            continue
        out.append(sym)
    return out


def classify_positions(rows, account="brokerage", source="positions", extra_map=None,
                       sma_symbols=None, sma_label="Direct-index SMA"):
    """Classify position rows [{symbol, value, desc?}] -> BalanceSheet-v1 sleeves.

    The ONE classification pipeline: the CSV parser feeds it, and so does manual
    in-app holdings entry — typed tickers get exactly the same fund map,
    concentration split, and pooling a statement upload gets. Hiding the intake
    complexity behind a file is not allowed (principal, 2026-09-03): typing your
    holdings is the honest cold path, so it is a first-class input.
    """
    from officekit.staging import num
    rows = [{"symbol": str(r.get("symbol", "")).strip().upper(),
             "desc": str(r.get("desc", "")).strip(),
             "value": num(r["value"])}                # tolerate "1,234" / "$1,234" typed input
            for r in rows if r.get("value") not in (None, "", 0)]
    if not rows:
        raise ValueError(f"{source}: no position rows to classify")

    total = sum(r["value"] for r in rows)
    buckets = {}     # (category, style) -> {"value", "symbols"}
    stocks = []      # individual equities
    for r in rows:
        cat, style = _classify(r["symbol"], r["desc"], extra_map)
        if cat == "__stock__":
            stocks.append(r)
            continue
        b = buckets.setdefault((cat, style), {"value": 0.0, "symbols": []})
        b["value"] += r["value"]
        if r["symbol"] and r["symbol"] not in b["symbols"]:
            b["symbols"].append(r["symbol"])

    sleeves = []
    src_note = f"classified by officekit importer from the {account} positions export"
    CAT_LABEL = {"public_equity": "US Equity", "fixed_income": "US Bond", "municipal_credit": "Muni",
                 "cash": "Cash / MMF"}
    STYLE_LABEL = {"intl": "Intl / EM Equity", "tech": "Tech Equity", "target_date": "Target-Date Fund",
                   "short_duration": "Short-Duration Bond"}
    for (cat, style), b in sorted(buckets.items(), key=lambda kv: -kv[1]["value"]):
        label = STYLE_LABEL.get(style) or CAT_LABEL.get(cat, cat)
        syms = " + ".join(b["symbols"][:3]) + (f" + {len(b['symbols'])-3} more" if len(b["symbols"]) > 3 else "")
        name = f"{label} — {syms} ({account})" if syms else f"{label} ({account})"
        sleeves.append(assign_betas({
            "name": name, "kind": "asset", "category": cat, "value": round(b["value"]),
            "target_pct": None, "_confidence": "known",
            "risks": list(CATEGORY_RISKS.get(cat, [])) + [src_note],
        }, style=style))

    # individual stocks: concentrated names split out, the rest pooled with holdings
    pooled = []
    # concentration is a fraction of the POSITIVE book — a net total of 0 (longs
    # cancel shorts) must not divide-by-zero, and a net-short/debit total must
    # not invert the ratio's sign (both would misfire the split)
    denom = sum(r["value"] for r in stocks if r["value"] > 0) or 1.0
    for r in sorted(stocks, key=lambda r: -r["value"]):
        if r["value"] / denom >= CONCENTRATION_SPLIT:
            sym = r["symbol"] or r["desc"]
            sleeves.append(assign_betas({
                "name": f"{sym} Concentrated ({account})", "kind": "asset",
                "category": "single_name_equity", "value": round(r["value"]),
                "target_pct": None, "_confidence": "known",
                "risks": list(CATEGORY_RISKS["single_name_equity"]) + [src_note],
            }))
        else:
            pooled.append(r)

    # DIRECT-INDEX SMA split: any pooled name that belongs to a known direct-index
    # SMA constituent set is separated into its own direct_index sleeve — same
    # individual lots, but a different risk/strategy read than deliberate single-name
    # picks (2026-09-10). Both remain lot-level TLH-capable.
    sma_syms = {str(s).strip().upper() for s in (sma_symbols or [])}
    sma_pooled = [r for r in pooled if r["symbol"] in sma_syms] if sma_syms else []
    other_pooled = [r for r in pooled if r not in sma_pooled]

    def _pool_sleeve(items, name, category, risks):
        syms = " + ".join(r["symbol"] for r in items[:3]) + (f" + {len(items)-3} more" if len(items) > 3 else "")
        return assign_betas({
            "name": f"{name} — {syms} ({account})", "kind": "asset", "category": category,
            "value": round(sum(r["value"] for r in items)), "target_pct": None, "_confidence": "known",
            "risks": risks + [src_note],
            "holdings": [{"company": r["symbol"] or r["desc"], "amount": round(r["value"])} for r in items],
        })

    if sma_pooled:
        sleeves.append(_pool_sleeve(
            sorted(sma_pooled, key=lambda r: -r["value"]), sma_label, "direct_index",
            ["Tracks its index — broad, not concentrated", "Lot-level tax-loss harvesting engine"]))
    if other_pooled:
        # when an SMA was split out, the remainder is the deliberate single-name book
        label = "Concentrated single names" if sma_pooled else "Individual stocks"
        sleeves.append(_pool_sleeve(
            sorted(other_pooled, key=lambda r: -r["value"]), label, "public_equity",
            ["Market drawdown", "Single-name dispersion within the pool"]))
    return sleeves


def run_import(spec, extra_map=None):
    """Dispatch one import spec {kind, path, account?} -> sleeves."""
    kind = spec.get("kind", "positions_csv")
    if kind == "positions_csv":
        from officekit.runtime import import_path
        return parse_positions_csv(import_path(spec["path"]), account=spec.get("account", "brokerage"),
                                   extra_map=extra_map)
    raise ValueError(f"unknown import kind: {kind!r}")
