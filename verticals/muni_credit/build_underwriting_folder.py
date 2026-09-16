"""build_underwriting_folder — one underwriting memo per CUSIP, merged from every evidence stream.

Deterministic and re-runnable: re-run after any new DD lands (e.g. the Phase-2 OS reads) and the
memos refresh. Sources merged per name:
  outputs/BUY_LIST_20260610.json            staged order, limits, phases, dd verdicts
  muni_etf_sleeve_blended.json              insulation/credit/liq/zone/fire fields
  data/issuer_credit/issuer_credit_latest.json   district resolution, AB-1200, seismic, notes
  outputs/buylist_dd/agent{1..7}.json       per-bond 7-point DD records
  outputs/buylist_dd/oid_check.json         original-issue-price verification
  outputs/buylist_dd/cd_scan_p1.json        continuing-disclosure scan (Phase 1)
  outputs/buylist_dd/atwater_os.json        OS deep read (Atwater)
  outputs/buylist_dd/p2_os_reads.json       OS reads (Phase-2 revenue/structure names), if present
  outputs/buylist_dd/av_underwrite.json     levy-base underwrites (Emery, Turlock)
Output: outputs/underwriting/<CUSIP>_<slug>.md + INDEX.md
"""
import json, os, re, datetime

OUT = "outputs/underwriting"
os.makedirs(OUT, exist_ok=True)
TODAY = "2026-06-11"

def jload(p, default=None):
    try: return json.load(open(p))
    except FileNotFoundError: return default

bl = jload("outputs/BUY_LIST_20260610.json")
orders = {o["cusip"]: o for o in bl["orders"]}
sleeve = {b["cusip"]: b for b in jload("muni_etf_sleeve_blended.json")["barbell"]}
ic = {r["cusip"]: r for r in jload("data/issuer_credit/issuer_credit_latest.json", [])}
dd = {}
for i in (1, 2, 3, 4, 5, 6, 7):
    for r in jload(f"outputs/buylist_dd/agent{i}.json", []):
        dd[r["cusip"]] = r
oid = {r["cusip"]: r for r in jload("outputs/buylist_dd/oid_check.json", [])}
cds = {r["cusip"]: r for r in jload("outputs/buylist_dd/cd_scan_p1.json", [])}
atw = jload("outputs/buylist_dd/atwater_os.json")
p2os = {r["cusip"]: r for r in jload("outputs/buylist_dd/p2_os_reads.json", [])}
_av_raw = jload("outputs/buylist_dd/av_underwrite.json", {})
_av_list = _av_raw.get("districts", _av_raw) if isinstance(_av_raw, dict) else _av_raw
av = {}
if isinstance(_av_list, dict):
    for k, v in _av_list.items():
        av[v.get("cusip", k)] = v
else:
    for v in _av_list:
        av[v.get("cusip")] = v

def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", (s or "x").lower()).strip("-")[:36]

def pct(x, d=2):
    return f"{x*100:.{d}f}%" if isinstance(x, (int, float)) and x < 1.5 else (f"{x:.{d}f}%" if isinstance(x, (int, float)) else "—")

