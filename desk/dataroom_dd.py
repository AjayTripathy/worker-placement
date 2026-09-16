"""dataroom_dd — one-shot pipeline: property data room in, verified analyst brief out.

Born from the 2100 Woods Lane run (2026-08-07): ten interactive turns, of which only four
steps were irreducibly human (price arrives socially; PRA signature; auth-walled portals;
the verdict). The rest was deterministic and is now THIS pipeline:

  stage 1  INVENTORY    unzip/walk the room; classify files by folder+name; date-span map;
                        flag scanned PDFs (no text layer) for visual read
  stage 2  EXTRACT      pdftotext sweeps of conclusion/recommendation/constraint sections
                        from every text-bearing PDF
  stage 3  VERIFY       the external battery, all public endpoints proven live 2026-08-07:
                          - Census geocoder -> coords + INCORPORATED-PLACE jurisdiction
                          - FEMA NFHL      -> flood zone at point
                          - CAL FIRE FHSZ  -> fire hazard zone at point
                          - USGS NHD       -> stream courses + culvert connectors on-site
                          - county parcels -> APN tie-out (adapter registry; SCC wired)
  stage 4  DRAFT        render the brief skeleton: inventory + extraction + verification
                        table PRE-FILLED, Mode A/Mode B/verdict slots left as TODO
  stage 5  BENCH (opt)  --bench dispatches the Mode A/B analysis through the headless
                        claude -p transport (court_runner pattern); adjudication stays
                        a session job (generator-never-grades-itself)
  stage 6  RENDER       pandoc + headless Chrome -> PDF next to the .md

  python3 -m desk.dataroom_dd <zip-or-dir> --address "2100 Woods Lane, Los Altos, CA" \
      [--apns 342-04-078,342-04-089] [--county scc] [--bench] [--out dd_reports/]

Irreducibly human, by design: ask price, records-request signatures, auth-walled portals
(flagged in the brief with exact next actions), and the final verdict.
"""
from __future__ import annotations

import datetime
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

DOC_CLASSES = {
    "geotech": r"geotech|soils|boring",
    "environmental": r"phase\s*1|riparian|habitat|biolog|CEQA|wetland",
    "civil/site": r"civil|site.?plan|grading|topo|elevation|survey",
    "entitlement": r"fire.?comment|approval|permit|resolution|tentative|application",
    "financial": r"proforma|feasibil|comps|budget|model",
    "legal/title": r"title|prelim|easement|purchase|agreement|LOI",
}


def _curl(url: str, timeout: int = 25) -> str:
    r = subprocess.run(["curl", "-sL", "--max-time", str(timeout), url, "-A", UA],
                       capture_output=True, text=True)
    return r.stdout


def inventory(room: Path) -> dict:
    files = [p for p in room.rglob("*") if p.is_file()]
    inv = {"n_files": len(files), "classes": {}, "scanned_pdfs": [], "date_tokens": {}}
    for p in files:
        rel = str(p.relative_to(room))
        cls = next((c for c, pat in DOC_CLASSES.items() if re.search(pat, rel, re.I)), "other")
        inv["classes"].setdefault(cls, []).append(rel)
        for y in re.findall(r"(20[0-2]\d)", rel):
            inv["date_tokens"][y] = inv["date_tokens"].get(y, 0) + 1
    return inv


def extract(room: Path, max_pdfs: int = 60) -> dict:
    """Conclusion/constraint sections from text-bearing PDFs; scanned ones flagged."""
    out, scanned = {}, []
    pdfs = sorted(room.rglob("*.pdf")) + sorted(room.rglob("*.PDF"))
    for p in pdfs[:max_pdfs]:
        try:
            t = subprocess.run(["pdftotext", "-layout", str(p), "-"],
                               capture_output=True, text=True, timeout=60).stdout
        except Exception:
            continue
        if len(t.strip()) < 200:
            scanned.append(str(p.relative_to(room)))
            continue
        hits = []
        for kw in ("conclusion", "recommend", "constraint", "not approved", "denied",
                   "jurisdictional", "listed species", "material weakness", "going concern"):
            for m in list(re.finditer(kw, t, re.I))[:2]:
                s = max(0, m.start() - 150)
                hits.append(" ".join(t[s:m.start() + 320].split())[:420])
        if hits:
            out[str(p.relative_to(room))] = hits[:6]
    return {"extracts": out, "scanned_needing_visual_read": scanned}


