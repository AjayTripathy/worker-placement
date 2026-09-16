"""demo_recorder — record a scripted walkthrough of a client's office + scenario
pages as a video, in a browser WE own.

Why this exists (2026-09-02): recording through the user's live Chrome is fragile
by construction — the capture inherits their window state (focus, occlusion,
size), and a fully-covered tab paints black frames. A scripted Playwright session
renders off-screen, is immune to all of that, and makes the demo video a
REPRODUCIBLE ARTIFACT: re-run it on every release and the walkthrough regenerates.

Dev tooling, not part of the core engine: requires `playwright` (+ its bundled
Chromium) at runtime only. The core package keeps its zero-dependency guarantee.

    python3 -m officekit.demo_recorder --office maya_office.html \\
        --scenarios maya_scenarios.html --out walkthrough.webm

The choreography: office top -> risk/cash -> goals -> sleeve cards -> beta matrix
-> agent lanes, then the scenario planner top -> scenario list -> heatmap ->
playbook (switching the client-profile lens live) -> liquidity map -> goals
through the tail (the life-event column) -> microstructure effects.
"""
from __future__ import annotations

import argparse
import shutil
import time
from pathlib import Path

VIEWPORT = {"width": 1440, "height": 900}
SCROLL_SETTLE = 1.6          # seconds to rest on each stop (becomes watchable pacing)


def _smooth_to(page, y, settle=SCROLL_SETTLE):
    page.evaluate(f"window.scrollTo({{top: {int(y)}, behavior: 'smooth'}})")
    time.sleep(settle)


def _section_tops(page):
    """h2 section label -> absolute y, measured from the live page."""
    rows = page.evaluate(
        "[...document.querySelectorAll('h2')].map(e => "
        "[e.textContent.trim(), Math.round(e.getBoundingClientRect().top + scrollY)])")
    return {t: y for t, y in rows}


def _walk_sections(page, stop_offset=90, dwell=SCROLL_SETTLE):
    for _, y in sorted(_section_tops(page).items(), key=lambda kv: kv[1]):
        _smooth_to(page, max(y - stop_offset, 0), dwell)


def record(office_html, scenarios_html, out_path, headless=True):
    from playwright.sync_api import sync_playwright   # dev-only dependency

    out_path = Path(out_path)
    workdir = out_path.parent / f".{out_path.stem}_frames"
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=headless)
        ctx = browser.new_context(viewport=VIEWPORT, record_video_dir=str(workdir),
                                  record_video_size=VIEWPORT)
        page = ctx.new_page()

        # ---- office page ----
        page.goto(Path(office_html).resolve().as_uri())
        page.wait_for_load_state("networkidle")
        time.sleep(2.2)                                   # hold the header + inbox
        _smooth_to(page, 480)                             # risk summary + liquidity
        _walk_sections(page)                              # goals, assets, matrices, lanes

        # ---- scenario planner ----
        page.goto(Path(scenarios_html).resolve().as_uri())
        page.wait_for_load_state("networkidle")
        time.sleep(2.2)                                   # worst-case stat tiles
        tops = _section_tops(page)
        for label, y in sorted(tops.items(), key=lambda kv: kv[1]):
            _smooth_to(page, max(y - 90, 0))
            if label.startswith("Playbook"):              # switch the client lens live
                sel = page.locator("#profileSel")
                if sel.count():
                    time.sleep(0.6)
                    sel.select_option("lev")
                    time.sleep(1.4)
                    sel.select_option("acc")
                    time.sleep(0.8)
            if label.startswith("Goals through the tail"):
                time.sleep(1.8)                           # linger on the life-event column
        time.sleep(1.5)

        ctx.close()                                       # flushes the video
        video_path = Path(page.video.path())
        browser.close()

    out_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(video_path), out_path)
    shutil.rmtree(workdir, ignore_errors=True)
    return out_path


def _type(page, selector, text, delay=42):
    """Human-paced typing (reads as a person on video, not a paste)."""
    page.click(selector)
    page.type(selector, str(text), delay=delay)


def _frame(page):
    """The app shell's content iframe."""
    for f in page.frames:
        if f != page.main_frame:
            return f
    return page.main_frame


