"""render_imports — the import audit page (principal-directed 2026-09-05).

One page answering two questions with no digging:
  1. What import integrations exist, and when did each last pull?
  2. For any asset: which source supplies it, does it refresh itself, and
     how stale is it?

Three sections: INTEGRATIONS (live adapters — auto-refresh), DOCUMENTS
(uploaded statements — manual refresh, with their reconciliation warnings
shown, never buried), and the ASSET SOURCE MAP (the deduped union, one row
per asset, source + refresh mode + as-of). Anything typed by hand carries no
source — that IS the trace: manual data refreshes only when a human does.
"""
from __future__ import annotations

import re
from datetime import date, datetime

from officekit.fmt import esc
from officekit.render_signals import CSS, _page
from officekit.staging import num


def import_slug(source_id):
    """Stable page slug for one import source — 'adapter:ibkr_socket' ->
    'import_adapter-ibkr-socket'. Used for both the link and the page filename so
    a row on the imports page and its detail page always agree."""
    s = re.sub(r"[^a-z0-9]+", "-", str(source_id).lower()).strip("-")
    return "import_" + (s or "x")


def _link(source_id, label):
    return f'<a href="/pages/{import_slug(source_id)}.html">{label}</a>'


def _age_days(stamp, today=None):
    if not stamp:
        return None
    try:
        dt = datetime.fromisoformat(str(stamp).replace("Z", "+00:00"))
        d = dt.astimezone().date() if dt.tzinfo else dt.date()
        return max(0, ((today or date.today()) - d).days)
    except ValueError:
        return None


def _age_html(stamp, today=None):
    a = _age_days(stamp, today)
    if a is None:
        return '<span class="h-NEVER_RUN">—</span>'
    cls = "h-OK" if a <= 1 else ("h-STALE" if a <= 30 else "h-ERROR")
    return f'<span class="{cls}">{a}d</span>'


_BUSY = ("onsubmit=\"var b=this.querySelector('button');b.textContent='\u23f3 pulling\u2026';"
         "setTimeout(function(){b.disabled=true},0)\"")


