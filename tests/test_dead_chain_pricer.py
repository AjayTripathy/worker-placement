"""dead_chain_pricer is the mandatory staging gate for the options program — its math
must be RIGHT, not plausible. Tests pin: BSM against known values, American>=European
and >=intrinsic, the skew bump's shape, implied-vol round-trip, realized-vol on
synthetic series, the FAF regression (the numbers the post-mortem froze), and the
CLI gate's REFUSE behaviour (the whole reason the tool exists)."""
import json
import math
import subprocess
import sys

from desk.dead_chain_pricer import (bsm_put, american_put, skew_bump,
                                    implied_vol, realized_vols)


# ---------- BSM ----------

def test_bsm_put_matches_textbook_value():
    # canonical: S=K=100, T=1, sigma=20%, r=5%, q=0 -> put = 5.5735 (any BSM table)
    assert abs(bsm_put(100, 100, 1.0, 0.20, 0.05, 0.0) - 5.5735) < 0.01


def test_bsm_put_call_parity():
    # C - P = S e^{-qT} - K e^{-rT}; recover the call from parity and check it's
    # the BSM call value independently (S=110,K=100 -> call 17.663 at these params)
    S, K, T, r, q, sig = 110, 100, 1.0, 0.05, 0.0, 0.20
    p = bsm_put(S, K, T, sig, r, q)
    c = p + S * math.exp(-q * T) - K * math.exp(-r * T)
    assert abs(c - 17.663) < 0.02


def test_bsm_monotonic_in_vol_and_strike():
    base = bsm_put(75, 70, 0.5, 0.25, 0.04, 0.03)
    assert bsm_put(75, 70, 0.5, 0.35, 0.04, 0.03) > base          # more vol, dearer put
    assert bsm_put(75, 65, 0.5, 0.25, 0.04, 0.03) < base          # lower strike, cheaper put


def test_bsm_degenerate_inputs_return_intrinsic():
    assert bsm_put(50, 70, 0.0, 0.25, 0.04, 0.0) == 20.0
    assert bsm_put(80, 70, 0.5, 0.0, 0.04, 0.0) == 0.0


# ---------- American binomial ----------

def test_american_at_least_european_and_intrinsic():
    for S, K in [(75, 70), (70, 70), (60, 70), (40, 70)]:
        am = american_put(S, K, 0.45, 0.30, 0.04, 0.03, steps=200)
        eu = bsm_put(S, K, 0.45, 0.30, 0.04, 0.03)
        assert am >= eu - 1e-9, f"American < European at S={S}"
        assert am >= max(K - S, 0) - 1e-9, f"American < intrinsic at S={S}"


def test_american_equals_european_when_rates_zero():
    # with r=0 and q=0 there is no interest-on-strike incentive: early exercise of a
    # put is never optimal, so the binomial must converge to BSM
    am = american_put(75, 70, 0.45, 0.30, 0.0, 0.0, steps=400)
    eu = bsm_put(75, 70, 0.45, 0.30, 0.0, 0.0)
    assert abs(am - eu) < 0.02


def test_american_deep_itm_holds_intrinsic():
    # European deep-ITM put decays below intrinsic via discounting; American must not
    eu = bsm_put(40, 100, 1.0, 0.20, 0.05, 0.0)
    am = american_put(40, 100, 1.0, 0.20, 0.05, 0.0, steps=200)
    assert eu < 60.0
    assert am >= 60.0 - 1e-9


# ---------- skew ----------

def test_skew_zero_at_or_above_spot():
    assert skew_bump(75, 75) == 0.0
    assert skew_bump(75, 80) == 0.0


def test_skew_scales_with_otm_distance():
    # FAF regression: 70 strike vs 75.15 spot = 7.1% log-OTM -> +2.1 vol pts at 0.30
    assert abs(skew_bump(75.15, 70, 0.30) - 0.0213) < 0.002
    assert skew_bump(75, 60, 0.30) > skew_bump(75, 70, 0.30)
    assert skew_bump(75, 70, 0.0) == 0.0                          # disable switch


# ---------- implied vol ----------

def test_implied_vol_round_trip():
    price = bsm_put(75.15, 70, 0.45, 0.25, 0.039, 0.029)
    iv = implied_vol(price, 75.15, 70, 0.45, 0.039, 0.029)
    assert iv is not None and abs(iv - 0.25) < 0.001