def verify_address(address: str) -> dict:
    v = {"address": address}
    street, rest = address.split(",", 1)
    city = rest.split(",")[0].strip()
    g = _curl("https://geocoding.geo.census.gov/geocoder/geographies/address?"
              f"street={street.strip().replace(' ', '+')}&city={city.replace(' ', '+')}"
              "&state=CA&benchmark=Public_AR_Current&vintage=Current_Current&format=json")
    try:
        m = json.loads(g)["result"]["addressMatches"][0]
        x, y = m["coordinates"]["x"], m["coordinates"]["y"]
        v["matched"] = m["matchedAddress"]
        v["coords"] = (x, y)
        for k, items in m["geographies"].items():
            if "Incorporated" in k and items:
                v["jurisdiction"] = items[0].get("NAME")
    except Exception as e:
        v["geocode_error"] = str(e)
        return v
    try:
        f = json.loads(_curl(
            "https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/identify?"
            f"geometry={x},{y}&geometryType=esriGeometryPoint&sr=4326&layers=all:28&tolerance=2"
            f"&mapExtent={x-.01},{y-.01},{x+.01},{y+.01}&imageDisplay=400,400,96"
            "&returnGeometry=false&f=json"))
        rs = f.get("results", [])
        v["flood"] = ({k: rs[0]["attributes"].get(k) for k in ("FLD_ZONE", "ZONE_SUBTY", "SFHA_TF")}
                      if rs else "no flood layer at point")
    except Exception as e:
        v["flood"] = f"FEMA error: {e}"
    try:
        fz = json.loads(_curl(
            "https://egis.fire.ca.gov/arcgis/rest/services/FHSZ/FHSZ_SRA_LRA_Combined/"
            f"MapServer/0/query?geometry={x},{y}&geometryType=esriGeometryPoint&inSR=4326"
            "&spatialRel=esriSpatialRelIntersects&outFields=*&returnGeometry=false&f=json"))
        fs = fz.get("features", [])
        v["fire_hazard"] = (fs[0]["attributes"] if fs else "no mapped FHSZ at point")
    except Exception as e:
        v["fire_hazard"] = f"CALFIRE error: {e}"
    try:
        nh = json.loads(_curl(
            "https://hydro.nationalmap.gov/arcgis/rest/services/nhd/MapServer/6/query?"
            f"geometry={x-.004},{y-.003},{x+.004},{y+.003}&geometryType=esriGeometryEnvelope"
            "&inSR=4326&spatialRel=esriSpatialRelIntersects&outFields=gnis_name,fcode"
            "&returnGeometry=false&f=json"))
        v["streams_on_or_near"] = [
            {"name": f["attributes"].get("gnis_name"), "fcode": f["attributes"].get("fcode"),
             "note": {46007: "intermittent stream", 46006: "perennial stream",
                      33400: "CONNECTOR (culvert/pipe — existing crossing)"}.get(
                          f["attributes"].get("fcode"), "")}
            for f in nh.get("features", [])]
    except Exception as e:
        v["streams_on_or_near"] = f"NHD error: {e}"
    return v


COUNTY_PARCELS = {
    "scc": ("https://services2.arcgis.com/tcv2cMrq63AgvbHF/arcgis/rest/services/"
            "Parcels_Public_View/FeatureServer/0/query?where=APNdashed IN ({apns})"
            "&outFields=*&returnGeometry=false&f=json"),
}


def verify_parcels(apns: list[str], county: str = "scc") -> list[dict]:
    tpl = COUNTY_PARCELS.get(county)
    if not tpl:
        return [{"error": f"no parcel adapter for county '{county}' — add to COUNTY_PARCELS"}]
    q = tpl.format(apns=",".join(f"'{a}'" for a in apns)).replace(" ", "%20")
    try:
        d = json.loads(_curl(q))
        return [f["attributes"] for f in d.get("features", [])]
    except Exception as e:
        return [{"error": str(e)}]


def render_pdf(md: Path):
    html = Path("/tmp") / (md.stem + ".html")
    subprocess.run(["pandoc", str(md), "-o", str(html), "--standalone", "--embed-resources",
                    "--metadata", f"title={md.stem}", "-c", str(ROOT / "dd_reports/public/style.css")],
                   capture_output=True)
    subprocess.run(["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                    "--headless", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={md.with_suffix('.pdf')}", f"file://{html}"],
                   capture_output=True)


