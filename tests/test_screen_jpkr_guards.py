"""Golden tests for the Japan/Korea batch-2 screen-defect fixes.
The fixtures ARE the caught names, with the trap-verification's verified-correct values."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "verticals" / "deep_value" / "global"))

from screen_japan import apply_japan_guards          # noqa: E402
from screen_korea import apply_korea_guards          # noqa: E402


# =============== JAPAN ===============
def test_jp_mcap_divergence_nulls_ratios():
    # SEMITEC 6626: screen mcap ¥8B vs true ¥19.7B — every ratio must stop ranking
    r = {"mktcap": 8.0e9, "am": 4.1, "pb": 0.98, "ncash_r": 0.38, "ncav_r": 0.1, "fcfy": 0.12}
    apply_japan_guards(r, {}, yq_mcap=19.7e9)
    assert r["mcap_suspect"] is True
    assert r["mktcap"] == 19.7e9                      # larger wins: bias against fake cheapness
    assert r["am"] is None and r["pb"] is None and r["ncash_r"] is None and r["fcfy"] is None
    assert r["am_asis"] == 4.1                        # forensics preserved


def test_jp_mcap_agreement_keeps_ratios():
    r = {"mktcap": 10.0e9, "am": 3.0, "pb": 0.5, "ncash_r": 0.4, "ncav_r": 0.2, "fcfy": 0.10}
    apply_japan_guards(r, {"PaymentsToAcquirePropertyPlantAndEquipment": 1.0}, yq_mcap=10.9e9)
    assert r["mcap_suspect"] is False and r["am"] == 3.0


def test_jp_no_yahoo_quote_no_false_fire():
    r = {"mktcap": 10.0e9, "am": 3.0, "fcfy": 0.10}
    apply_japan_guards(r, {"PaymentsToAcquirePropertyPlantAndEquipment": 1.0}, yq_mcap=None)
    assert r["mcap_suspect"] is False


def test_jp_missing_capex_never_prints_cfo_as_fcf():
    # SEMITEC's 12% was CFO-derived with capex=None in the store
    r = {"mktcap": 19.7e9, "fcfy": 0.12}
    apply_japan_guards(r, {"PaymentsToAcquirePropertyPlantAndEquipment": None}, yq_mcap=19.7e9)
    assert r["fcfy"] is None and r["fcf_no_capex"] is True and r["fcfy_asis"] == 0.12


def test_jp_contract_liabilities_adjust_netcash():
    # Kinki Sharyo 7122: cash ¥16.9B, 契約負債 ¥20.1B, mcap ¥16.3B — ncash flips negative
    r = {"mktcap": 16.3e9, "ncash_r": 1.05, "fcfy": None}
    f = {"CashAndCashEquivalentsAtCarryingValue": 16.9e9, "_ContractLiabilities": 20.1e9,
         "PaymentsToAcquirePropertyPlantAndEquipment": 1.7e9}
    apply_japan_guards(r, f, yq_mcap=16.3e9)
    assert r["contract_liab_adj"] is True
    assert r["ncash_r"] < 0                           # 1.05 − 20.1/16.3 ≈ −0.18
    assert abs(r["ncash_r"] - (1.05 - 20.1 / 16.3)) < 1e-9


def test_jp_small_advances_not_adjusted():
    r = {"mktcap": 10e9, "ncash_r": 0.5}
    f = {"CashAndCashEquivalentsAtCarryingValue": 10e9, "_ContractLiabilities": 1e9,
         "PaymentsToAcquirePropertyPlantAndEquipment": 1.0}
    apply_japan_guards(r, f, yq_mcap=10e9)
    assert r["contract_liab_adj"] is False and r["ncash_r"] == 0.5


# =============== KOREA ===============
def _itcen():
    # ITCen CTS 031820: NCI ₩130.0B of ₩377.8B equity; annual cash ₩167.1B, 1Q26 ₩110.9B
    return {"MinorityInterest": 130.0e9, "StockholdersEquity": 247.8e9,
            "CashAndCashEquivalentsAtCarryingValue": 167.1e9,
            "interim": {"period_end": "2026-03-31",
                        "CashAndCashEquivalentsAtCarryingValue": 110.9e9}}


def test_kr_nci_heavy_nulls_ncash():
    r = {"mktcap": 69.1e9, "ncash_r": 1.29}
    apply_korea_guards(r, _itcen())
    assert r["nci_heavy"] is True and r["ncash_ye_float"] is True
    assert r["ncash_r"] is None and r["ncash_r_asis"] == 1.29


def test_kr_ye_float_alone_fires():
    # Hancom 372910: annual ₩51.3B -> 1Q ₩36.0B (70.1% — under the 75% line)
    f = {"MinorityInterest": 0, "StockholdersEquity": 100e9,
         "CashAndCashEquivalentsAtCarryingValue": 51.3e9,
         "interim": {"CashAndCashEquivalentsAtCarryingValue": 36.0e9}}
    r = {"mktcap": 48.8e9, "ncash_r": 1.05}
    apply_korea_guards(r, f)
    assert r["nci_heavy"] is False and r["ncash_ye_float"] is True and r["ncash_r"] is None


def test_kr_stable_interim_cash_keeps_ncash():
    # DY Power-shaped: interim cash flat (64.75 vs 64.77) — the guard must NOT fire
    f = {"MinorityInterest": 1e9, "StockholdersEquity": 300e9,
         "CashAndCashEquivalentsAtCarryingValue": 64.77e9,
         "interim": {"CashAndCashEquivalentsAtCarryingValue": 64.75e9}}
    r = {"mktcap": 124.5e9, "ncash_r": 0.50}
    apply_korea_guards(r, f)
    assert r["ncash_ye_float"] is False and r["ncash_r"] == 0.50


def test_kr_no_interim_no_false_fire():
    f = {"CashAndCashEquivalentsAtCarryingValue": 50e9, "StockholdersEquity": 100e9}
    r = {"mktcap": 50e9, "ncash_r": 0.8}
    apply_korea_guards(r, f)
    assert r["ncash_ye_float"] is False and r["ncash_r"] == 0.8


def test_kr_contract_advances_subtract():
    # Hancom-shaped once _ContractAdvances lands on recrawl: 선수금 60.7B vs cash 51.3B
    f = {"CashAndCashEquivalentsAtCarryingValue": 51.3e9, "_ContractAdvances": 60.7e9,
         "StockholdersEquity": 100e9,
         "interim": {"CashAndCashEquivalentsAtCarryingValue": 50e9}}   # interim fine here
    r = {"mktcap": 48.8e9, "ncash_r": 1.04}
    apply_korea_guards(r, f)
    assert r["contract_adv_adj"] is True
    assert r["ncash_r"] < 0                            # 1.04 − 60.7/48.8 ≈ −0.20


def test_kr_cb_trail_flag():
    r = {"mktcap": 47.8e9, "ncash_r": 0.29}
    apply_korea_guards(r, {"_DebtCurSpecificCB": 11.32e9,
                           "CashAndCashEquivalentsAtCarryingValue": 27.9e9,
                           "StockholdersEquity": 100e9})
    assert r["cb_on_bs"] is True


def test_kr_cb_labels_in_name_map():
    import dart_fundamentals as DF
    m = dict(DF.NAME_MAP)
    assert "유동성전환사채" in m["_DebtCurSpecificCB"]
    assert "전환사채" in m["_DebtCB"]
    assert "선수금" in m["_ContractAdvances"] and "계약부채" in m["_ContractAdvances"]
