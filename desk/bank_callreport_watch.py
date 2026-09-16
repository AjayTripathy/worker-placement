"""bank_callreport_watch — v1.5 forward instrumentation for the WAL + FSBW starters (built 2026-07-29).

Polls the FDIC BankFind financials API (free, no key; ~60d lag after quarter-end) and grades
the red-team kill triggers MECHANICALLY as each new call report lands:

  WAL (Western Alliance Bank, cert 57512 — red-team verified):
    - estimated uninsured deposits % (DEPUNA/DEP; red team: 36.5% at 2026-03-31, kill bar >40%)
    - uninsured RISING while insured (DEPINS) shrinks q/q = the scar-reopen mix tell
    - net charge-offs annualized (4*NTLNLSQ/LNLSNET) vs the 0.60% bar
      (bank-level ALL-IN basis: the Q1 fraud quarter printed ~1.45% here — this bar fires on
       the unadjusted series by design; the holdco "adjusted" series is management's)
  FSBW (1st Security Bank of Washington — cert RESOLVED via the institutions API, cached):
    - construction & land development / total risk-based capital (LNRECONS/RBC;
      Q1-26 = 102.9%, red-added kill bar >~115%)
    - retail deposits proxy (DEP - BRO) runoff >5% seq = the re-specified retail-only trigger
    - ACL/loans (LNATRES/LNLSNET) < 1.10% while NCOs annualized > 0.5% (red-added)

Basis caveats (named, not hidden): FDIC data is BANK-level; holdco ratios (WAL nonaccrual/HFI
0.92%, TCE) differ. WAL's NCLNLSR noncurrent ratio is structurally inflated by government-
guaranteed GNMA early-buyout mortgage loans -> reported TREND-ONLY, never against the holdco
1.3% nonaccrual kill bar. Reciprocal (CDARS/ICS) balances are NOT a servable field -> the
"reciprocal shrinking" leg of WAL's kill trigger is approximated by DEPINS (insured) shrinking;
named as a proxy. DATA MISSING never zero; a quarter with no new REPDTE reports exactly that.

TRIPWIRE NOWCAST, not alpha. Grades alongside the Q3-2026 prints (WAL ~mid-Oct, FSBW ~late-Oct).
"""
from __future__ import annotations
import json, sys, datetime, urllib.request, urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "desk" / "data" / "bank_callreport"
STATE = DATA / "state.json"
HISTORY = DATA / "history.jsonl"

API = "https://api.fdic.gov/banks"
FIELDS = "REPDTE,DEP,DEPUNA,DEPINS,BRO,LNRECONS,RBC,LNLSNET,NTLNLSQ,NCLNLSR,NAASSET,ASSET,LNATRES"
UA = {"User-Agent": "Mozilla/5.0 (desk research; contact: none)"}


def _get(url):
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=40) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"_error": str(e)[:140]}


def resolve_cert(name: str, city: str, state: dict) -> int | None:
    """Institutions-API exact-name resolution, cached in state (never guess a cert)."""
    cached = state.get("certs", {}).get(name)
    if cached:
        return cached
    q = urllib.parse.quote(f'NAME:"{name}"')
    j = _get(f"{API}/institutions?search={q}&fields=CERT,NAME,CITY,ACTIVE&limit=5&format=json")
    if "_error" in j:
        return None
    rows = [d["data"] for d in j.get("data", [])]
    hits = [r for r in rows if r.get("ACTIVE") == 1 and r.get("NAME", "").lower() == name.lower()
            and (not city or r.get("CITY", "").lower() == city.lower())]
    if len(hits) != 1:
        return None  # ambiguity -> UNRESOLVED, never a silent pick (matcher-hardening lesson)
    state.setdefault("certs", {})[name] = hits[0]["CERT"]
    return hits[0]["CERT"]


def fetch_quarters(cert: int, n=6):
    j = _get(f"{API}/financials?filters=CERT:{cert}&fields={FIELDS}&sort_by=REPDTE&sort_order=DESC&limit={n}&format=json")
    if "_error" in j:
        return None, j["_error"]
    rows = [d["data"] for d in j.get("data", [])]
    return (rows, None) if rows else (None, "empty result")


def pct(a, b):
    return round(100.0 * a / b, 2) if (a is not None and b) else None


def wal_metrics(q):
    return {
        "repdte": q["REPDTE"],
        "uninsured_pct": pct(q.get("DEPUNA"), q.get("DEP")),
        "insured_musd": round(q.get("DEPINS", 0) / 1000, 1),
        "deposits_musd": round(q.get("DEP", 0) / 1000, 1),
        "nco_ann_pct": pct(4 * q.get("NTLNLSQ", 0), q.get("LNLSNET")),
        "noncurrent_pct_TREND_ONLY": round(q.get("NCLNLSR", 0), 2),
        "brokered_pct": pct(q.get("BRO"), q.get("DEP")),
    }


