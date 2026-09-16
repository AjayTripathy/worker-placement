"""Compute divergence scores for v3 narrow-screen probe.

Method:
  1. Use the 5 chemistry-intensive control names (SCL, IOSP, KOP, OEC, NGVT)
     to build the "expected" footprint distribution.
  2. For each control, compute log10(rev / n_FRS) — the orders-of-magnitude
     revenue supported per EPA-permitted facility.
  3. For each TARGET name (battery/lithium/specialty-chem claimants),
     compute the same metric and z-score it against the control mean/std.
  4. Flag |z| >= 1.5 as candidate divergence (>1 std below mean = "lighter
     footprint than peers", >1 std above = "more concentrated than peers").

Caveats baked in:
  - SLI has revenue=0, so rev/FRS is undefined. Reported separately with
    the "tenant at Lanxess" explanation.
  - FOR (real estate non-chem) reported as expected-zero baseline.
  - MTW (industrial cranes non-chem) reported to show that even non-chem
    industrials hit FRS heavily — the screen wouldn't be specific to
    chemistry.
"""
from __future__ import annotations

import json
import math
import statistics
from pathlib import Path

HERE = Path(__file__).parent

CONTROLS = {"SCL", "IOSP", "KOP", "OEC", "NGVT"}
TARGETS  = {"AMPX", "EOSE", "LXU", "ASIX", "TROX", "AMSC", "SLI"}
NONCHEM  = {"FOR", "MTW"}


def main():
    rows = json.loads((HERE / "probe_all.json").read_text())
    by_tk = {r["ticker"]: r for r in rows}

    # Build control distribution
    ctrl_log_rev_per_frs = []
    ctrl_log_n_frs = []
    for tk in CONTROLS:
        r = by_tk[tk]
        rpf = r["rev_per_FRS"]
        if rpf and rpf > 0:
            ctrl_log_rev_per_frs.append(math.log10(rpf))
        if r["n_FRS"] > 0:
            ctrl_log_n_frs.append(math.log10(r["n_FRS"]))

    mu_rpf = statistics.mean(ctrl_log_rev_per_frs)
    sd_rpf = statistics.stdev(ctrl_log_rev_per_frs)
    mu_n   = statistics.mean(ctrl_log_n_frs)
    sd_n   = statistics.stdev(ctrl_log_n_frs)

    print("=== Control distribution (chemistry mid-caps) ===")
    print(f"  log10(rev/FRS): mean={mu_rpf:.3f}  std={sd_rpf:.3f}  "
          f"({10**mu_rpf/1e6:.1f}M ± {sd_rpf:.2f}dex)")
    print(f"  log10(n_FRS):   mean={mu_n:.3f}  std={sd_n:.3f}  "
          f"(~{10**mu_n:.1f} facilities ± {sd_n:.2f}dex)")
    print()

    # Score everyone
    results = []
    for tk, r in by_tk.items():
        rpf = r["rev_per_FRS"]
        nfrs = r["n_FRS"]
        rev = r["revenue"]
        bucket = "CTRL" if tk in CONTROLS else "TGT" if tk in TARGETS else "NCHEM"

        z_rpf = None
        if rpf and rpf > 0:
            z_rpf = (math.log10(rpf) - mu_rpf) / sd_rpf
        z_n = None
        if nfrs > 0:
            z_n = (math.log10(nfrs) - mu_n) / sd_n

        # "Revenue-adjusted expected facilities": at chemistry-control mean
        # rev/FRS, a name with revenue R would have R / 10^mu_rpf facilities.
        exp_n = (rev / (10**mu_rpf)) if rev and rev > 0 else None
        ratio = (nfrs / exp_n) if exp_n and exp_n > 0 else None

        results.append({
            "ticker": tk,
            "bucket": bucket,
            "industry": r["industry"],
            "mcap_b": r["mcap"]/1e9,
            "rev_b":  r["revenue"]/1e9 if r["revenue"] else 0,
            "n_FRS":  nfrs,
            "rev_per_FRS_M": (rpf/1e6) if rpf else None,
            "z_log_rev_per_FRS": z_rpf,
            "z_log_n_FRS": z_n,
            "expected_n_FRS_at_ctrl_rate": exp_n,
            "actual_vs_expected_ratio": ratio,
        })

    # Print table
    print("=== Divergence scores (vs chemistry-control distribution) ===")
    print(f"{'TK':5s} {'bkt':>5s} {'mcap':>5s} {'rev':>5s} {'n_FRS':>5s} "
          f"{'rev/FRS':>8s} {'z_rpf':>6s} {'z_nf':>6s} "
          f"{'exp_n':>6s} {'act/exp':>7s} flag")
    print("=" * 90)
    for r in sorted(results, key=lambda r: (r["bucket"], r["ticker"])):
        rpf_s = f"{r['rev_per_FRS_M']:>7.1f}M" if r["rev_per_FRS_M"] else "      --"
        z_rpf_s = f"{r['z_log_rev_per_FRS']:+5.2f}" if r["z_log_rev_per_FRS"] is not None else "  n/a"
        z_n_s   = f"{r['z_log_n_FRS']:+5.2f}" if r["z_log_n_FRS"] is not None else "  n/a"
        exp_n_s = f"{r['expected_n_FRS_at_ctrl_rate']:>5.1f}" if r["expected_n_FRS_at_ctrl_rate"] else "    --"
        rat_s   = f"{r['actual_vs_expected_ratio']:>6.2f}" if r["actual_vs_expected_ratio"] is not None else "    --"

        flag = ""
        if r["z_log_rev_per_FRS"] is not None and abs(r["z_log_rev_per_FRS"]) >= 1.5:
            flag = "DIVERGE"
        elif r["z_log_n_FRS"] is not None and abs(r["z_log_n_FRS"]) >= 1.5:
            flag = "DIVERGE_n"
        if r["bucket"] == "TGT" and r["n_FRS"] == 0:
            flag = "ZERO_FRS"

        print(f"  {r['ticker']:5s} {r['bucket']:>4s} "
              f"{r['mcap_b']:>4.2f}B {r['rev_b']:>4.2f}B "
              f"{r['n_FRS']:>5d} {rpf_s:>8s} {z_rpf_s:>6s} {z_n_s:>6s} "
              f"{exp_n_s:>6s} {rat_s:>7s}  {flag}")

    # Save
    out = {
        "control_params": {
            "names": list(CONTROLS),
            "mu_log10_rev_per_FRS": mu_rpf,
            "sd_log10_rev_per_FRS": sd_rpf,
            "mu_log10_n_FRS": mu_n,
            "sd_log10_n_FRS": sd_n,
        },
        "rows": results,
    }
    (HERE / "divergence.json").write_text(json.dumps(out, indent=2))
    print()
    print("Wrote divergence.json")


if __name__ == "__main__":
    main()
