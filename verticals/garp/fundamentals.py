"""Multi-year fundamentals cross-section for GARP, via the SEC frames API.

Pulls 4 annual years (CY2022..CY2025) of Revenues / NetIncome / OperatingIncome so we can
compute trailing 3-yr growth, plus latest-quarter balance-sheet instants and CY2025 cash
flow. ~25 frame calls assemble the whole small/mid-cap cross-section. Reuses the
deep_value frame() / _freshest() helpers (same SEC endpoint + rate-limit + calendar-frame
limitation: off-fiscal-year filers are absent).
"""
from __future__ import annotations
from ..deep_value import fundamentals as DV

YEARS = ["CY2022", "CY2023", "CY2024", "CY2025"]
INSTANTS = ["CY2026Q1I", "CY2025Q4I", "CY2025Q3I", "CY2024Q4I"]
FLOW = ["Revenues", "NetIncomeLoss", "OperatingIncomeLoss"]
INST = ["StockholdersEquity", "Assets", "Liabilities",
        "CashAndCashEquivalentsAtCarryingValue", "ShortTermInvestments",
        "LongTermDebtNoncurrent", "LongTermDebt", "DebtCurrent"]


def build_cross_section() -> dict[int, dict]:
    """{cik: {Revenues_CY2025, NetIncomeLoss_CY2022, ..., StockholdersEquity, cfo, capx}}"""
    flows = {c: {y: DV.frame(c, y) for y in YEARS} for c in FLOW}
    # revenue-tag fallback: many filers tag the newer RevenueFromContractWithCustomer...
    rev_alt = {y: DV.frame("RevenueFromContractWithCustomerExcludingAssessedTax", y) for y in YEARS}
    for y in YEARS:
        for cik, v in rev_alt[y].items():
            flows["Revenues"][y].setdefault(cik, v)        # fill only where Revenues absent
    cfo = DV._freshest("NetCashProvidedByUsedInOperatingActivities", ["CY2025", "CY2024"])
    capx = DV._freshest("PaymentsToAcquirePropertyPlantAndEquipment", ["CY2025", "CY2024"])
    inst = {c: DV._freshest(c, INSTANTS) for c in INST}

    ciks = set()
    for c in FLOW:
        for y in YEARS:
            ciks |= set(flows[c][y])

    out = {}
    for cik in ciks:
        rec = {}
        for c in FLOW:
            for y in YEARS:
                rec[f"{c}_{y}"] = flows[c][y].get(cik)
        rec["cfo"] = cfo.get(cik)
        rec["capx"] = capx.get(cik)
        for c in INST:
            rec[c] = inst[c].get(cik)
        out[cik] = rec
    return out