index_rows = []
for cu, o in orders.items():
    b = sleeve.get(cu, {}); r = ic.get(cu, {}); d = dd.get(cu, {})
    name = o.get("issuer") or o.get("security") or cu
    md = []
    md.append(f"# {name} — `{cu}`\n")
    md.append(f"*Underwriting memo · compiled {TODAY} · {o['coupon']}% due {o['maturity']} · "
              f"staged ${o['par_to_buy']:,} face, Phase {o['phase']}, limit {o['limit_px']}*\n")
    md.append(f"**Overall: {d.get('verdict','—')}** — {d.get('basis','')}\n")

    md.append("## Security & identity")
    md.append(f"- Pledge: {('CONFIRMED' if d.get('pledge_confirmed') else 'NOT CONFIRMED')} — "
              f"{o.get('security') or ''}; issuer resolved as **{d.get('issuer_resolved') or r.get('district') or '—'}**"
              f" ({o.get('county') or '—'} Co)")
    md.append(f"- Call: {('callable ' + str(d.get('next_call'))) if d.get('callable') else 'non-callable'}")
    md.append(f"- Tax status: **{d.get('tax_status','—')}**\n")

    md.append("## Yield arithmetic (independently recomputed)")
    md.append(f"- Mark {o['last_print_px']} ({o.get('last_trade')}); YTW {pct(o.get('ytw_at_mark'))}; "
              f"after-tax TEY **{pct(o.get('tey_aftertax_at_mark'))}** "
              f"(recomputed {d.get('recomputed_tey_at')}%, divergence {d.get('tey_divergence_pp')}pp)")
    md.append(f"- De-minimis breach: {o.get('demin_breach')}")
    oc = oid.get(cu)
    if oc:
        md.append(f"- Original issue price: **{oc.get('issue_price')}** → {oc.get('classification')} "
                  f"({oc.get('note') or 'see oid_check.json'})")
    md.append("")

    md.append("## Liquidity (MSRB tape)")
    l = o.get("liq") or {}
    md.append(f"- {l.get('n365')} trades/yr · last trade {l.get('days_since_trade')}d ago · "
              f"{l.get('two_sided_days')} two-sided days · realized spread {l.get('px_spread')}pt · "
              f"median block ${l.get('med_block') or 0:,.0f}\n")

    md.append("## Fiscal")
    md.append(f"- AB-1200 interim certification: {d.get('ab1200') or r.get('cert_status') or '—'}")
    a = o.get("av_underwrite") or av.get(cu)
    if a:
        md.append(f"- **Levy-base underwrite ({a.get('verdict')})**: AV/debt {a.get('av_to_debt')}; "
                  f"Teeter {a.get('teeter')}; {a.get('flag')}")
    c = cds.get(cu)
    if c:
        ev = "; ".join(f"{e.get('date','?')} {e.get('type','')}: {e.get('note','')[:80]}" for e in (c.get("event_notices") or [])[:4])
        md.append(f"- Continuing disclosure: **{c.get('status')}** — last annual {c.get('last_annual_filing_date')}"
                  + (f"; notices: {ev}" if ev else ""))
    md.append("")

    osr = (atw if (atw and atw.get("cusip") == cu) else p2os.get(cu))
    if osr:
        md.append("## Official-statement read")
        for k in ("pledge", "lien", "rate_covenant", "dsrf", "abt", "insurance", "issue_price_this_maturity", "adverse_notes"):
            if osr.get(k): md.append(f"- {k.replace('_',' ').title()}: {osr[k]}")
        if osr.get("fiscal_indicators"): md.append(f"- Fiscal indicators: {osr['fiscal_indicators']}")
        md.append(f"- OS verdict: **{osr.get('verdict')}** — {osr.get('basis','')}")
        md.append("")

    md.append("## Hazards & insulation")
    fire = o.get("fire_high_share")
    md.append(f"- Wildfire (FEMA NRI): {(f'{100*fire:.0f}% of district building value in high/very-high tracts' if fire is not None else 'UNVERIFIED / not district-mappable')}"
              + (" — **above 30% threshold, held within the 15% cap**" if (fire or 0) > 0.30 else ""))
    md.append(f"- Seismic: SS {r.get('seismic_ss','—')} · fault zone {o.get('fault_zone') or 'not zone-mapped'}")
    md.append(f"- AI-insulation {b.get('insul','—')} / our credit {b.get('credit','—')}"
              + (f" — {r.get('credit_notes')}" if r.get("credit_notes") else "") + "\n")

    md.append("## Caveats & open items")
    cavs = []
    if (d.get("verdict") == "FLAG"): cavs.append(f"DD flag: {d.get('basis','')[:160]}")
    if c and c.get("status") not in (None, "CLEAN"): cavs.append(f"Disclosure: {c.get('status')} (see above)")
    if fire is None: cavs.append("Fire exposure unverified (treated as unverified, not clean)")
    if str(r.get("cert_status","")).startswith("NOT-COVERED"): cavs.append("Community-college district: AB-1200 regime does not apply; fiscal status partially verified only")
    if not osr and (o.get("security") or "").lower().find("water") >= 0: cavs.append("OS not yet read (Phase-2 read in progress)")
    if not cavs: cavs.append("None outstanding beyond portfolio-level risks (rate shock; see deck caveats)")
    md += [f"- {x}" for x in cavs]
    md.append(f"\n## Sources\nEMMA Security/Details + ContinuingDisclosurePartialView + issue documents (per-CUSIP, {TODAY}); "
              "OpenFIGI; CDE AB-1200 FY24-25 interim rosters; FEMA National Risk Index × NCES GRF25; USGS ASCE7-22; "
              "MSRB trade tape via liquidity_gate. Structured records: outputs/buylist_dd/*.json; cached documents: data/os_cache/.")

    fn = f"{OUT}/{cu}_{slug(name)}.md"
    open(fn, "w").write("\n".join(md))
    index_rows.append((cu, name, o["phase"], d.get("verdict","—"), pct(o.get("tey_aftertax_at_mark")), fn.split("/")[-1]))