def _frame_smooth_to(frame, y, settle=SCROLL_SETTLE):
    frame.evaluate(f"window.scrollTo({{top: {int(y)}, behavior: 'smooth'}})")
    time.sleep(settle)


def _frame_sections(frame):
    rows = frame.evaluate(
        "[...document.querySelectorAll('h2')].map(e => "
        "[e.textContent.trim(), Math.round(e.getBoundingClientRect().top + scrollY)])")
    return rows


def record_cold_start(base_url, csv_path, out_path, headless=True):
    """A NEW user, cold: land on the empty app, fill the onboarding form (CSV
    upload, home/mortgage/cash, income, goals, profile), submit, then PLAY —
    browse the office, flip to the Scenario Planner, switch the client lens,
    linger on goals-through-the-tail."""
    from playwright.sync_api import sync_playwright

    out_path = Path(out_path)
    workdir = out_path.parent / f".{out_path.stem}_frames"
    cues = []                                          # (label, seconds-from-video-start)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=headless)
        ctx = browser.new_context(viewport=VIEWPORT, record_video_dir=str(workdir),
                                  record_video_size=VIEWPORT)
        page = ctx.new_page()
        t0 = time.monotonic()                          # video capture starts with the page

        def mark(label):
            cues.append((label, round(time.monotonic() - t0, 2)))

        def reveal(selector, settle=0.7):
            page.eval_on_selector(selector,
                                  "e => e.scrollIntoView({behavior:'smooth', block:'center'})")
            time.sleep(settle)

        # ---- cold landing: the streamlined onboarding form (no name, defaults on) ----
        page.goto(base_url)
        page.wait_for_load_state("networkidle")
        mark("land")
        time.sleep(4.6)
        mark("holdings")
        # ONE holdings table: tickers (classified) and named assets side by side
        rows = [("ticker", "SCHB", "120000", ""), ("ticker", "VTEB", "45000", ""),
                ("ticker", "TSLA", "30000", ""),
                ("real_estate", "Home", "750000", ""),
                ("real_estate_debt", "Mortgage (5.9% fixed)", "380000", "5.9"),
                ("cash", "Cash / HYSA", "60000", "")]
        for i, (kind, name, value, rate) in enumerate(rows):
            page.locator('select[name=u_kind]').nth(i).select_option(kind)
            page.locator('input[name=u_name]').nth(i).type(name, delay=22)
            page.locator('input[name=u_value]').nth(i).type(value, delay=24)
            if rate:
                page.locator('input[name=u_rate]').nth(i).type(rate, delay=24)
            time.sleep(0.25)
        time.sleep(0.8)
        if csv_path:                                    # …then UPLOAD the statement export too
            page.eval_on_selector('input[name=positions_csv]',
                                  "e => e.scrollIntoView({behavior:'smooth', block:'center'})")
            time.sleep(0.9)
            page.set_input_files('input[name=positions_csv]', str(csv_path))
            time.sleep(1.8)
        time.sleep(1.0)                                 # narration room

        mark("income")
        reveal('input[name=income_annual]')             # income as an asset
        _type(page, 'input[name=income_annual]', "280000", delay=26)
        _type(page, 'input[name=income_years]', "25", delay=26)
        page.select_option('select[name=income_style]', "equity_linked")
        time.sleep(2.2)                                 # narration room

        mark("goals")
        reveal('input[name=ret_date]')                  # goals
        _type(page, 'input[name=ret_date]', "2052-01-01", delay=20)
        _type(page, 'input[name=ret_spend]', "110000", delay=26)
        _type(page, 'input[name=floor_amount]', "50000", delay=26)
        time.sleep(1.3)                                 # narration room

        reveal('button[type=submit]', 0.9)
        mark("build")
        page.click('button[type=submit]')               # build my office ->
        page.wait_for_load_state("networkidle")
        mark("office")
        time.sleep(3.2)                                 # the office appears

        # ---- play: office page ----
        f = _frame(page)
        _frame_smooth_to(f, 480)
        for _, y in sorted(_frame_sections(f), key=lambda r: r[1])[:4]:
            _frame_smooth_to(f, max(y - 90, 0), 1.4)

        # ---- play: scenario planner ----
        mark("scenarios")
        page.click("#t_scenarios")
        page.wait_for_load_state("networkidle")
        time.sleep(3.4)
        f = _frame(page)
        for label, y in sorted(_frame_sections(f), key=lambda r: r[1]):
            _frame_smooth_to(f, max(y - 90, 0), 1.3)
            if label.startswith("Scenarios"):
                mark("cards")
                sel = f.locator("#profileSel")     # switch the client lens live
                if sel.count():
                    time.sleep(0.5)
                    sel.select_option("lev")
                    time.sleep(1.2)
                    sel.select_option("acc")
                    time.sleep(0.6)
                cards = f.locator("details.scard summary")
                for i in (1, 2):                   # click cards open: probability, tripwires, playbook
                    if cards.count() > i:
                        cards.nth(i).click()
                        time.sleep(0.6)
                        cards.nth(i).scroll_into_view_if_needed()
                        time.sleep(1.6)
            if label.startswith("Goals through the tail"):
                mark("goals_tail")
                time.sleep(2.0)

        # ---- play: click a mitigation through to its STRATEGY card ----
        _frame_smooth_to(f, 0, 1.2)                     # back to the open worst card
        link = f.locator('a[href*="strat-"]').first
        if link.count():
            link.scroll_into_view_if_needed()
            time.sleep(0.9)
            link.click()                                # lands on strategies.html#strat-… (card opens)
            mark("strategies")
            time.sleep(2.4)
            f = _frame(page)
            for _, y in sorted(_frame_sections(f), key=lambda r: r[1]):
                _frame_smooth_to(f, max(y - 90, 0), 1.5)
            more = f.locator("#strat-harvest_engine summary")
            if more.count():                            # open one more strategy by hand
                mark("closing")
                more.scroll_into_view_if_needed()
                time.sleep(0.6)
                more.click()
                time.sleep(2.6)
        time.sleep(2.0)

        ctx.close()
        video_path = Path(page.video.path())
        browser.close()

    out_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(video_path), out_path)
    shutil.rmtree(workdir, ignore_errors=True)
    import json as _json
    out_path.with_suffix(".cues.json").write_text(_json.dumps(cues, indent=1))
    return out_path