def render_imports(discover_results, ledger, merged, overlaps, today=None,
                   key_status=None, pull_endpoint=None, reconciliation=None, upload_html=""):
    """discover_results: officekit_adapters.discover() output (or []);
    ledger: staging.ledger(folder); merged: staging.merged_rows(folder)[0];
    key_status: the AI key treated as an integration; pull_endpoint enables
    per-integration Pull-now buttons."""
    from officekit.runtime import hosted
    connection_note = ("Use Re-pull to refresh cloud connections. Desktop sources update through your local app when office sync is enabled."
                       if hosted() else "Connected sources refresh daily while the app runs. Setup details and timestamps live on each source page.")
    by_source = {r["source_id"]: r for r in ledger}

    # 0 — the AI key IS an integration: where it came from, or how to attach one
    key_row = ""
    if key_status is not None:
        ok = key_status.get("attached")
        key_row = (f'<tr><td><b>AI model key</b><details><summary>Key details</summary><div class="sub">{esc(key_status["label"])}</div></details></td>'
                   f'<td class="{"h-OK" if ok else "h-STALE"}">{"attached" if ok else "needs attaching"}</td>'
                   f'<td>manual</td><td class="mono">—</td><td class="mono">—</td><td>—</td></tr>')

    # 1 — integrations: every registered adapter, live status + last pull + pull-now
    rows, available = [], []
    for a in discover_results or []:
        led = by_source.get(f"adapter:{a['name']}")
        pull = ""
        # Show a re-pull button for ANY fetchable connection (or one pulled
        # before) — NOT gated on the cached status. The pull itself connects
        # live and re-probes, so a stale "absent" never hides the button
        # (2026-09-09). It flashes an error only if the source is truly down.
        if pull_endpoint and ((a.get("can_fetch") and a.get("found") and a.get("status") == "ready") or led):
            label = "Re-pull" if led else "Pull now"
            pull = (f'<form method="POST" action="{esc(pull_endpoint)}" style="margin:4px 0 0" {_BUSY}>'
                    f'<input type="hidden" name="adapter" value="{esc(a["name"])}">'
                    f'<input type="hidden" name="back" value="imports">'
                    f'<button type="submit" style="background:var(--violet);color:#0b0e12;border:0;'
                    f'border-radius:8px;padding:5px 12px;font-weight:700;cursor:pointer;font-size:12px">'
                    f'{label}</button></form>')
        # clickable when there's a detail page (fetchable adapter or one pulled)
        label_html = (_link(f"adapter:{a['name']}", f'<b>{esc(a["label"])}</b>')
                      if (a.get("can_fetch") or led) else f'<b>{esc(a["label"])}</b>')
        refresh_mode = "auto" if a.get("auto", True) else "manual"
        status = {"ready": "Connected", "absent": "Not connected", "needs_key": "Setup needed", "needs_dep": "Setup needed", "error": "Needs attention"}.get(a["status"], a["status"].replace("_", " ").capitalize())
        setup = (f'<details><summary>Connection details</summary><p class="sub">{esc(a["detail"])}</p></details>')
        if not pull and a.get("can_fetch"):
            setup = f'<a href="/pages/{import_slug("adapter:" + a["name"])}.html">Set up connection →</a>'
        # A connection is ACTIVE if it is ready or has ever imported; everything
        # else is a not-yet-connected provider and belongs under "Add a
        # connection", not in the primary view (2026-09-13, lead with active).
        active = bool(led) or a.get("status") == "ready"
        stamp = (led or {}).get("pulled_utc") or ""
        try:
            imported_at = datetime.fromisoformat(str(stamp).replace("Z", "+00:00"))
            display_date = str(imported_at.astimezone().date() if imported_at.tzinfo else imported_at.date())
        except ValueError:
            display_date = "Not imported"
        row_html = (
            f'<tr><td>{label_html}<div class="sub" style="margin:5px 0">{setup}</div>{pull}</td>'
            f'<td class="{"h-OK" if active else "h-NEVER_RUN"}">{esc(status)}</td>'
            f'<td>{refresh_mode}</td>'
            f'<td class="mono" title="{esc(stamp)}">{esc(display_date)}</td>'
            f'<td class="mono">{(led or {}).get("n_rows", "—")}</td>'
            f'<td>{_age_html((led or {}).get("pulled_utc"), today)}</td></tr>')
        if active:
            # refresh problems (failing / never-imported live connections) lead
            attention = 0 if (a.get("status") == "error" or not stamp) else 1
            rows.append((attention, row_html))
        else:
            available.append(row_html)
    rows.sort(key=lambda r: r[0])
    n_attention = sum(1 for att, _ in rows if att == 0)
    rows_html = key_row + ''.join(h for _, h in rows)
    table_head = '<div class="table-scroll"><table><tr><th>Connection</th><th>Status</th><th>Refresh</th><th>Last import</th><th>Rows</th><th>Age</th></tr>'
    lead_line = connection_note + (' ' + f'<b class="h-STALE">{n_attention} need a refresh or reconnect</b> — shown first.' if n_attention else '')
    integrations = ('<h2>Your connections</h2><p class="sub">' + lead_line + '</p>'
                    + (table_head + rows_html + '</table></div>' if rows or key_row else
                       '<div class="panel">No live connections yet. Add a connection below or upload a statement from Home.</div>'))
    if available:
        integrations += ('<details class="panel" style="margin-top:20px"><summary>Add a connection · '
                         f'{len(available)} available</summary>'
                         '<p class="sub" style="margin:8px 0 0">Providers you can connect but haven\'t yet. '
                         'Open <a href="/settings" target="_top">Office settings</a> to manage your connections; source pages show import details.</p>'
                         + table_head + ''.join(available) + '</table></div></details>')

    # 2 — documents: uploads are manual-refresh sources; warnings shown in full
    docs = [r for r in ledger if r["kind"] == "upload"]
    drows = []
    for d in docs:
        warn = "".join(f'<div class="sub h-STALE">⚠ {esc(w)}</div>' for w in d["warnings"])
        dlabel = _link(d["source_id"], "<b>" + esc(d["ref"]) + "</b>")
        drows.append(
            f'<tr><td>{dlabel}'
            f'<div class="sub">{esc(d["detail"][:80])}</div>{warn}</td>'
            f'<td>manual</td><td class="mono" title="imported {esc(d["pulled_utc"] or "")} UTC">{esc(d.get("as_of") or "?")}</td>'
            f'<td class="mono">{d["n_rows"]}</td>'
            f'<td class="mono">{("$%s" % format(d["stated_total"], ",.0f")) if d.get("stated_total") is not None else "—"}</td>'
            f'<td>{_age_html(d.get("as_of") or d["pulled_utc"], today)}</td></tr>')
    documents = ('<h2>Documents — uploaded statements, refresh only when you re-upload</h2>'
                 '<table><tr><th>document</th><th>refresh</th><th>as-of</th>'
                 '<th>rows</th><th>stated total</th><th>age</th></tr>'
                 + "".join(drows) + "</table>") if drows else ""

    # 2b — proposed: assets born from the app's own deliberation, not a pipeline
    props = [r for r in ledger if r["kind"] == "proposed"]
    prows = []
    for d in props:
        sym = (d.get("source_id") or "").split(":")[-1]
        prows.append(
            f'<tr><td><b>{esc(sym)}</b><div class="sub">{esc(d["ref"])}</div></td>'
            f'<td>{esc(d["detail"])}</td>'
            f'<td class="mono">{esc(d.get("as_of") or "")}</td>'
            f'<td>manual</td>'
            f'<td>{_age_html(d.get("as_of") or d["pulled_utc"], today)}</td></tr>')
    proposed = ('<h2>Proposed — born from a court verdict and a recorded purchase, not a pipeline</h2>'
                '<p class="sub">Provenance is the deliberation itself: the adjudication that proposed '
                'the asset, under which strategy, and when. A later live-connection import of the same '
                'symbol supersedes this row — the proposal became a broker position.</p>'
                '<table><tr><th>asset</th><th>proposed by</th><th>recorded</th>'
                '<th>refresh</th><th>age</th></tr>' + "".join(prows) + "</table>") if prows else ""

    # 3 — the asset source map: an asset can come from MANY sources (the same
    # ticker held in an IBKR account AND a Parametric SMA is 2x exposure, not a
    # dup) — group by asset, total it neatly, and break out each contributing
    # source underneath (principal-directed 2026-09-06).
    over_by_sym = {o["symbol"]: o for o in overlaps or []}
    by_asset = {}
    for r in merged or []:
        sym = str(r.get("symbol") or r.get("description", "?")).upper()
        a = by_asset.setdefault(sym, {"total": 0.0, "src": []})
        a["total"] += num(r.get("value"))
        a["src"].append(r)
    arows = []
    for sym, a in sorted(by_asset.items(), key=lambda kv: -abs(kv[1]["total"])):
        multi = len(a["src"]) > 1
        o = over_by_sym.get(sym)                      # a stale same-account copy was superseded
        superseded = (f'<div class="sub">also in {esc(", ".join(o["displaced"]))} '
                      '— superseded stale copy, freshest won (not double-counted)</div>'
                      if o else "")
        head = (f'<tr><td><b>{esc(sym)}</b>'
                + (f'<span class="sub"> {len(a["src"])} sources</span>' if multi else "")
                + superseded
                + f'</td><td class="mono"><b>{a["total"]:,.0f}</b></td>'
                + (f'<td colspan="4" class="sub">combined across accounts</td>' if multi else
                   f'<td>{esc(a["src"][0].get("source_id",""))}</td>'
                   f'<td>{esc(a["src"][0].get("refresh",""))}</td>'
                   f'<td class="mono">{esc(a["src"][0].get("as_of") or "")}</td>'
                   f'<td>{_age_html(a["src"][0].get("as_of") or a["src"][0].get("pulled_utc"), today)}</td>')
                + "</tr>")
        arows.append(head)
        if multi:                                    # one indented line per contributing source
            for r in sorted(a["src"], key=lambda x: -abs(num(x.get("value")))):
                arows.append(
                    f'<tr><td style="padding-left:20px" class="sub">↳ {esc(str(r.get("account") or "—"))}</td>'
                    f'<td class="mono sub">{num(r.get("value")):,.0f}</td>'
                    f'<td class="sub">{esc(r.get("source_id",""))}</td>'
                    f'<td class="sub">{esc(r.get("refresh",""))}</td>'
                    f'<td class="mono sub">{esc(r.get("as_of") or "")}</td>'
                    f'<td>{_age_html(r.get("as_of") or r.get("pulled_utc"), today)}</td></tr>')
    asset_map = ('<h2>Asset source map — where each number comes from</h2>'
                 '<p class="sub">One line per asset with its combined total; an asset held in '
                 'more than one account breaks out each source beneath it (both counted — that '
                 'is real 2x exposure, not a duplicate). Anything typed by hand appears WITHOUT '
                 'a source — that is the trace: manual data refreshes only when you do.</p>'
                 '<table><tr><th>asset / account</th><th>value</th><th>source</th><th>refresh</th>'
                 '<th>as-of</th><th>age</th></tr>' + "".join(arows) + "</table>") if arows else \
        '<h2>Asset source map</h2><p class="sub">nothing staged yet — import a connection or drop documents on the onboarding page</p>'

    reconciliation_html = ""
    if reconciliation:
        reconciliation_html = ('<h2>Last office reconciliation</h2><p class="sub">'
            f'{reconciliation.get("changed", 0)} updated · {reconciliation.get("added", 0)} added · '
            f'{reconciliation.get("removed", 0)} closed. Closures require complete account coverage and matching control totals.</p>')
        for warning in reconciliation.get("warnings", []):
            reconciliation_html += f'<p class="h-ERROR">{esc(warning)}</p>'
    return _page("Imports",
                 "Keep your balances current. Review connected sources, refresh history and statement dates.",
                 reconciliation_html + integrations + upload_html + documents + proposed + asset_map)


