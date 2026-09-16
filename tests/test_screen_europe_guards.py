"""Golden regression tests for the Europe-screen defect fixes.

The fixtures ARE the caught bugs — real extracted store values for the names the
batch-2 trap verification refuted, with the verified-correct behavior asserted:
  KSL.HE  — zero debt tags + EUR 69.4M noncurrent liabilities: 7.9x printed vs 14.3x true
  VERK.HE — BS leases tagged, lease payments untagged: 13.2% FCFy printed vs ~7% true
  CARD.L  — BS leases tagged: 38.3% FCFy printed vs 15.7% company-published true
Every future caught screen bug adds its fixture here (PIPELINE_ARCHITECTURE §P1 tests).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "verticals" / "deep_value" / "global"))

from screen_europe import apply_europe_guards  # noqa: E402


# ---- fixtures: minimal real extracts (esef_store.json, crawl of 2026-08-06) ----
KSL = {  # Keskisuomalainen — the debt-blind class
    "Liabilities": 138_385_000.0, "LiabilitiesCurrent": 69_007_000.0,
    "Assets": 191_826_000.0, "CashAndCashEquivalentsAtCarryingValue": 15_909_000.0,
    "OperatingIncomeLoss": 11_700_000.0, "OperatingIncomeLoss_prior": 2_600_000.0,
    "Revenues": 212_800_000.0, "Revenues_prior": 202_700_000.0,
    # NO debt-side tags at all — the defect condition
}

VERK = {  # Verkkokauppa — leases on BS, payment untagged
    "_DebtCurrentBorrowings": 2_097_000.0, "_DebtLeaseCurrent": 4_194_000.0,
    "_DebtLeaseNoncurrent": 19_573_000.0,
    "Liabilities": 133_803_000.0, "LiabilitiesCurrent": 98_523_000.0,
    "Assets": 173_175_000.0, "CashAndCashEquivalentsAtCarryingValue": 47_288_000.0,
    "OperatingIncomeLoss": 17_392_000.0, "OperatingIncomeLoss_prior": 10_100_000.0,
    "Revenues": 553_000_000.0, "Revenues_prior": 520_000_000.0,
}

CARD = {  # Card Factory — leases on BS; payment TAGGED in this variant
    "_DebtCurrentBorrowings": 1_500_000.0, "_DebtNoncurrentBorrowings": 83_800_000.0,
    "_DebtLeaseCurrent": 32_800_000.0, "_DebtLeaseNoncurrent": 90_400_000.0,
    "_LeasePayments": 37_000_000.0,       # FY26 prelims: "Payment of lease liabilities"
    "OperatingIncomeLoss": 59_400_000.0, "OperatingIncomeLoss_prior": 66_100_000.0,
    "Revenues": 582_700_000.0, "Revenues_prior": 542_500_000.0,
}

CLEAN = {  # unlevered filer: no debt tags AND small noncurrent liabilities — keeps numbers
    "Liabilities": 30_000_000.0, "LiabilitiesCurrent": 28_000_000.0,
    "Assets": 200_000_000.0, "CashAndCashEquivalentsAtCarryingValue": 60_000_000.0,
    "OperatingIncomeLoss": 20_000_000.0, "OperatingIncomeLoss_prior": 18_000_000.0,
    "Revenues": 100_000_000.0, "Revenues_prior": 95_000_000.0,
}


def _m(**kw):
    base = {"am": 7.9, "ncash_r": 0.18, "fcf": 20_400_000.0, "fcfy": 0.182,
            "mktcap": 112_300_000.0}
    base.update(kw)
    return base


# ---------- defect 2: KSL debt-blindness ----------
def test_ksl_debt_blind_nulls_multiple_and_ncash():
    m = apply_europe_guards(_m(), dict(KSL))
    assert m["debt_blind"] is True
    assert m["ncash_r"] is None and m["am"] is None       # 7.9x must never print again
    assert m["am_asis"] == 7.9                            # as-is preserved for forensics


def test_clean_unlevered_filer_keeps_numbers():
    m = apply_europe_guards(_m(am=5.0, ncash_r=0.5), dict(CLEAN))
    assert m["debt_blind"] is False
    assert m["am"] == 5.0 and m["ncash_r"] == 0.5


def test_tagged_debt_never_triggers_blind_guard():
    m = apply_europe_guards(_m(), dict(VERK))
    assert m["debt_blind"] is False


# ---------- defect 1: IFRS16 lease-blind FCF ----------
def test_verk_untagged_lease_payment_blinds_fcfy():
    m = apply_europe_guards(_m(fcf=20_102_000.0, fcfy=0.132, mktcap=152_200_000.0), dict(VERK))
    assert m["fcf_lease_blind"] is True
    assert m["fcfy"] is None                              # 13.2% must never print again


def test_card_tagged_lease_payment_corrects_fcfy():
    m = apply_europe_guards(
        _m(fcf=98_600_000.0, fcfy=0.383, mktcap=257_400_000.0), dict(CARD))
    assert m["fcf_lease_blind"] is False
    assert m["fcf"] == 98_600_000.0 - 37_000_000.0
    # corrected 61.6/257.4 = 23.9% — still generous vs the company's 15.7% (interest legs
    # stay untagged in ESEF), but the 2.4x-inflated 38.3% is dead
    assert abs(m["fcfy"] - 0.2394) < 0.001


def test_no_lease_tags_leaves_fcf_untouched():
    m = apply_europe_guards(_m(fcf=10.0, fcfy=0.10), dict(CLEAN))
    assert m["fcf_lease_blind"] is False and m["fcfy"] == 0.10


# ---------- defect 3: one-off contamination ----------
def test_ksl_one_off_suspect_fires():
    # EBIT 2.6M -> 11.7M (+350%) on rev +5% — the competitor-exit windfall pattern
    m = apply_europe_guards(_m(), dict(KSL))
    assert m["one_off_suspect"] is True


def test_verk_one_off_fires_on_finance_book_gain():
    # EBIT 10.1 -> 17.4M (+72%) on rev +6.3%
    m = apply_europe_guards(_m(), dict(VERK))
    assert m["one_off_suspect"] is True


def test_ordinary_growth_not_flagged():
    m = apply_europe_guards(_m(), dict(CLEAN))            # EBIT +11% on rev +5.3%
    assert m["one_off_suspect"] is False


def test_card_moderate_decline_not_flagged():
    m = apply_europe_guards(_m(), dict(CARD))             # EBIT −10% on rev +7.4%
    assert m["one_off_suspect"] is False
