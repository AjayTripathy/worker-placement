"""pz2_hype_watch — continuous pre/post-launch telemetry for Planet Zoo 2 (the FDEV T1/T2 gates).

Principal directive 2026-08-04: pre-binary commitment is acceptable WITH a measured hype edge —
so the hype leg of the FDEV two-signal gate gets a daily instrument, not a weekly eyeball.

PRE-LAUNCH MODE (until 2026-10-13):
  - Steam most-wishlisted RANK (the industry-standard pre-launch demand indicator; PZ2 was #158
    at first read 2026-08-04). Signals: TOP-60 = the T1 gate's hype leg TRUE (alert; T1 may stage
    once the ~09-10 audited accounts also print clean); rank > 200 any day, or outside top-100
    at T-7 (2026-10-06), = WARNING (alert).
  - Steam announcement cadence (store news count) as a secondary.
  - Followers/Reddit legs blocked (SteamDB 403 / Reddit 403) — manual only, noted not faked.
POST-LAUNCH MODE (from 2026-10-13):
  - Daily review count + % positive from the PZ2 store page → the LAUNCH POSITIVE-RATE LADDER
    graded against Frontier's own 4-point history (PC1 94.6 / PZ1 87.8 / RoR 67.1 / PC2 59.3):
    >=85% BULL / 78-85 BASE / 70-78 WARN / <=67 BEAR-CONFIRMED. The 2026-10-15 read = the T2
    gate + the accelerated impairment tripwire. Emails via desk/mailer on ladder resolution and
    any threshold crossing. (Volume is SECONDARY by design: the review-count pace bar would have
    passed the reference flop — PC2 had 4,499 reviews at day 14.)
State: desk/data/pz2_hype/state.json + history.jsonl. Registry: daily, enabled:True.
"""
from __future__ import annotations

import datetime
import json
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / "desk" / "data" / "pz2_hype"
DIR.mkdir(parents=True, exist_ok=True)
STATE = DIR / "state.json"
HIST = DIR / "history.jsonl"
UA = {"User-Agent": "Mozilla/5.0 (desk research; contact 4tripathy@gmail.com)",
      "Cookie": "birthtime=568022401; wants_mature_content=1"}
LAUNCH = datetime.date(2026, 10, 13)
T_MINUS7 = datetime.date(2026, 10, 6)
LADDER = [(85.0, "BULL"), (78.0, "BASE"), (70.0, "WARN"), (0.0, "BEAR-CONFIRMED")]


def _get(url: str) -> str:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def _load() -> dict:
    if STATE.exists():
        return json.loads(STATE.read_text())
    return {"appid": None, "alerts_fired": []}


def _alert(st: dict, key: str, subject: str, body: str) -> None:
    if key in st["alerts_fired"]:
        return
    st["alerts_fired"].append(key)
    print(f"ALERT [{key}]: {subject}")
    try:
        from desk.mailer import send_raw
        send_raw(subject, body)
    except Exception as ex:
        print(f"  (mail failed: {ex})\n{body}")


def resolve_appid(st: dict) -> int | None:
    if st.get("appid"):
        return st["appid"]
    try:
        js = json.loads(_get("https://store.steampowered.com/api/storesearch/?term=Planet%20Zoo%202&l=english&cc=US"))
        for item in js.get("items", []):
            if item.get("name", "").strip().lower() == "planet zoo 2":
                st["appid"] = item["id"]
                return item["id"]
        if js.get("items"):
            st["appid"] = js["items"][0]["id"]
            print(f"[warn] exact name not found; using first hit {js['items'][0]['name']} ({st['appid']})")
            return st["appid"]
    except Exception as ex:
        print(f"appid resolve failed: {ex}")
    return None