def run(room_path: str, address: str, apns: list[str], county: str, out_dir: str,
        bench: bool = False) -> Path:
    src = Path(room_path).expanduser()
    if src.suffix == ".zip":
        room = Path("/tmp") / ("dataroom_" + src.stem.replace(" ", "_"))
        room.mkdir(exist_ok=True)
        with zipfile.ZipFile(src) as z:
            z.extractall(room)
    else:
        room = src
    inv = inventory(room)
    ext = extract(room)
    ver = verify_address(address)
    par = verify_parcels(apns, county) if apns else []
    today = datetime.date.today().isoformat()
    name = re.sub(r"[^A-Za-z0-9]+", "_", address.split(",")[0]).strip("_").upper()
    md = Path(out_dir) / f"{name}_DATAROOM_BRIEF_{today}.md"
    lines = [f"# Data-Room DD Brief — {address}",
             f"*Machine pass {today}: stages 1-3 automated; Mode A/B analysis and verdict are "
             f"bench/session work (marked TODO). Human-only items listed at bottom.*\n",
             "## Stage 1 — Inventory",
             f"- {inv['n_files']} files; year tokens: " +
             ", ".join(f"{y}×{n}" for y, n in sorted(inv["date_tokens"].items())),
             *(f"- **{c}** ({len(fs)}): " + "; ".join(fs[:4]) + ("…" if len(fs) > 4 else "")
               for c, fs in sorted(inv["classes"].items())),
             "\n## Stage 3 — External verification (live public endpoints)",
             f"- Jurisdiction (Census): **{ver.get('jurisdiction', 'GEOCODE FAILED')}** ({ver.get('matched','')})",
             f"- Flood (FEMA NFHL): {json.dumps(ver.get('flood'))}",
             f"- Fire (CAL FIRE FHSZ): {json.dumps(ver.get('fire_hazard'))[:200]}",
             f"- Hydrography (NHD): {json.dumps(ver.get('streams_on_or_near'))[:400]}",
             "- Parcel tie-out: " + (json.dumps(par, indent=1) if par else "no APNs supplied"),
             "\n## Stage 2 — Extracted conclusions/constraints (per document)"]
    for f, hits in list(ext["extracts"].items())[:25]:
        lines.append(f"\n**{f}**")
        lines += [f"> {h}" for h in hits[:3]]
    if ext["scanned_needing_visual_read"]:
        lines.append("\n**Scanned PDFs needing visual read (no text layer):** " +
                     "; ".join(ext["scanned_needing_visual_read"][:10]))
    lines += ["\n## TODO — bench/session work",
              "- [ ] Mode A: claims table (room vs its own documents)",
              "- [ ] Mode B: disconfirming pass (what the room implies by what it omits)",
              "- [ ] Aerial + topo visual read (access geometry)",
              "- [ ] Verdict + decision framework (needs ask price)",
              "\n## Human-only items",
              "- Ask price (arrives socially) · records-request signature (PRA) · "
              "auth-walled portals (assessor owner/values; planning portal) · final verdict"]
    md.write_text("\n".join(lines))
    if bench:
        try:
            from desk.court_runner import _dispatch, MODEL_COURT
            prompt = (f"Two-mode data-room DD for {address}. The machine brief (inventory, "
                      f"extractions, external verification) follows. Produce the Mode A claims "
                      f"table and Mode B disconfirming findings in plain language, flagging "
                      f"UNVERIFIABLE explicitly. ≥1 citation to a named room document per claim."
                      f"\n\n{md.read_text()[:60000]}")
            res = _dispatch(prompt, MODEL_COURT)
            if res.get("text"):
                md.write_text(md.read_text() + "\n\n## Bench pass (headless)\n\n" + res["text"])
        except Exception as e:
            md.write_text(md.read_text() + f"\n\n*Bench dispatch failed: {e}*")
    render_pdf(md)
    return md


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("room")
    ap.add_argument("--address", required=True)
    ap.add_argument("--apns", default="")
    ap.add_argument("--county", default="scc")
    ap.add_argument("--out", default=str(ROOT / "dd_reports"))
    ap.add_argument("--bench", action="store_true")
    a = ap.parse_args()
    p = run(a.room, a.address, [x.strip() for x in a.apns.split(",") if x.strip()], a.county,
            a.out, bench=a.bench)
    print(f"brief: {p}\npdf:   {p.with_suffix('.pdf')}")
