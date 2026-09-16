"""EDGAR S-1 figure extractor — fetches embedded images for figure-level DD.

Why this exists
---------------
S-1 / F-1 filings commonly convey quantitative claims ONLY through figures
(waterfall plots, swim plots, Kaplan-Meier curves, market-share charts, mineral
resource maps, customer-mix donuts) WITHOUT an accompanying data table. The
chart is the disclosure; the underlying numbers live in pixel-space.

A DD agent that text-greps the S-1 misses these. This helper closes that gap:
given a figure reference, it returns a local PNG path that the agent can Read
directly via Claude's multimodal capability.

The pattern recurred across the 2026-05-29 top-30 IPO batch (Parabilis
waterfall, Sunshine Silver resource map, SpaceX Starlink subscriber chart,
Quantinuum qubit roadmap, etc.) — same R/M asymmetry where R is in pixels.
This helper makes figure-level reading a one-call operation rather than a
per-agent re-derivation.

Usage
-----
    from verticals.buyside_dd.edgar_figure_extractor import extract_figure

    path = extract_figure(
        cik="1657677",
        accession="0001193125-26-230994",
        s1_html_path="/path/to/s1.htm",
        figure_number=10,
    )
    # `path` is now a downsized PNG ready for Read.

Notes
-----
- EDGAR Archives requires SEC fair-access UA (Company Name + admin email).
- GIF/JPEG/PNG images from EDGAR can exceed the Read tool's 2000x2000 px limit;
  this module always downsizes the longest edge to 1800 px and saves as PNG.
- The figure→image mapping uses a "nearest <img> tag" heuristic since EDGAR
  S-1 HTML doesn't tag figures by number. Heuristic is: the <img> immediately
  preceding "Figure N:" caption text, falling back to the <img> immediately
  following it.
"""
from __future__ import annotations

import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Optional

HEADERS = {
    "User-Agent": "Signal OS DD Pipeline ajay@example.com",
    "Accept": "image/gif,image/jpeg,image/png,*/*",
}

EDGAR_ARCHIVES = "https://www.sec.gov/Archives/edgar/data/{cik}/{acc_nodash}/"


def _http_get(url: str, timeout: int = 30, retries: int = 3) -> Optional[bytes]:
    import time
    delay = 1.0
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < retries - 1:
                time.sleep(delay)
                delay *= 2
                continue
            if e.code == 404:
                return None
            print(f"  HTTP error {url[:80]}: {e}", file=sys.stderr)
            return None
        except Exception as e:
            print(f"  HTTP error {url[:80]}: {e}", file=sys.stderr)
            return None
    return None


def _accession_no_dashes(acc: str) -> str:
    return acc.replace("-", "")


_IMG_PAT = re.compile(r'src="([^"]+\.(?:jpg|jpeg|png|gif))"', re.IGNORECASE)


def find_figure_image_filename(s1_html: str, figure_number: int) -> Optional[str]:
    """Locate the <img> tag corresponding to "Figure N:" in S-1 HTML.

    Heuristic (validated on Parabilis 2026-05-19 S-1):
      1. Find the caption text "Figure N:" or "Figure N." or "Figure N "
         in the HTML.
      2. Among all <img src="..."> tags, pick the one with the smallest
         byte distance to the caption. Tie-break: prefer the image AFTER the
         caption — EDGAR S-1 HTML typically places the image immediately
         following its caption header (Parabilis Figure 10 caption at byte
         2389366, image at byte 2390026 — only 660 bytes after).
      3. Reject candidates more than 20KB from the caption (likely belong to
         a different figure).
    Returns the image filename (e.g., "img78361224_14.gif") or None.
    """
    cap_pat = re.compile(rf"Figure\s+{figure_number}[:\.\s]", re.IGNORECASE)
    m = cap_pat.search(s1_html)
    if not m:
        return None
    pos = m.start()
    candidates = []
    for im in _IMG_PAT.finditer(s1_html):
        delta = im.start() - pos  # negative if before, positive if after
        if abs(delta) > 20000:
            continue
        # Sort key: prefer "just after" caption — small positive deltas first,
        # then small negative deltas.
        if delta >= 0:
            key = (0, delta)
        else:
            key = (1, -delta)
        candidates.append((key, im.group(1)))
    if not candidates:
        return None
    candidates.sort()
    return candidates[0][1]