# ---- INDEX ----
ix = []
ix.append(f"# Underwriting File — CA Insulated Muni Sleeve\n")
ix.append(f"*{len(index_rows)} names · ${sum(o['par_to_buy'] for o in orders.values()):,} face · compiled {TODAY} · one memo per CUSIP, merged from every verification stream*\n")
ix.append("## The review stack applied to every name")
ix.append("1. Identity (EMMA issue title + OpenFIGI, adjudicated)  ")
ix.append("2. Tax status + AMT (EMMA record)  ")
ix.append("3. Legal pledge vs marketed label (EMMA; OS read for revenue/structure names)  ")
ix.append("4. Call features; original-issue price (OID vs market discount)  ")
ix.append("5. Yield arithmetic recomputed from raw coupon/price/maturity (de-minimis aware)  ")
ix.append("6. Liquidity from the MSRB tape (trades/yr, two-sided days, realized spread, blocks)  ")
ix.append("7. AB-1200 fiscal-stress rosters; levy-base underwrite where concentration was flagged  ")
ix.append("8. Continuing-disclosure history (event notices, redemption risk, filing currency)  ")
ix.append("9. Hazards jointly: FEMA NRI wildfire × USGS seismic × fault-zone caps  \n")
ix.append("| CUSIP | Name | Phase | DD | TEY a-t | Memo |")
ix.append("|---|---|---|---|---|---|")
for cu, name, ph, v, tey, fn in sorted(index_rows, key=lambda x: (x[2], x[0])):
    ix.append(f"| `{cu}` | {name[:38]} | P{ph} | {v} | {tey} | [{fn}]({fn}) |")
ix.append("\n## What the process caught (chronological)")
ix.append("- 29 federally **taxable** bonds excluded from the candidate universe (incl. 2 UC names already in a prior basket)  ")
ix.append("- 5 issuer **misbindings** corrected (one changed county + fault zone; one replacement candidate REJECTED outright as a mislabeled community-college district)  ")
ix.append("- 5 stale **price marks** re-set to the live tape (one would have overpaid ~2.8pt)  ")
ix.append("- 3 high-fire names swapped out at zero yield cost after the wildfire overlay; fire capped in aggregate  ")
ix.append("- Atwater: pledge **stronger** than assumed (gross-revenue first lien, AGM wrap) but **chronic late-audit filer** — caveated, not killed  ")
ix.append("- OID check: after-tax TEY floor **conservative** for all 11 discounts (3 pure market discount, 8 partial OID = small upside)  ")
ix.append("- Emery: office-CRE concentration **real** (48% office AV, flat AV) but debt = 1% of AV (96×) + Teeter — monitor, intact  ")
ix.append("- Turlock SFID: boundary concern **defused** (77% of district AV, 70% residential, 230× coverage)  ")
ix.append("\n*Standing monitors: daily limit re-mark + continuing-disclosure delta watch (cd_monitor.py) over all 25 CUSIPs.*")
open(f"{OUT}/INDEX.md", "w").write("\n".join(ix))
print(f"wrote {len(index_rows)} memos + INDEX.md -> {OUT}/")