def test_implied_vol_unresolvable_returns_none():
    # a price above the sigma=200% bracket cannot be inverted -> None (a tiny but
    # positive price is NOT unresolvable — it just implies tiny vol)
    assert implied_vol(69.0, 75.15, 70, 0.45, 0.039, 0.029) is None
    # ITM put priced below its lower no-arbitrage bound is likewise uninvertible
    assert implied_vol(1.0, 50.0, 70, 0.45, 0.039, 0.029) is None


# ---------- realized vol ----------

def test_realized_vol_on_synthetic_alternating_series():
    # alternating +1%/-1% daily log-returns -> stdev ~1%/day -> ~15.9% annualized
    closes, px = [], 100.0
    for i in range(300):
        px *= math.exp(0.01 if i % 2 == 0 else -0.01)
        closes.append(px)
    rv = realized_vols(closes)
    assert abs(rv["rv_1y"] - 0.01 * math.sqrt(252)) < 0.01
    assert rv["n_bars"] == 300


def test_realized_vol_thin_series_refuses_windows():
    rv = realized_vols([100.0 + i * 0.1 for i in range(30)])
    assert rv["rv_1y"] is None and rv["rv_2y"] is None


# ---------- FAF regression (the frozen post-mortem numbers) ----------

def test_faf_regression_full_model():
    # sigma = RV 29.2% + skew 2.1 -> 31.3%; theo ~3.70, reservation (+4pt) ~4.41
    sigma = 0.292 + skew_bump(75.15, 70, 0.30)
    t = 165 / 365
    theo = american_put(75.15, 70, t, sigma, 0.039, 0.029, steps=400)
    resv = american_put(75.15, 70, t, sigma + 0.04, 0.039, 0.029, steps=400)
    assert abs(theo - 3.70) < 0.06
    assert abs(resv - 4.41) < 0.06
    assert 3.40 < theo    # the FAF fill must grade BELOW theoretical under the full model


# ---------- CLI gate (subprocess; the tool's reason to exist) ----------

def _run_cli(root, args):
    return subprocess.run([sys.executable, "-m", "desk.dead_chain_pricer"] + args,
                          cwd=str(root), capture_output=True, text=True, timeout=120)


def _closes_file(tmp_path):
    closes, px = [], 100.0
    import random
    rnd = random.Random(7)                      # deterministic series, ~25% vol
    for _ in range(300):
        px *= math.exp(rnd.gauss(0, 0.0157))
        closes.append(px)
    f = tmp_path / "closes.json"
    f.write_text(json.dumps(closes))
    return f, closes[-1]


def test_cli_refuses_ask_below_theoretical(root, tmp_path):
    f, last = _closes_file(tmp_path)
    r = _run_cli(root, ["SYN", str(round(last * 0.93, 2)), "2027-06-18",
                        "--spot", f"{last:.2f}", "--div-yield", "0.02",
                        "--closes-json", str(f), "--check", "0.05"])
    assert r.returncode == 0, r.stderr
    assert "REFUSE" in r.stdout
    assert "RESERVATION ASK" in r.stdout
    assert "after-tax" in r.stdout              # the carry-vs-muni line always prints


def test_cli_passes_generous_ask_and_mark_is_floor_only(root, tmp_path):
    f, last = _closes_file(tmp_path)
    strike = round(last * 0.93, 2)
    r = _run_cli(root, ["SYN", str(strike), "2027-06-18",
                        "--spot", f"{last:.2f}", "--div-yield", "0.02",
                        "--closes-json", str(f), "--check", str(round(strike * 0.5, 2)),
                        "--mark", str(round(strike * 0.9, 2))])
    assert r.returncode == 0, r.stderr
    assert "PASS" in r.stdout                   # an absurdly rich ask passes the gate
    assert "floor" in r.stdout                  # a high observed mark RAISES the quote
    assert "NEVER a discount" in r.stdout


def test_cli_requires_spot_with_injected_closes(root, tmp_path):
    f, _ = _closes_file(tmp_path)
    r = _run_cli(root, ["SYN", "65", "2027-06-18", "--closes-json", str(f)])
    assert r.returncode != 0
    assert "--spot is required" in (r.stdout + r.stderr)