def fsbw_metrics(q):
    return {
        "repdte": q["REPDTE"],
        "cd_conc_pct_rbc": pct(q.get("LNRECONS"), q.get("RBC")),
        "retail_dep_musd": round((q.get("DEP", 0) - q.get("BRO", 0)) / 1000, 1),
        "brokered_pct": pct(q.get("BRO"), q.get("DEP")),
        "acl_pct_loans": pct(q.get("LNATRES"), q.get("LNLSNET")),
        "nco_ann_pct": pct(4 * q.get("NTLNLSQ", 0), q.get("LNLSNET")),
        "noncurrent_pct": round(q.get("NCLNLSR", 0), 2),
    }


def grade(bank, cur, prior, flags):
    if bank == "WAL":
        if cur["uninsured_pct"] is not None and cur["uninsured_pct"] > 40:
            flags.append(f"FLAG WAL: uninsured {cur['uninsured_pct']}% > 40% kill bar")
        if prior and cur["uninsured_pct"] and prior["uninsured_pct"] and \
           cur["uninsured_pct"] > prior["uninsured_pct"] and cur["insured_musd"] < prior["insured_musd"]:
            flags.append("FLAG WAL: uninsured RISING while insured (DEPINS proxy for reciprocal) SHRINKING — scar-reopen mix tell")
        if cur["nco_ann_pct"] is not None and cur["nco_ann_pct"] > 0.60:
            flags.append(f"FLAG WAL: bank-level NCOs annualized {cur['nco_ann_pct']}% > 0.60% bar (unadjusted basis — check whether fraud/NDFI-related; any single such loss >$25M = exit-review)")
    else:
        if cur["cd_conc_pct_rbc"] is not None and cur["cd_conc_pct_rbc"] > 115:
            flags.append(f"FLAG FSBW: C&D concentration {cur['cd_conc_pct_rbc']}% of RBC > 115% red bar")
        if prior and cur["retail_dep_musd"] and prior["retail_dep_musd"] and \
           cur["retail_dep_musd"] < 0.95 * prior["retail_dep_musd"]:
            flags.append(f"FLAG FSBW: RETAIL deposits (DEP-BRO proxy) -{round(100 - 100*cur['retail_dep_musd']/prior['retail_dep_musd'], 1)}% seq > 5% runoff trigger")
        if cur["acl_pct_loans"] is not None and cur["nco_ann_pct"] is not None and \
           cur["acl_pct_loans"] < 1.10 and cur["nco_ann_pct"] > 0.5:
            flags.append(f"FLAG FSBW: ACL {cur['acl_pct_loans']}% < 1.10% while NCOs {cur['nco_ann_pct']}% > 0.5% (red-added)")
    return flags


def main():
    DATA.mkdir(parents=True, exist_ok=True)
    state = json.loads(STATE.read_text()) if STATE.exists() else {}
    now = datetime.datetime.now().isoformat(timespec="seconds")
    out = {"ts": now, "banks": {}}
    flags, new_data = [], False

    fsbw_cert = resolve_cert("1st Security Bank of Washington", "Mountlake Terrace", state)
    banks = [("WAL", 57512, wal_metrics), ("FSBW", fsbw_cert, fsbw_metrics)]

    for name, cert, mfn in banks:
        if cert is None:
            out["banks"][name] = {"status": "DATA MISSING", "detail": "cert unresolved (ambiguous or API down)"}
            continue
        rows, err = fetch_quarters(cert)
        if rows is None:
            out["banks"][name] = {"status": "DATA MISSING", "detail": err}
            continue
        cur, prior = mfn(rows[0]), (mfn(rows[1]) if len(rows) > 1 else None)
        last_seen = state.get("last_repdte", {}).get(name)
        fresh = last_seen != cur["repdte"]
        if fresh:
            new_data = True
            state.setdefault("last_repdte", {})[name] = cur["repdte"]
            grade(name, cur, prior, flags)
        out["banks"][name] = {"status": "ok", "cert": cert, "fresh_quarter": fresh,
                              "latest": cur, "prior": prior}

    out["flags"] = flags
    state["last_run"] = now
    STATE.write_text(json.dumps(state, indent=1))
    if new_data or not HISTORY.exists():
        with HISTORY.open("a") as f:
            f.write(json.dumps(out) + "\n")

    print(f"[bank_callreport] {now}")
    for name, b in out["banks"].items():
        if b.get("status") != "ok":
            print(f"  {name}: DATA MISSING — {b.get('detail')}")
            continue
        c = b["latest"]
        tag = "NEW QUARTER" if b["fresh_quarter"] else f"no new call report; latest = {c['repdte']}"
        print(f"  {name} (cert {b['cert']}): {tag}")
        print(f"    {json.dumps(c)}")
        if b["prior"]:
            print(f"    prior: {json.dumps(b['prior'])}")
    for fl in flags:
        print(f"  {fl}")
    if not flags:
        print("  no kill bars tripped on the latest call reports")
    print("  unserved fields (named): reciprocal CDARS/ICS balances (DEPINS = insured-total proxy); holdco nonaccrual/HFI + TCE (bank-level data only); per-loan construction charge-off attribution (8-K only)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