def record_goal_flow(base_url, out_path, headless=True):
    """The goal->strategy flow, on an EXISTING office: open the goals editor,
    add goals from the sample chips, save — then watch the strategies page
    where each goal has decomposed into a sized, QUEUED strategy proposal with
    'mandated by your goal' on its trail. Assumes the serve folder is
    pre-built (goals editor needs an office to edit)."""
    from playwright.sync_api import sync_playwright

    out_path = Path(out_path)
    workdir = out_path.parent / f".{out_path.stem}_frames"
    cues = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=headless)
        ctx = browser.new_context(viewport=VIEWPORT, record_video_dir=str(workdir),
                                  record_video_size=VIEWPORT)
        page = ctx.new_page()
        t0 = time.monotonic()

        def mark(label):
            cues.append((label, round(time.monotonic() - t0, 2)))

        # ---- the office, as it stands: goals scored today ----
        page.goto(base_url)
        page.wait_for_load_state("networkidle")
        mark("office")
        time.sleep(3.0)
        f = _frame(page)
        for label, y in _frame_sections(f):
            if label.startswith("Goals"):
                _frame_smooth_to(f, max(y - 90, 0), 2.2)
                break

        # ---- open the editor, add two goals from the sample chips ----
        mark("editor")
        ed = f.locator('details:has(form#goalform) > summary')
        ed.scroll_into_view_if_needed()
        time.sleep(0.8)
        ed.click()
        time.sleep(1.8)                                  # chips + existing rows visible
        mark("chips")
        for chip in ("College fund", "Sabbatical year"):
            c = f.locator(f'.gchip:has-text("{chip}")')
            c.scroll_into_view_if_needed()
            time.sleep(0.7)
            c.click()                                    # prefills a row: kind, label, $, date
            time.sleep(1.9)
        time.sleep(1.0)
        mark("save")
        f.locator('#goalform .gbtn').scroll_into_view_if_needed()
        time.sleep(0.8)
        f.locator('#goalform .gbtn').click()             # save -> decompose -> rebuild
        time.sleep(3.0)

        # ---- the office re-scored: new goals on the board ----
        mark("rescored")
        f = _frame(page)                                 # fresh page after the redirect
        for label, y in _frame_sections(f):
            if label.startswith("Goals"):
                _frame_smooth_to(f, max(y - 90, 0), 2.6)
                break

        # ---- strategies: each goal became a queued, sized proposal ----
        mark("strategies")
        page.click("#t_strategies")
        page.wait_for_load_state("networkidle")
        time.sleep(2.8)
        f = _frame(page)
        opened = 0
        for sid in ("muni", "bonds", "core_equity", "cash_mgmt"):
            card = f.locator(f"#strat-{sid} summary")
            if not card.count():
                continue
            card.scroll_into_view_if_needed()
            time.sleep(0.8)
            card.click()                                 # open: target %, note, mandate trail
            mark(f"card_{sid}")
            time.sleep(3.2)                              # linger on 'mandated by your goal'
            opened += 1
            if opened == 3:
                break
        time.sleep(2.2)

        ctx.close()
        video_path = Path(page.video.path())
        browser.close()

    out_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(video_path), out_path)
    shutil.rmtree(workdir, ignore_errors=True)
    import json as _json
    out_path.with_suffix(".cues.json").write_text(_json.dumps(cues, indent=1))
    return out_path