def wishlist_rank(appid: int) -> int | None:
    """PZ2's position on the most-wishlisted chart (server-rendered; walk pages until found)."""
    for start in range(0, 500, 50):
        try:
            html = _get(f"https://store.steampowered.com/search/?filter=popularwishlist&start={start}")
        except Exception as ex:
            print(f"wishlist page {start} failed: {ex}")
            return None
        ids = re.findall(r"data-ds-appid=\"(\d+)\"", html)
        if str(appid) in ids:
            return start + ids.index(str(appid)) + 1
    return None  # outside top 500


def review_read(appid: int) -> tuple[int, float] | None:
    """Post-launch: total review count + % positive from the appreviews endpoint."""
    try:
        js = json.loads(_get(f"https://store.steampowered.com/appreviews/{appid}?json=1&language=all&purchase_type=all&num_per_page=0"))
        q = js.get("query_summary", {})
        tot = q.get("total_reviews", 0)
        pos = q.get("total_positive", 0)
        if tot:
            return tot, 100.0 * pos / tot
    except Exception as ex:
        print(f"review read failed: {ex}")
    return None


def main() -> None:
    today = datetime.date.today()
    now = datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z"
    st = _load()
    appid = resolve_appid(st)
    row = {"ts": now, "mode": "post" if today >= LAUNCH else "pre"}
    if not appid:
        row["error"] = "appid unresolved — DATA MISSING, not zero"
        print(row["error"])
    elif today < LAUNCH:
        rank = wishlist_rank(appid)
        row["wishlist_rank"] = rank
        if rank is None:
            print(f"[{now}] PZ2 wishlist rank: OUTSIDE TOP 500 (or fetch gap)")
            _alert(st, "outside500", "PZ2 HYPE WARNING: outside wishlist top-500",
                   "Pre-launch demand signal has collapsed or the fetch broke — verify manually. FDEV T1 gate leg 2 = FAIL state.")
        else:
            print(f"[{now}] PZ2 wishlist rank: #{rank}")
            if rank <= 60:
                _alert(st, "top60", "PZ2 HYPE: TOP-60 — FDEV T1 hype leg TRUE",
                       f"PZ2 wishlist rank #{rank} <= 60. T1 (0.375% GTC <=435p) may stage ONCE the audited accounts "
                       f"(~09-10) also print clean. Two-signal gate per the 08-04 restructure. Pack FDEV|2026-09-30.")
            if rank > 200:
                _alert(st, "gt200", "PZ2 HYPE WARNING: rank > 200",
                       f"PZ2 slipped to #{rank}. Warning leg fired — bear weight review; no T1 staging.")
            if today >= T_MINUS7 and rank > 100:
                _alert(st, "tminus7", "PZ2 HYPE WARNING: outside top-100 at T-7",
                       f"#{rank} one week before launch — the strongest pre-launch warning we defined. No T1.")
    else:
        rr = review_read(appid)
        if rr:
            tot, pct = rr
            row["reviews"], row["pct_positive"] = tot, round(pct, 1)
            grade = next(g for thr, g in LADDER if pct >= thr)
            row["ladder"] = grade
            print(f"[{now}] PZ2 reviews {tot} @ {pct:.1f}% positive → LADDER: {grade}")
            if today >= datetime.date(2026, 10, 15) and "ladder_verdict" not in st["alerts_fired"]:
                _alert(st, "ladder_verdict", f"PZ2 LADDER VERDICT: {grade} ({pct:.1f}% on {tot} reviews)",
                       f"The 10-15 read. >=85 BULL -> T2 arms (chase-cap 530p) · 78-85 BASE -> T2 half "
                       f"· 70-78 WARN -> no T2, T1 review · <=67 BEAR-CONFIRMED -> T1 exit-review + "
                       f"accelerated impairment tripwire. Volume secondary BY DESIGN (PC2 had 4,499 reviews at day 14 and flopped).")
        else:
            print(f"[{now}] post-launch review read unavailable")
    with HIST.open("a") as f:
        f.write(json.dumps(row) + "\n")
    STATE.write_text(json.dumps(st, indent=1))


if __name__ == "__main__":
    main()
