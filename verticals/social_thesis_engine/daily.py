"""daily — the social-thesis engine's daily cycle (cron entrypoint). READ-ONLY: surfaces &
paper-tracks candidates, NEVER places an order.

1) triage   — social feed -> conditioning + IV richness -> decision matrix -> log + diligence queue
2) score    — stamp realized-vol-vs-implied on any matured rows (forward paper track record)
3) diligence— run the signalos-quant-analyst pass on queued candidates (if claude CLI present)
"""
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))


def main():
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"\n===== SOCIAL-THESIS DAILY {stamp} =====")
    try:
        import triage
        res = triage.run(top_n=int(sys.argv[1]) if len(sys.argv) > 1 else 10)
        nq = len(res.get("queue", []))
    except Exception:
        traceback.print_exc(); nq = 0
    try:
        import score_log
        score_log.run()
    except Exception:
        traceback.print_exc()
    if nq:
        try:
            import run_diligence
            run_diligence.run()
        except Exception:
            traceback.print_exc()
    print("===== done — staging/monitoring only; no orders =====")


if __name__ == "__main__":
    main()