def record_ai_onboarding(base_url, out_path, headless=True):
    """AI onboarding, live: the chat panel elicits the balance sheet and goals
    in conversation (the agent FILLS THE FORM VISIBLY), the user reviews and
    builds, the AI-1 classification confirm step catches unknown tickers, and
    the office lands with goals already decomposed into queued strategies.
    Requires the serve process to be running WITH a usable intake/classify
    slot (key in the server env) — replies are real model calls, so pacing
    waits on the chat log rather than fixed sleeps."""
    from playwright.sync_api import sync_playwright

    out_path = Path(out_path)
    workdir = out_path.parent / f".{out_path.stem}_frames"
    cues = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=headless)
        ctx = browser.new_context(viewport=VIEWPORT, record_video_dir=str(workdir),
                                  record_video_size=VIEWPORT)
        page = ctx.new_page()
        t0 = time.monotonic()

        def mark(label):
            cues.append((label, round(time.monotonic() - t0, 2)))

        def reveal(selector, settle=0.8):
            page.eval_on_selector(selector,
                                  "e => e.scrollIntoView({behavior:'smooth', block:'center'})")
            time.sleep(settle)

        def chat(msg, label, scope="assets"):
            log = f"chatlog_{scope}"
            n0 = page.evaluate(f"document.getElementById('{log}').children.length")
            reveal(f'#chatin_{scope}', 0.5)
            page.click(f'#chatin_{scope}')
            page.type(f'#chatin_{scope}', msg, delay=24)
            time.sleep(0.7)
            page.keyboard.press("Enter")
            # the agent's reply is a real model call — wait on the log, not a timer
            page.wait_for_function(
                f"document.getElementById('{log}').children.length >= {n0 + 2}",
                timeout=180_000)
            mark(label)
            time.sleep(2.6)

        page.goto(base_url)
        page.wait_for_load_state("networkidle")
        mark("land")
        time.sleep(3.4)                                   # the chat panel invites

        chat("We have about 520k at Vanguard: 400k in VTI, 45k in QQQJ, 40k in FLOT, "
             "and 35k cash. Our home is worth about 1.2M with a 480k mortgage at 5.8% fixed.",
             "chat_assets")
        reveal('#holdings', 1.0)                          # the agent filled the table, visibly
        time.sleep(3.2)

        chat("I also make 260k a year in tech — figure 20 more years of it. That's all the assets.",
             "chat_income")
        reveal('input[name=income_annual]', 1.0)
        time.sleep(2.0)

        # one ticker the user types by hand — an unknown symbol, so the
        # AI-1 classification confirm step has something to catch on camera
        # (the chat agent classifies funds it recognizes on its own)
        reveal('#holdings', 0.8)
        kinds = page.locator('select[name=u_kind]')
        idx = next((i for i in range(kinds.count()) if not kinds.nth(i).input_value()), None)
        if idx is None:                                  # agent filled every row — add one
            page.evaluate("addURow()")
            time.sleep(0.5)
            idx = page.locator('select[name=u_kind]').count() - 1
        page.locator('select[name=u_kind]').nth(idx).select_option("ticker")
        page.locator('input[name=u_name]').nth(idx).type("SUB", delay=40)
        page.locator('input[name=u_value]').nth(idx).type("25000", delay=30)
        time.sleep(1.2)

        # goals are their OWN conversation — the goals chatbox fills the
        # goal fields above it; assets are off-limits in that scope
        chat("Retire around 2052 spending 120k a year, a 300k college fund for 2038, "
             "and keep a 50k cash floor.", "chat_goals_scope", scope="goals")
        reveal('input[name=ret_date]', 1.0)
        time.sleep(2.4)

        reveal('button[type=submit]', 0.9)
        mark("build")
        page.click('button[type=submit]')
        page.wait_for_load_state("networkidle")
        time.sleep(1.2)

        # AI-1: unknown tickers -> the classification CONFIRM step (human accepts)
        if page.locator('input[name=answers_json]').count():
            mark("confirm")
            time.sleep(4.2)                               # read the suggestions + confidences
            page.click('button[type=submit]')
            page.wait_for_load_state("networkidle")
        mark("office")
        time.sleep(3.2)

        f = _frame(page)
        for label, y in _frame_sections(f):
            if label.startswith("Goals"):                 # scored + '-> served by' coverage
                _frame_smooth_to(f, max(y - 90, 0), 3.0)
                break

        mark("strategies")                                # goals already decomposed + queued
        page.click("#t_strategies")
        page.wait_for_load_state("networkidle")
        time.sleep(2.6)
        f = _frame(page)
        opened = 0
        for sid in ("core_equity", "bonds", "muni", "cash_mgmt"):
            card = f.locator(f"#strat-{sid} summary")
            if not card.count():
                continue
            card.scroll_into_view_if_needed()
            time.sleep(0.7)
            card.click()
            mark(f"card_{sid}")
            time.sleep(3.0)
            opened += 1
            if opened == 2:
                break
        time.sleep(2.0)

        ctx.close()
        video_path = Path(page.video.path())
        browser.close()

    out_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(video_path), out_path)
    shutil.rmtree(workdir, ignore_errors=True)
    import json as _json
    out_path.with_suffix(".cues.json").write_text(_json.dumps(cues, indent=1))
    return out_path


