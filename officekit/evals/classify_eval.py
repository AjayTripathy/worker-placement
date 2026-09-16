"""classify_eval — grade the AI-1 classifier against known ground truth.

    ANTHROPIC_API_KEY=... python3 -m officekit.evals.classify_eval

The eval set is everything we already know the answer to: the entire FUND_MAP
(labeled fund tickers), a control set of unambiguous single stocks, and the
known lookalike traps from live use (VWLUX-class). Symbol-only — the worst
case, which is what the typed-holdings path sees.

Grades the RAW model output (before suggest()'s confidence filter), then
reports what the filter would have let through:
  - category accuracy (the load-bearing number)
  - CONFIDENT-WRONG rate: wrong category at >= 0.6 confidence — the only
    failure class that reaches the confirmation step with a bad suggestion
  - calibration: mean confidence on correct vs wrong
  - style accuracy where category is right (secondary)

Writes results JSON next to this file (dated) — the proof-gate artifact for
default-on. Also flags disagreements worth a second look at OUR table, not
just the model.
"""
from __future__ import annotations

import json
import time
from datetime import date
from pathlib import Path

from officekit.importers import FUND_MAP
from officekit_ai.classify import _PROMPT, _SCHEMA, CLASSIFY_MODEL

# unambiguous individual stocks — the model must say single_name_equity
STOCK_CONTROLS = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META",
                  "JPM", "XOM", "UNH", "JNJ", "V", "WMT", "HD", "COST"]

# lookalike traps + funds we know cold but the table doesn't carry
EXTRA_TRUTH = {
    "VWLUX": ("municipal_credit", None),     # Vanguard Long-Term Tax-Exempt — the live miss
    "SUB": ("municipal_credit", None),       # iShares Short-Term National Muni
    "FLOT": ("fixed_income", None),          # iShares Floating Rate Bond
    "QQQJ": ("public_equity", "tech"),       # Invesco Nasdaq Next Gen 100
    "SCHD": ("public_equity", None),         # Schwab US Dividend Equity
    "VUG": ("public_equity", None),          # Vanguard Growth
}


def truth_set():
    t = {sym: (cat, style) for sym, (cat, style) in FUND_MAP.items()}
    t.update(EXTRA_TRUTH)
    t.update({s: ("single_name_equity", None) for s in STOCK_CONTROLS})
    return t


def run(batch_size=25, model=CLASSIFY_MODEL):
    import anthropic
    cl = anthropic.Anthropic()
    truth = truth_set()
    syms = sorted(truth)
    raw = {}
    for i in range(0, len(syms), batch_size):
        batch = syms[i:i + batch_size]
        listing = "\n".join(f"- {s}" for s in batch)
        resp = cl.messages.create(
            model=model, max_tokens=4000,
            messages=[{"role": "user", "content": _PROMPT.format(symbols=listing)}],
            output_config={"format": {"type": "json_schema", "schema": _SCHEMA}})
        text = next(b.text for b in resp.content if b.type == "text")
        for c in json.loads(text)["classifications"]:
            raw[c["symbol"].upper()] = c
        time.sleep(0.5)

    rows, correct, confident_wrong = [], 0, []
    conf_ok, conf_bad = [], []
    style_n = style_ok = 0
    for sym in syms:
        want_cat, want_style = truth[sym]
        got = raw.get(sym) or {"category": "MISSING", "style": None, "confidence": 0.0}
        ok = got["category"] == want_cat
        conf = float(got.get("confidence") or 0)
        (conf_ok if ok else conf_bad).append(conf)
        if ok:
            correct += 1
            if want_style is not None:
                style_n += 1
                style_ok += got.get("style") == want_style
        elif conf >= 0.6 and got["category"] != "single_name_equity":
            # the only dangerous class: a wrong FUND suggestion that would
            # actually reach the confirmation step
            confident_wrong.append(sym)
        rows.append({"symbol": sym, "want": [want_cat, want_style],
                     "got": [got["category"], got.get("style")], "conf": conf, "ok": ok})

    n = len(syms)
    summary = {
        "date": date.today().isoformat(), "model": model, "n": n,
        "category_accuracy": round(correct / n, 3),
        "confident_wrong": confident_wrong,
        "confident_wrong_rate": round(len(confident_wrong) / n, 3),
        "mean_conf_correct": round(sum(conf_ok) / len(conf_ok), 3) if conf_ok else None,
        "mean_conf_wrong": round(sum(conf_bad) / len(conf_bad), 3) if conf_bad else None,
        "style_accuracy_given_category": round(style_ok / style_n, 3) if style_n else None,
    }
    out = Path(__file__).parent / f"classify_eval_{summary['date'].replace('-', '')}.json"
    out.write_text(json.dumps({"summary": summary, "rows": rows}, indent=1))
    return summary, rows, out


if __name__ == "__main__":
    summary, rows, out = run()
    print(json.dumps(summary, indent=1))
    print("\nmisses:")
    for r in rows:
        if not r["ok"]:
            print(f"  {r['symbol']:6s} want {r['want'][0]:18s} got {r['got'][0]:18s} conf {r['conf']:.2f}")
    print(f"\nresults -> {out}")
