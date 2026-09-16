"""Onboarding walkthrough VIDEO — an integration test that records the real
onboarding end to end, using the PRINCIPAL'S OWN DATA, and saves a narrated GIF
(principal-directed 2026-09-07).

It drives the actual serve HTTP surface in a headless browser (playwright), so
every frame is the real rendered product, not a mock:

  1. Landing — drop a statement or scan a broker
  2. Import the live Morgan Stanley Prime bundle -> positions land in the form to review
  3. Add the off-book items (mortgage, GOOG, the $5M CA gain) and Build the office
  4. The office dashboard — sleeves, factor betas, liquidity
  5. Scenario Planner — every goal through the tail

Output: officekit/media/onboarding_walkthrough.gif (committed asset). Skips
cleanly when the bundle or a browser isn't available (CI), so it only ever
records on a machine that actually has the data.
"""
import threading
import time
import urllib.parse
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "officekit" / "media" / "onboarding_walkthrough.gif"
VIEW = {"width": 1200, "height": 780}
BAND = 68                                    # caption strip height (px)


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


def _post(url, fields):
    body = urllib.parse.urlencode(fields).encode()
    req = urllib.request.Request(url, data=body,
                                 headers={"Content-Type": "application/x-www-form-urlencoded"})
    try:
        urllib.request.build_opener(_NoRedirect).open(req, timeout=60).read()
    except urllib.error.HTTPError:
        pass                                 # a 303 is expected (PRG)


def _nw(folder):
    from officekit import build_model, load_balance_sheet
    return build_model(load_balance_sheet(folder / "balance_sheet.json", strict=False))["NW"]


def _font(size):
    from PIL import ImageFont
    for p in ("/System/Library/Fonts/Supplemental/Arial.ttf",
              "/System/Library/Fonts/Helvetica.ttc",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _frame(png_bytes, step, total, caption):
    """Compose a screenshot under a captioned title strip -> one PIL frame."""
    import io

    from PIL import Image, ImageDraw
    shot = Image.open(io.BytesIO(png_bytes)).convert("RGB")
    w = shot.width
    canvas = Image.new("RGB", (w, shot.height + BAND), (14, 17, 22))
    canvas.paste(shot, (0, BAND))
    d = ImageDraw.Draw(canvas)
    d.rectangle([0, 0, w, BAND], fill=(14, 17, 22))
    d.line([0, BAND - 1, w, BAND - 1], fill=(52, 199, 143), width=2)     # emerald rule
    d.text((22, 14), f"{step}/{total}", font=_font(20), fill=(52, 199, 143))
    d.text((72, 12), "Worker Placement", font=_font(22), fill=(236, 240, 244))
    d.text((72, 40), caption, font=_font(16), fill=(150, 160, 172))
    return canvas


@pytest.fixture
def server(tmp_path):
    from officekit_adapters import morgan_stanley as ms
    if ms.newest_bundle() is None:
        pytest.skip("no Morgan Stanley bundle in ~/Downloads — nothing to record")
    from officekit import serve
    # pre-seed discovery so the onboarding page shows the (real) MS adapter ready
    serve._DISCOVERY_CACHE["results"] = [{
        "name": "morgan_stanley_bundle",
        "label": "Morgan Stanley Prime Brokerage (statement bundle)", "kind": "file",
        "found": True, "status": "ready",
        "detail": f"newest {ms.newest_bundle().name}", "guidance": None, "can_fetch": True}]
    serve._DISCOVERY_CACHE["ts"] = time.time()
    srv = ThreadingHTTPServer(("127.0.0.1", 0), serve.make_handler(tmp_path))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    time.sleep(0.2)
    yield f"http://127.0.0.1:{srv.server_address[1]}", tmp_path
    srv.shutdown()


def test_record_onboarding_walkthrough(server):
    base, folder = server
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        pytest.skip("playwright not installed")

    frames, durations = [], []

    def shot(pg, path="/", settle=1100):
        pg.goto(base + path, wait_until="networkidle", timeout=30000)
        pg.wait_for_timeout(settle)              # let the iframe/dashboard paint
        return pg.screenshot()

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=True)
        except Exception as e:
            pytest.skip(f"no browser for playwright: {e}")
        pg = browser.new_page(viewport=VIEW)

        # 1 — the landing page
        frames.append(_frame(shot(pg, "/"), 1, 5,
                             "Drop a statement or scan your broker to start."))
        durations.append(3200)

        # 2 — import the real MS Prime bundle: positions land in the form to REVIEW
        _post(f"{base}/adapter/import", {"adapter": "morgan_stanley_bundle"})
        from officekit.serve import staged_prefill
        prefill, _ = staged_prefill(folder)
        frames.append(_frame(shot(pg, "/"), 2, 5,
                             f"Imported {len(prefill)} positions — review them, add what a "
                             f"connection can't see, then Build."))
        durations.append(4000)

        # 3 — add the off-book items alongside the import and BUILD the office
        fields = [("account", "Parametric"), ("owner", "")]
        for kind, name, value, rate, *_ in prefill:
            fields += [("u_kind", kind), ("u_name", str(name)), ("u_value", str(value)), ("u_rate", "")]
        fields += [
            ("u_kind", "real_estate_debt"), ("u_name", "Home mortgage (fixed)"),
            ("u_value", "720000"), ("u_rate", "5.75"),
            ("u_kind", "ticker"), ("u_name", "GOOG"), ("u_value", "652738.74"), ("u_rate", ""),
            ("wind_amount", "5000000"), ("wind_eta", "Dec"), ("wind_character", "ltcg"),
            ("wind_state", "CA"), ("wind_rate", ""), ("goal_taxharvest", "1")]
        _post(f"{base}/onboard", fields)
        assert (folder / "balance_sheet.json").exists(), "Build did not produce an office"
        nw = _nw(folder)
        frames.append(_frame(shot(pg, "/"), 3, 5,
                             f"Built: the Parametric book + $720k mortgage + GOOG + a $5M CA gain "
                             f"(auto tax-reserved). NW ${nw:,.0f}."))
        durations.append(4600)

        # 4 — the office dashboard, factor betas and liquidity
        frames.append(_frame(shot(pg, "/pages/office.html"), 4, 5,
                             "Your full financial world — every sleeve, its risks, how they move together."))
        durations.append(3600)

        # 5 — the payoff surface: goals through the tail
        frames.append(_frame(shot(pg, "/pages/scenarios.html"), 5, 5,
                             "Every goal stress-tested through the tail — the Scenario Planner."))
        durations.append(3600)

        browser.close()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(OUT, save_all=True, append_images=frames[1:],
                   duration=durations, loop=0, optimize=True)

    assert OUT.exists() and OUT.stat().st_size > 20_000, "walkthrough GIF not written"
    assert len(frames) == 5
    # the office really carries the off-book items (the video isn't a mock)
    from officekit import load_balance_sheet
    d = load_balance_sheet(folder / "balance_sheet.json", strict=False)
    assert any(s["category"] == "real_estate_debt" for s in d["sleeves"])
    assert d.get("tax_model", {}).get("rate_ltcg") == pytest.approx(0.371, abs=1e-6)
    print(f"\nsaved {OUT} ({OUT.stat().st_size//1024} KB, {len(frames)} frames)")