def record_loop_close(base_url, out_path, headless=True):
    """The taxonomy, on camera: goal card -> the OFFERED strategy menu ->
    Adopt click -> the adopted strategy's courted assets (verdicts pre-run
    live pre-roll; Opus deliberation is minutes) -> click through to a full
    pitch deck -> back -> Record purchase -> IMPLEMENTED -> the goal's
    coverage line carries real value."""
    from playwright.sync_api import sync_playwright

    out_path = Path(out_path)
    workdir = out_path.parent / f".{out_path.stem}_frames"
    cues = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=headless)
        ctx = browser.new_context(viewport=VIEWPORT, record_video_dir=str(workdir),
                                  record_video_size=VIEWPORT)
        page = ctx.new_page()
        t0 = time.monotonic()

        def mark(label):
            cues.append((label, round(time.monotonic() - t0, 2)))

        # 1 · the goal, scored on the office
        page.goto(base_url)
        page.wait_for_load_state("networkidle")
        mark("office_goal")
        time.sleep(2.4)
        f = _frame(page)
        for label, y in _frame_sections(f):
            if label.startswith("Goals"):
                _frame_smooth_to(f, max(y - 90, 0), 2.6)
                break

        # 2 · the taxonomy: the goal OFFERS a handful of strategies
        mark("menu")
        page.click("#t_strategies")
        page.wait_for_load_state("networkidle")
        time.sleep(3.2)                                  # read the offered menu + why-lines

        # 3 · Adopt the primary
        f = _frame(page)
        adopt = f.locator('form[action="/strategy/goal-adopt"] button').first
        adopt.scroll_into_view_if_needed()
        time.sleep(1.0)
        mark("adopt")
        adopt.click()
        page.wait_for_load_state("networkidle")
        time.sleep(2.6)                                  # adopted: assets + verdicts appear

        # 4 · the courted assets, each with its deck — click one through
        f = _frame(page)
        f.eval_on_selector("details[id^=goal-]", "e => e.open = true")
        time.sleep(1.2)
        mark("assets")
        deck_link = f.locator('a[href^="deck_"]').last   # the WATCH-graded pick
        deck_link.scroll_into_view_if_needed()
        time.sleep(1.6)
        deck_link.click()
        page.wait_for_load_state("networkidle")
        mark("deck")
        time.sleep(2.8)                                  # verdict banner + adjudication
        for yy in (600, 1300, 2100):
            _frame_smooth_to(_frame(page), yy, 2.0)      # rationale, red brief, blue brief
        _frame(page).locator("a").first.click()          # back to the strategy
        page.wait_for_load_state("networkidle")
        time.sleep(1.4)

        # 5 · the implementation door
        f = _frame(page)
        f.eval_on_selector("details[id^=goal-]", "e => e.open = true")
        time.sleep(1.0)
        mark("purchase")
        form = f.locator('form[action="/holdings"]').first
        form.scroll_into_view_if_needed()
        time.sleep(0.8)
        form.locator('input[name=symbol]').type("IBMT", delay=40)
        form.locator('input[name=amount]').type("8000", delay=30)
        time.sleep(0.8)
        form.locator("button").click()
        page.wait_for_load_state("networkidle")
        time.sleep(2.0)

        # 6 · implemented + the goal's coverage carries real value
        f = _frame(page)
        f.eval_on_selector("details[id^=goal-]", "e => e.open = true")
        mark("implemented")
        time.sleep(3.2)
        mark("coverage")
        page.click("#t_office")
        page.wait_for_load_state("networkidle")
        time.sleep(1.8)
        f = _frame(page)
        for label, y in _frame_sections(f):
            if label.startswith("Goals"):
                _frame_smooth_to(f, max(y - 90, 0), 3.6)
                break
        time.sleep(1.2)

        ctx.close()
        video_path = Path(page.video.path())
        browser.close()

    out_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(video_path), out_path)
    shutil.rmtree(workdir, ignore_errors=True)
    import json as _json
    out_path.with_suffix(".cues.json").write_text(_json.dumps(cues, indent=1))
    return out_path