def list_all_figures(s1_html: str) -> list[dict]:
    """Return a list of every (figure_number, caption_excerpt, image_filename)
    found in the S-1 HTML. Useful for an agent to know what figures exist.

    Caption excerpt is the first 100 chars after "Figure N:" minus HTML tags."""
    out = []
    for m in re.finditer(r"Figure\s+(\d+)[:\.\s]([^.]{0,180})", s1_html, re.IGNORECASE):
        n = int(m.group(1))
        cap = m.group(2)
        cap = re.sub(r"<[^>]+>", " ", cap)
        cap = re.sub(r"\s+", " ", cap).strip()[:100]
        img = find_figure_image_filename(s1_html, n)
        out.append({"figure_number": n, "caption_excerpt": cap, "image_filename": img})
    return out


def fetch_and_downsize(cik: str, accession: str, image_filename: str,
                       out_dir: str = "/tmp/edgar_figures",
                       max_edge_px: int = 1800) -> Optional[str]:
    """Download an EDGAR image and downsize to max_edge_px on the longest edge.
    Always saves as PNG. Returns the local path or None on failure."""
    try:
        from PIL import Image
    except ImportError:
        print("Pillow not installed — install with: pip3 install Pillow", file=sys.stderr)
        return None
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    cik_int = int(cik.lstrip("0") or "0")
    acc_nodash = _accession_no_dashes(accession.split(":")[0])
    base = EDGAR_ARCHIVES.format(cik=cik_int, acc_nodash=acc_nodash)
    url = base + image_filename
    raw = _http_get(url)
    if not raw:
        return None
    # Save original
    raw_path = Path(out_dir) / image_filename
    raw_path.write_bytes(raw)
    # Open with Pillow, downsize, convert to RGB PNG
    try:
        img = Image.open(raw_path)
        # Convert paletted GIFs / transparent images to RGB on white background
        if img.mode in ("P", "RGBA", "LA"):
            bg = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            bg.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
            img = bg
        elif img.mode != "RGB":
            img = img.convert("RGB")
        img.thumbnail((max_edge_px, max_edge_px), Image.Resampling.LANCZOS)
        png_path = Path(out_dir) / (Path(image_filename).stem + "_resized.png")
        img.save(png_path, "PNG", optimize=True)
        return str(png_path)
    except Exception as e:
        print(f"  Pillow error on {image_filename}: {e}", file=sys.stderr)
        return None


def extract_figure(cik: str, accession: str, s1_html_path: str,
                   figure_number: int, out_dir: str = "/tmp/edgar_figures") -> Optional[dict]:
    """One-shot: load S-1 HTML, find Figure N's image filename, fetch from EDGAR,
    downsize, return {figure_number, caption_excerpt, image_filename, source_url,
    local_path} ready for Read.
    """
    html = Path(s1_html_path).read_text(encoding="utf-8", errors="ignore")
    image_filename = find_figure_image_filename(html, figure_number)
    if not image_filename:
        return {"figure_number": figure_number, "error": "image_filename_not_found"}
    # Caption excerpt for context
    m = re.search(rf"Figure\s+{figure_number}[:\.\s]([^.]{{0,200}})", html, re.IGNORECASE)
    caption = ""
    if m:
        caption = re.sub(r"<[^>]+>", " ", m.group(1))
        caption = re.sub(r"\s+", " ", caption).strip()[:200]
    local_path = fetch_and_downsize(cik, accession, image_filename, out_dir=out_dir)
    if not local_path:
        return {"figure_number": figure_number, "image_filename": image_filename,
                "caption_excerpt": caption, "error": "fetch_or_downsize_failed"}
    cik_int = int(cik.lstrip("0") or "0")
    acc_nodash = _accession_no_dashes(accession.split(":")[0])
    source_url = f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{acc_nodash}/{image_filename}"
    return {
        "figure_number": figure_number,
        "caption_excerpt": caption,
        "image_filename": image_filename,
        "source_url": source_url,
        "local_path": local_path,
    }


if __name__ == "__main__":
    # CLI: python3 -m verticals.buyside_dd.edgar_figure_extractor CIK ACC HTML_PATH FIGURE_N
    if len(sys.argv) < 5:
        print("Usage: python3 -m verticals.buyside_dd.edgar_figure_extractor <CIK> <ACCESSION> <S1_HTML_PATH> <FIGURE_NUMBER>")
        sys.exit(1)
    cik, acc, html_path, fig_n = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
    result = extract_figure(cik, acc, html_path, fig_n)
    print(json.dumps(result, indent=2))