def render_import_detail(title, subtitle, entry, rows, refresh_html,
                         today=None, back_href="/pages/imports.html"):
    """One import's own page: every asset it supplies, totalled (and subtotalled
    by account), with the reconciliation warnings and the refresh control — a
    Re-pull button for a live connection, the full file picker for an upload.

    entry: the ledger dict for this source (kind/refresh/as_of/pulled_utc/
    stated_total/warnings/detail); rows: the raw staged rows; refresh_html: the
    caller-built control (kept out of here to avoid a serve<->render import cycle)."""
    total = sum(num(r.get("value")) for r in rows)
    by_acct = {}
    for r in rows:
        by_acct.setdefault(str(r.get("account") or "—"), 0.0)
        by_acct[str(r.get("account") or "—")] += num(r.get("value"))

    # this page reuses the upload dropzone, whose classes aren't in the signals
    # stylesheet — ship the few it needs inline so the file picker renders right.
    head = ['<style>'
            '.row2{display:flex;flex-wrap:wrap;gap:22px;align-items:flex-start}'
            '.btn2{background:#1a1f25;color:#e8ebee;border:1px solid #2a3038;border-radius:9px;'
            'padding:9px 16px;font-weight:600;cursor:pointer}'
            '.dz{border:2px dashed #2a3038;border-radius:12px;padding:26px 18px;text-align:center;'
            'color:#9aa4b0;cursor:pointer;margin-top:8px}'
            '.dz:hover,.dz.over{border-color:#b1a5ff;background:#1f2530;color:#e8ebee} .dz b{color:#e8ebee}'
            'label{display:block;font-size:11px;color:#9aa4b0;text-transform:uppercase;'
            'letter-spacing:.06em;margin:10px 0 4px}'
            '</style>'
            f'<p><a href="{esc(back_href)}">&larr; all imports</a></p>']

    # reconciliation warnings, never buried
    warns = "".join(f'<div class="sub h-STALE">⚠ {esc(w)}</div>' for w in (entry.get("warnings") or []))
    stated = entry.get("stated_total")
    recon = ""
    if stated is not None:
        diff = total - num(stated)
        cls = "h-OK" if abs(diff) < max(1.0, abs(num(stated)) * 0.005) else "h-STALE"
        recon = (f'<div class="sub">document stated total <b>${num(stated):,.0f}</b> · '
                 f'summed here <b>${total:,.0f}</b> · '
                 f'<span class="{cls}">Δ ${diff:,.0f}</span></div>')

    head.append(
        '<div class="panel">'
        f'<div class="row2"><div><div class="sub">total value</div>'
        f'<div style="font:660 26px/1.1 ui-monospace,Menlo,monospace">${total:,.0f}</div></div>'
        f'<div><div class="sub">assets</div><div class="mono">{len(rows)}</div></div>'
        f'<div><div class="sub">refresh</div><div>{esc(entry.get("refresh") or "—")}</div></div>'
        f'<div><div class="sub">as-of</div><div class="mono">{esc(entry.get("as_of") or "—")}</div></div>'
        f'<div><div class="sub">last pull (UTC)</div><div class="mono">{esc(entry.get("pulled_utc") or "never")}</div></div>'
        f'<div><div class="sub">age</div>{_age_html(entry.get("as_of") or entry.get("pulled_utc"), today)}</div>'
        f'</div><p class="sub">Coverage: {esc((entry.get("snapshot") or {}).get("mode", "partial"))}. '
        f'Only complete, reconciled account coverage can close missing holdings.</p>{recon}{warns}</div>')

    # the refresh control — the caller supplies it WITH its own heading, because
    # the right verb differs by mechanism (pull a live API vs re-add a file).
    if refresh_html:
        head.append(refresh_html)

    # per-account subtotals (only when it spans more than one account)
    if len(by_acct) > 1:
        srows = "".join(f'<tr><td>{esc(a)}</td><td class="mono">${v:,.0f}</td></tr>'
                        for a, v in sorted(by_acct.items(), key=lambda kv: -abs(kv[1])))
        head.append('<h2>Totals by account</h2><table><tr><th>account</th><th>value</th></tr>'
                    + srows + f'<tr><td><b>all accounts</b></td><td class="mono"><b>${total:,.0f}</b></td></tr></table>')

    # every asset in this import
    if rows:
        arows = []
        for r in sorted(rows, key=lambda x: -abs(num(x.get("value")))):
            sym = str(r.get("symbol") or r.get("description") or "—").upper()
            cb = r.get("cost_basis")
            cbcell = f'${num(cb):,.0f}' if cb is not None else "—"
            arows.append(
                f'<tr><td><b>{esc(sym)}</b><div class="sub">{esc((r.get("description") or "")[:60])}</div></td>'
                f'<td class="mono">{num(r.get("qty")):,.0f}</td>'
                f'<td class="mono">${num(r.get("value")):,.0f}</td>'
                f'<td class="mono">{esc(cbcell)}</td>'
                f'<td>{esc(str(r.get("account") or "—"))}</td>'
                f'<td>{esc(str(r.get("sec_type") or "STK"))}</td></tr>')
        head.append('<h2>Assets in this import</h2>'
                    '<table><tr><th>asset</th><th>qty</th><th>value</th><th>cost basis</th>'
                    '<th>account</th><th>type</th></tr>'
                    + "".join(arows)
                    + f'<tr><td><b>total</b></td><td></td><td class="mono"><b>${total:,.0f}</b></td>'
                    '<td></td><td></td><td></td></tr></table>')
    else:
        head.append('<p class="sub">Nothing staged from this source yet — refresh it above.</p>')

    return _page(title, subtitle, "".join(head))