def main(argv=None):
    ap = argparse.ArgumentParser(prog="officekit.demo_recorder",
                                 description=__doc__.splitlines()[0])
    ap.add_argument("--office", help="rendered office page (html) — static-pages mode")
    ap.add_argument("--scenarios", help="rendered scenario-planner page (html) — static-pages mode")
    ap.add_argument("--cold-start", help="serve-app base URL — record a NEW user onboarding + playing")
    ap.add_argument("--goal-flow", help="serve-app base URL with a PRE-BUILT office — record the goal->strategy decomposition flow")
    ap.add_argument("--ai-onboarding", help="serve-app base URL (server running WITH a key) — record chat onboarding + classify confirm")
    ap.add_argument("--loop-close", help="serve-app base URL with a PRE-BUILT office incl. a court verdict — record goal->court->purchase->coverage")
    ap.add_argument("--csv", help="optional: positions CSV the cold-start user uploads; omit to TYPE holdings (the honest cold path)")
    ap.add_argument("--out", default="walkthrough.webm", help="output video (.webm)")
    ap.add_argument("--headed", action="store_true", help="watch it record (debugging)")
    args = ap.parse_args(argv)
    if args.loop_close:
        out = record_loop_close(args.loop_close, args.out, headless=not args.headed)
    elif args.ai_onboarding:
        out = record_ai_onboarding(args.ai_onboarding, args.out, headless=not args.headed)
    elif args.goal_flow:
        out = record_goal_flow(args.goal_flow, args.out, headless=not args.headed)
    elif args.cold_start:
        out = record_cold_start(args.cold_start, args.csv, args.out, headless=not args.headed)
    else:
        if not (args.office and args.scenarios):
            ap.error("either --cold-start URL --csv PATH, or --office + --scenarios")
        out = record(args.office, args.scenarios, args.out, headless=not args.headed)
    print(f"[demo_recorder] video -> {out} ({out.stat().st_size/1e6:.1f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
