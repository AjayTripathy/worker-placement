"""narrate — add a spoken voiceover to a demo recording, from its cue timeline.

Part of the reproducible demo pipeline (dev tooling, macOS): demo_recorder emits
`<video>.cues.json` (phase -> seconds); this tool synthesizes one narration
segment per cue with the system TTS (`say`), schedules each at its cue time
(never overlapping the previous segment), and muxes audio + video into an mp4
with a full ffmpeg (imageio-ffmpeg). Re-record → re-narrate → same command, so
the narrated demo regenerates on every release like everything else.

    python3 -m officekit.narrate --video cold_start_walkthrough.webm \\
        --out cold_start_narrated.mp4
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

VOICE = "Samantha"
RATE = 190          # words/min

# cue label -> what the narrator says while that phase plays
SCRIPT = {
    "land": "This is officekit — an open-source family office. A new user, starting cold.",
    "holdings": "Holdings go in ticker by ticker — or a statement upload does it in one shot. "
                "Funds classify into sleeves; concentrated stock splits out automatically.",
    "sleeves": "Then, what no statement shows: home, mortgage, cash.",
    "income": "Income becomes an asset — capitalized earnings, with a beta.",
    "goals": "Goals: retirement, spending, a liquidity floor.",
    "build": "One click.",
    "office": "The office builds — net worth, every sleeve with its risks and betas, each goal scored today. Unknowns stay tagged.",
    "scenarios": "The Scenario Planner stresses everything — crashes, rate shocks, even an income shock.",
    "cards": "Each scenario is a card: forecast probability, tripwires, and a costed playbook scored to your profile.",
    "goals_tail": "Every goal, re-scored through every tail.",
    "strategies": "Mitigations link to strategies — the sleeves you run and the sleeves you could, with honest statuses.",
    "closing": "Your data stays in a folder you own. Read-only — it never places orders.",
}


def _ffmpeg():
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def _duration(path):
    out = subprocess.run(["afinfo", str(path)], capture_output=True, text=True).stdout
    mm = re.search(r"estimated duration:\s*([\d.]+)", out)
    return float(mm.group(1)) if mm else 0.0


def narrate(video, out, cues_path=None, voice=VOICE, rate=RATE):
    video = Path(video)
    cues_path = Path(cues_path) if cues_path else video.with_suffix(".cues.json")
    cues = json.loads(cues_path.read_text(encoding="utf-8"))
    work = video.parent / f".{video.stem}_narration"
    work.mkdir(exist_ok=True)

    # synthesize each segment, then schedule: at its cue, but never on top of the
    # previous segment (a late segment slides later; the visuals can carry it)
    segs = []
    prev_end = 0.0
    for label, t in cues:
        text = SCRIPT.get(label)
        if not text:
            continue
        clip = work / f"{label}.aiff"
        subprocess.run(["say", "-v", voice, "-r", str(rate), "-o", str(clip), text], check=True)
        start = max(float(t) + 0.25, prev_end + 0.35)
        dur = _duration(clip)
        segs.append((clip, start, dur))
        prev_end = start + dur

    ff = _ffmpeg()
    cmd = [ff, "-y", "-loglevel", "error", "-i", str(video)]
    for clip, _, _ in segs:
        cmd += ["-i", str(clip)]
    delays = "".join(f"[{i+1}:a]adelay={int(s*1000)}|{int(s*1000)}[a{i}];"
                     for i, (_, s, _) in enumerate(segs))
    mix = "".join(f"[a{i}]" for i in range(len(segs)))
    cmd += ["-filter_complex",
            f"{delays}{mix}amix=inputs={len(segs)}:duration=longest:normalize=0[aout]",
            "-map", "0:v", "-map", "[aout]",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "medium", "-crf", "21",
            "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(out)]
    subprocess.run(cmd, check=True)
    for clip, _, _ in segs:
        clip.unlink(missing_ok=True)
    work.rmdir()
    return Path(out)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="officekit.narrate", description=__doc__.splitlines()[0])
    ap.add_argument("--video", required=True, help="recorded demo (webm)")
    ap.add_argument("--cues", help="cue timeline JSON (default: <video>.cues.json)")
    ap.add_argument("--out", default="narrated.mp4")
    ap.add_argument("--voice", default=VOICE)
    args = ap.parse_args(argv)
    out = narrate(args.video, args.out, cues_path=args.cues, voice=args.voice)
    print(f"[narrate] {out} ({out.stat().st_size/1e6:.1f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
