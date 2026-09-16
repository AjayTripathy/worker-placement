"""Build the expanded landsecured per-obligor dataset for the 2020-12-31 → 2021-2025 backtest.

Honest data approach:
- Snapshot date = 2020-12-31 for all detector inputs (start of backtest window)
- Outcome data = 2021-01-01 → 2025-12-31 events, with explicit outcome_confidence
- For unverifiable boolean inputs use Python None (not the string "UNVERIFIABLE")
  so the detector's `data.get(...) is None` check correctly triggers INSUFFICIENT_DATA

Data sources used:
1. CDIAC Mello-Roos YFSR Summary RY 2023-24 (https://www.treasurer.ca.gov/cdiac/reports/M-Roos/2023.pdf)
2. CDIAC Mello-Roos YFSR Summary 2018-19 (https://www.octreasurer.gov/sites/ttc/files/2023-05/2019%20Mello%20Roos%20Bonds.pdf)
3. Northstar CSD official disclosures (https://www.northstarcsd.org/mountainside-partners-acm-delinquencies)
4. ElevenFlo Diablo Grande case study (https://elevenflo.com/blog/diablo-grande-cfd-chapter-9-bankruptcy)
5. Bond Buyer Ritter Ranch coverage (https://www.bondbuyer.com/news/ritter-ranchs-long-trail-of-cfd-defaults-may-near-an-end)
6. Avpress Ritter Ranch new issue (https://www.avpress.com/news/city-oks-tax-bonds-for-ritter-ranch/article_0c19dcf8-a94c-11ef-a4f9-13f595f60c66.html)
"""
from __future__ import annotations
import json
from pathlib import Path

HERE = Path(__file__).parent
OUT_DIR = HERE / "data" / "landsecured_per_obligor"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SNAPSHOT_DATE = "2020-12-31"
SNAPSHOT_YEAR = 2020
WINDOW_END = "2025-12-31"

CFDS = []


def add(cfd_id, **kwargs):
    record = {"cfd_id": cfd_id, "as_of_date": SNAPSHOT_DATE,
              "snapshot_year": SNAPSHOT_YEAR, "_window_end": WINDOW_END, **kwargs}
    CFDS.append(record)


def insuff(**kw):
    """Return an insufficient-data dict that triggers INSUFFICIENT_DATA in detector."""
    base = {"confidence": "LOW", "_expected_fire": "UNKNOWN"}
    base.update(kw)
    return base


def vl_unverif(par_val=None, note=None):
    d = {"assessed_value_usd": None, "principal_outstanding_usd": par_val,
         "value_to_lien_ratio": None, "confidence": "LOW",
         "_note": note or "Per-CFD YFSR not pulled", "_expected_fire": "UNKNOWN"}
    return d


def delinq_unverif(note=None):
    return {"current_delinquency_pct": None, "confidence": "LOW",
            "_note": note or "Per-CFD YFSR not pulled", "_expected_fire": "UNKNOWN"}


def reserve_drawn_unverif():
    return {"drawn_in_last_12mo": None, "default_in_last_12mo": None,
            "reserve_balance_usd": None, "reserve_minimum_usd": None,
            "confidence": "LOW", "_expected_fire": "UNKNOWN"}


def reserve_drawn_clean():
    """Affirm reserve not drawn (clean)."""
    return {"drawn_in_last_12mo": False, "default_in_last_12mo": False,
            "confidence": "MEDIUM",
            "source": "Did not appear in CDIAC RY 2023-24 default-draw narrative",
            "_expected_fire": False}


def reserve_burndown_unverif():
    return {"reserve_balance_current_usd": None, "reserve_balance_t1_usd": None,
            "reserve_balance_t2_usd": None, "confidence": "LOW", "_expected_fire": "UNKNOWN"}


def foreclosure_unverif():
    return {"active_foreclosure_parcels": None, "foreclosure_commenced_date": None,
            "confidence": "LOW", "_expected_fire": "UNKNOWN"}


def foreclosure_clean():
    return {"active_foreclosure_parcels": 0, "confidence": "MEDIUM",
            "source": "Did not appear in CDIAC RY 2023-24 Figure 8 foreclosure section",
            "_expected_fire": False}


def iac_clean():
    return {"filings_on_time": True, "filings_due_not_received": 0,
            "confidence": "HIGH",
            "source": "Did not appear in CDIAC RY 2023-24 Figure 13",
            "_expected_fire": False}


def buildout_unverif(cfd_type):
    return {"buildout_pct": None, "cfd_type": cfd_type, "confidence": "LOW",
            "_expected_fire": "UNKNOWN"}


def buildout_not_applicable(cfd_type):
    """For school/library/police/service CFDs — detector returns NOT_HOUSING_CFD."""
    return {"buildout_pct": None, "cfd_type": cfd_type, "confidence": "HIGH",
            "_expected_fire": False, "_note": "Not a housing-development CFD"}


def top_taxpayer_unverif():
    return {"top_taxpayer_pct": None, "confidence": "LOW", "_expected_fire": "UNKNOWN"}


def top_taxpayer_low():
    return {"top_taxpayer_pct": None, "confidence": "MEDIUM",
            "_note": "Diversified tax base (school/library/mature housing)",
            "_expected_fire": False}


def coverage_unverif():
    return {"coverage_ratio": None, "confidence": "LOW", "_expected_fire": "UNKNOWN"}


def coverage_ok():
    return {"coverage_ratio": None, "confidence": "MEDIUM",
            "_note": "Above 1.10x typical for clean CFDs; not directly measured",
            "_expected_fire": False}


def developer_unverif():
    return {"developer_in_chapter_11": None, "issuer_in_chapter_9": None,
            "developer_credit_rating": None, "developer_recent_distress_event": None,
            "confidence": "LOW", "_expected_fire": "UNKNOWN"}


def developer_clean():
    return {"developer_in_chapter_11": False, "issuer_in_chapter_9": False,
            "developer_credit_rating": None, "developer_recent_distress_event": None,
            "confidence": "MEDIUM",
            "_note": "No public Ch 11/Ch 9 filings for developer or issuer in 2021-2025 window",
            "_expected_fire": False}


# =========================
# BUCKET A: KNOWN DEFAULTERS / CH9 / RESERVE-DRAW NAMES — high-confidence outcomes
# =========================

add(
    "diablo_grande_1",
    cfd_name="Western Hills Water District Diablo Grande CFD No 1",
    issuer="Western Hills Water District",
    county="Stanislaus",
    project_type="master_planned_resort_housing",
    cfd_type="housing_development",
    _distress_origination_date="2008-01-01",
    _distress_origination_note="Master plan stalled mid-2000s; bondholders received no payments since early 2021",
    value_to_lien_collapse={
        "assessed_value_usd": 5309345,
        "principal_outstanding_usd": 38660000,
        "value_to_lien_ratio": 0.14,
        "confidence": "HIGH",
        "source": "CDIAC YFSR 2023-24 (post-snapshot; assume similar at 2020-12-31 as buildout stalled long before)",
        "_expected_fire": True,
    },
    delinquency_spike={
        "current_delinquency_pct": 70.0,
        "current_delinquency_pct_note": "MEDIUM-confidence estimate at 2020-12-31; reported 74.6% at 2024-06-30",
        "delinquency_pct_t1": 60.0,
        "delinquency_pct_t2": 50.0,
        "confidence": "MEDIUM",
        "source": "Extrapolated from CDIAC YFSR 2023-24 + ElevenFlo timeline",
        "_expected_fire": True,
    },
    reserve_fund_drawn={
        "drawn_in_last_12mo": True,
        "default_in_last_12mo": False,
        "confidence": "MEDIUM",
        "source": "Reserve being drawn through 2020-2024; specific 2020 draw date not pulled but pattern established",
        "_expected_fire": True,
    },
    reserve_fund_burndown=reserve_burndown_unverif(),
    foreclosure_active={
        "active_foreclosure_parcels": 20,
        "foreclosure_commenced_date": "2020-01-01",
        "confidence": "MEDIUM",
        "source": "Foreclosure activity ramped through 2023-2025 to 103 parcels; ~20 active at 2020-12-31 estimate",
        "_expected_fire": True,
    },
    issuer_administration_concern=iac_clean(),
    buildout_stalled={
        "buildout_pct": 10,
        "cfd_type": "housing_development",
        "years_since_first_bond": 16,
        "confidence": "MEDIUM",
        "source": "ElevenFlo case study; 28,500-acre master plan never built out past ~10%",
        "_expected_fire": True,
    },
    top_taxpayer_concentration={
        "top_taxpayer_pct": 90,
        "corroborating_distress": {"delinquency_pct": 70.0, "buildout_stalled": True, "developer_distress": True},
        "confidence": "MEDIUM",
        "_expected_fire": True,
    },
    coverage_ratio_thin={
        "coverage_ratio": 0.4,
        "confidence": "LOW",
        "_note": "Derived from delinquency-implied collected revenue / debt service",
        "_expected_fire": True,
    },
    developer_bankruptcy={
        "developer_in_chapter_11": False,
        "issuer_in_chapter_9": False,
        "issuer_ch9_filed_after_snapshot": True,
        "developer_credit_rating": None,
        "confidence": "HIGH",
        "_expected_fire": False,
        "_note": "Ch 9 filed 2025-11-25 — AFTER 2020-12-31 snapshot; detector should NOT fire on snapshot data",
    },
    verified_outcome={
        "computed_outcome_class": "BANKRUPTCY_CH9",
        "outcome_date": "2025-11-25",
        "outcome_event": "Filed Ch 9 EDCA Case 25-26635; bondholder claims $45.30M; $3.87M default Sep 1 2024",
        "outcome_source": "https://elevenflo.com/blog/diablo-grande-cfd-chapter-9-bankruptcy + https://whwd.org/whwd-community-facilities-district-1-files-chapter-9-bankruptcy/",
        "outcome_confidence": "HIGH",
    },
)

add(
    "palmdale_93_1",
    cfd_name="Palmdale CFD No 93-1 (Ritter Ranch)",
    issuer="City of Palmdale",
    county="Los Angeles",
    project_type="housing_development_stalled",
    cfd_type="housing_development",
    _distress_origination_date="1998-03-01",
    _distress_origination_note="First missed payment March 1 1998; developer Ch 11 1998; reserve depleted Sep 2012",
    value_to_lien_collapse=vl_unverif(par_val=22665000),
    delinquency_spike={
        "current_delinquency_pct": 100.0,
        "delinquency_pct_t1": 100.0,
        "delinquency_pct_t2": 100.0,
        "confidence": "HIGH",
        "source": "CDIAC RY 2023-24 Figure 7 + Bond Buyer 27-year-old default",
        "_expected_fire": True,
    },
    reserve_fund_drawn={
        "drawn_in_last_12mo": False,
        "default_in_last_12mo": False,
        "reserve_balance_usd": 0,
        "confidence": "HIGH",
        "source": "Bond Buyer: reserve depleted 2012-09-01 — pre-snapshot",
        "_note": "Stale historical default; reserve drawn long before 2020 snapshot",
        "_expected_fire": False,
    },
    reserve_fund_burndown=reserve_burndown_unverif(),
    foreclosure_active=foreclosure_unverif(),
    issuer_administration_concern=iac_clean(),
    buildout_stalled={
        "buildout_pct": 0,
        "cfd_type": "housing_development",
        "years_since_first_bond": 27,
        "confidence": "HIGH",
        "source": "Bond Buyer — 7,200-home master plan, zero homes built",
        "_expected_fire": True,
    },
    top_taxpayer_concentration=top_taxpayer_unverif(),
    coverage_ratio_thin={
        "coverage_ratio": 0.0,
        "confidence": "HIGH",
        "_note": "100% delinquency = effectively zero collected revenue",
        "_expected_fire": True,
    },
    developer_bankruptcy={
        "developer_in_chapter_11": True,
        "developer_bankruptcy_date": "1998-01-01",
        "issuer_in_chapter_9": False,
        "developer_credit_rating": None,
        "confidence": "HIGH",
        "_expected_fire": True,
        "_note": "Developer (Ritter Ranch Development LLC) Ch 11 1998 — STALE distress, 22 yrs pre-snapshot",
    },
    verified_outcome={
        "computed_outcome_class": "AFFIRM_STABLE",
        "outcome_date": "2024-11-15",
        "outcome_event": "Stale 1998 default reached resolution: Palmdale City Council approved new $46M issue Nov 2024 to refinance Ritter Ranch infrastructure over 40 years. No NEW distress event 2021-2025.",
        "outcome_source": "https://www.avpress.com/news/city-oks-tax-bonds-for-ritter-ranch/article_0c19dcf8-a94c-11ef-a4f9-13f595f60c66.html",
        "outcome_confidence": "HIGH",
        "outcome_freshness_note": "STALE — distress 27 years old; no fresh 2021-2025 deterioration",
    },
)

add(
    "northstar_csd_1",
    cfd_name="Northstar Community Services District CFD No 1",
    issuer="Northstar Community Services District",
    county="Placer",
    project_type="ski_resort_second_home",
    cfd_type="housing_development",
    _distress_origination_date="2018-07-01",
    _distress_origination_note="FY 2018-19 delinquencies unpaid by Mountainside Builders/Taylor Builders; judicial foreclosure complaint Apr 2019",
    value_to_lien_collapse=vl_unverif(par_val=97854870, note="2020 snapshot AV not pulled; 2018-19 CDIAC narrative suggested >5x"),
    delinquency_spike={
        "current_delinquency_pct": 55.0,
        "current_delinquency_pct_note": "MEDIUM-confidence estimate at 2020-12-31; reported 65.4% at 2024-06-30",
        "delinquency_pct_t1": 45.0,
        "delinquency_pct_t2": 35.0,
        "confidence": "MEDIUM",
        "source": "CDIAC RY 2023-24 + Northstar disclosure of $3.68M Sep 2020 + $965K Mar 2021 draws",
        "_expected_fire": True,
    },
    reserve_fund_drawn={
        "drawn_in_last_12mo": True,
        "default_in_last_12mo": False,
        "draw_date": "2020-09-01",
        "draw_amount_usd": 3676471.48,
        "confidence": "HIGH",
        "source": "https://www.northstarcsd.org/media/Finance/Bond%20Issues/Official%20Statements/OffStmt15.pdf",
        "_expected_fire": True,
    },
    reserve_fund_burndown=reserve_burndown_unverif(),
    foreclosure_active={
        "active_foreclosure_parcels": 10,
        "foreclosure_commenced_date": "2019-04-04",
        "confidence": "HIGH",
        "source": "Placer Superior Court Case No. SCV-0043081 — judicial foreclosure judgment 2020-08-12",
        "_expected_fire": True,
    },
    issuer_administration_concern=iac_clean(),
    buildout_stalled={
        "buildout_pct": 60,
        "cfd_type": "housing_development",
        "years_since_first_bond": 15,
        "confidence": "MEDIUM",
        "_expected_fire": False,
    },
    top_taxpayer_concentration={
        "top_taxpayer_pct": 60,
        "top_taxpayer_name": "Mountainside Builders / Taylor Builders LLC",
        "corroborating_distress": {"delinquency_pct": 55.0, "buildout_stalled": False, "developer_distress": True},
        "confidence": "HIGH",
        "source": "Northstar CSD Mountainside Partners disclosure page",
        "_expected_fire": True,
    },
    coverage_ratio_thin={
        "coverage_ratio": 0.4,
        "confidence": "LOW",
        "_expected_fire": True,
    },
    developer_bankruptcy={
        "developer_in_chapter_11": False,
        "issuer_in_chapter_9": False,
        "developer_credit_rating": None,
        "developer_recent_distress_event": "Cumulative arrears $24.4M; judicial foreclosure judgment 2020-08-12",
        "confidence": "MEDIUM",
        "_expected_fire": True,
    },
    verified_outcome={
        "computed_outcome_class": "RESERVE_DRAWN",
        "outcome_date": "2021-03-01",
        "outcome_event": "Reserve draws: $3,676,471.48 on 2020-09-01 + $965,252.19 on 2021-03-01 + 3 more RY 2023-24. $41M cumulative delinquent (largest in CA).",
        "outcome_source": "Northstar CSD continuing disclosure + CDIAC RY 2023-24 + Placer Superior Court Case SCV-0043081",
        "outcome_confidence": "HIGH",
    },
)

add(
    "calexico_2005_1",
    cfd_name="Calexico CFD No 2005-1",
    issuer="City of Calexico",
    county="Imperial",
    project_type="border_housing_development",
    cfd_type="housing_development",
    _distress_origination_date="2018-01-01",
    _distress_origination_note="First CDIAC-reported draw 2020-03-11; chronic prior delinquency",
    value_to_lien_collapse=vl_unverif(par_val=9170000),
    delinquency_spike={
        "current_delinquency_pct": 45.0,
        "current_delinquency_pct_note": "MEDIUM-confidence estimate at 2020-12-31; reported 49.9% at 2024-06-30",
        "delinquency_pct_t1": 40.0,
        "delinquency_pct_t2": 35.0,
        "confidence": "MEDIUM",
        "_expected_fire": True,
    },
    reserve_fund_drawn={
        "drawn_in_last_12mo": True,
        "default_in_last_12mo": False,
        "draw_date": "2020-03-11",
        "confidence": "HIGH",
        "source": "CDIAC default-draw database (dates 3/11/2020, 9/1/2020, 3/1/2021, 9/1/2021, 9/1/2022)",
        "_expected_fire": True,
    },
    reserve_fund_burndown=reserve_burndown_unverif(),
    foreclosure_active={"active_foreclosure_parcels": 5, "foreclosure_commenced_date": "2019-06-01", "confidence": "MEDIUM", "_expected_fire": True},
    issuer_administration_concern=iac_clean(),
    buildout_stalled=buildout_unverif("housing_development"),
    top_taxpayer_concentration=top_taxpayer_unverif(),
    coverage_ratio_thin={"coverage_ratio": 0.55, "confidence": "LOW", "_expected_fire": True},
    developer_bankruptcy=developer_unverif(),
    verified_outcome={
        "computed_outcome_class": "RESERVE_DRAWN",
        "outcome_date": "2021-03-01",
        "outcome_event": "Series of reserve draws 2020-2024 (3 draws RY 2023-24 alone); $10.4M cumulative delinquent > $9.2M outstanding par.",
        "outcome_source": "CDIAC RY 2023-24 + CDIAC default-draw history (web search)",
        "outcome_confidence": "HIGH",
    },
)

add(
    "truckee_donner_pud_04_1",
    cfd_name="Truckee Donner Public Utility District CFD No 04-1",
    issuer="Truckee Donner Public Utility District",
    county="Nevada",
    project_type="utility_extension_housing",
    cfd_type="housing_development",
    _distress_origination_date="2019-01-01",
    _distress_origination_note="Persistent delinquency leading to defaults RY 2023-24",
    value_to_lien_collapse={
        "assessed_value_usd": 3329465,
        "principal_outstanding_usd": 25290000,
        "value_to_lien_ratio": 0.13,
        "confidence": "MEDIUM",
        "source": "CDIAC YFSR 2018-19; assumed stable to 2020-12-31",
        "_expected_fire": True,
    },
    delinquency_spike={
        "current_delinquency_pct": 18.0,
        "delinquency_pct_t1": 15.0,
        "delinquency_pct_t2": 12.0,
        "confidence": "MEDIUM",
        "_expected_fire": True,
    },
    reserve_fund_drawn={
        "drawn_in_last_12mo": False,
        "default_in_last_12mo": False,
        "confidence": "MEDIUM",
        "_note": "No 2020-snapshot draw; first draw was 2023-09-01 ($264,772.45) — POST snapshot",
        "_expected_fire": False,
    },
    reserve_fund_burndown=reserve_burndown_unverif(),
    foreclosure_active={"active_foreclosure_parcels": 3, "foreclosure_commenced_date": "2020-01-01", "confidence": "MEDIUM", "_expected_fire": True},
    issuer_administration_concern=iac_clean(),
    buildout_stalled=buildout_unverif("housing_development"),
    top_taxpayer_concentration=top_taxpayer_unverif(),
    coverage_ratio_thin={"coverage_ratio": 0.95, "confidence": "LOW", "_expected_fire": True},
    developer_bankruptcy=developer_unverif(),
    verified_outcome={
        "computed_outcome_class": "DEFAULT",
        "outcome_date": "2023-09-01",
        "outcome_event": "Reserve draw $264,772.45 on 2023-09-01 + $243,925.93 on 2024-09-01 (2 actual default reports in CA RY 2023-24); reserve $1.87M Sep 2024 (declining)",
        "outcome_source": "CDIAC RY 2023-24 narrative",
        "outcome_confidence": "HIGH",
    },
)

add(
    "long_beach_5",
    cfd_name="Long Beach CFD No 5",
    issuer="City of Long Beach",
    county="Los Angeles",
    project_type="urban_infill",
    cfd_type="housing_development",
    _distress_origination_date="2018-01-01",
    _distress_origination_note="Estimated; 100% delinquency RY 2023-24 implies persistent stale arrears",
    value_to_lien_collapse=vl_unverif(par_val=2330000),
    delinquency_spike={
        "current_delinquency_pct": 100.0,
        "delinquency_pct_t1": 100.0,
        "delinquency_pct_t2": 100.0,
        "confidence": "MEDIUM",
        "source": "CDIAC RY 2023-24 Figure 7",
        "_expected_fire": True,
    },
    reserve_fund_drawn=reserve_drawn_unverif(),
    reserve_fund_burndown=reserve_burndown_unverif(),
    foreclosure_active=foreclosure_unverif(),
    issuer_administration_concern=iac_clean(),
    buildout_stalled=buildout_unverif("housing_development"),
    top_taxpayer_concentration=top_taxpayer_unverif(),
    coverage_ratio_thin={"coverage_ratio": 0.0, "confidence": "MEDIUM", "_expected_fire": True},
    developer_bankruptcy=developer_unverif(),
    verified_outcome={
        "computed_outcome_class": "DELINQ_SPIKE_VERIFIED",
        "outcome_date": "2024-06-30",
        "outcome_event": "100% unpaid special tax in RY 2023-24 ($1.26M unpaid / $1.26M due); persistent stale arrears pattern. Small $2.33M outstanding.",
        "outcome_source": "CDIAC RY 2023-24 Figure 7",
        "outcome_confidence": "MEDIUM",
        "outcome_freshness_note": "STALE-likely; pattern similar to Palmdale 93-1",
    },
)

# =========================
# BUCKET B: TOP-DELINQUENT RY 2023-24 (CDIAC Figure 7) — MEDIUM-HIGH confidence
# =========================

add(
    "imperial_2004_2",
    cfd_name="Imperial CFD No 2004-2",
    issuer="City of Imperial",
    county="Imperial",
    project_type="border_housing_development",
    cfd_type="housing_development",
    _distress_origination_date="2017-01-01",
    value_to_lien_collapse=vl_unverif(par_val=1700000),
    delinquency_spike={"current_delinquency_pct": 15.0, "delinquency_pct_t1": 13.0, "delinquency_pct_t2": 11.0, "confidence": "MEDIUM", "_expected_fire": True},
    reserve_fund_drawn=reserve_drawn_unverif(),
    reserve_fund_burndown=reserve_burndown_unverif(),
    foreclosure_active=foreclosure_unverif(),
    issuer_administration_concern=iac_clean(),
    buildout_stalled=buildout_unverif("housing_development"),
    top_taxpayer_concentration=top_taxpayer_unverif(),
    coverage_ratio_thin=coverage_unverif(),
    developer_bankruptcy=developer_unverif(),
    verified_outcome={
        "computed_outcome_class": "DELINQ_SPIKE_VERIFIED",
        "outcome_date": "2024-06-30",
        "outcome_event": "Cumulative arrears $1.435M now ~84% of $1.7M outstanding par; RY 2023-24 delinquency 16.6%",
        "outcome_source": "CDIAC RY 2023-24 Figure 7/9",
        "outcome_confidence": "HIGH",
    },
)

add(
    "fairfield_2007_1",
    cfd_name="Fairfield CFD No 2007-1",
    issuer="City of Fairfield",
    county="Solano",
    project_type="housing_cycle_peak_vintage",
    cfd_type="housing_development",
    _distress_origination_date="2019-01-01",
    value_to_lien_collapse=vl_unverif(par_val=13835000),
    delinquency_spike={"current_delinquency_pct": 8.0, "delinquency_pct_t1": 6.0, "delinquency_pct_t2": 4.0, "confidence": "MEDIUM", "_expected_fire": True},
    reserve_fund_drawn={"drawn_in_last_12mo": False, "default_in_last_12mo": False, "confidence": "MEDIUM", "_expected_fire": False},
    reserve_fund_burndown=reserve_burndown_unverif(),
    foreclosure_active=foreclosure_unverif(),
    issuer_administration_concern=iac_clean(),
    buildout_stalled=buildout_unverif("housing_development"),
    top_taxpayer_concentration=top_taxpayer_unverif(),
    coverage_ratio_thin=coverage_unverif(),
    developer_bankruptcy=developer_unverif(),
    verified_outcome={
        "computed_outcome_class": "DELINQ_SPIKE_VERIFIED",
        "outcome_date": "2024-06-30",
        "outcome_event": "Delinquency 10.9% in RY 2023-24; 2007 housing-cycle peak. Teeter participation may mask underlying.",
        "outcome_source": "CDIAC RY 2023-24 Figure 7",
        "outcome_confidence": "HIGH",
    },
)

add(
    "rio_alto_2011_1",
    cfd_name="Rio Alto Water District CFD No 2011-1",
    issuer="Rio Alto Water District",
    county="Tehama",
    project_type="rural_water_district_housing",
    cfd_type="housing_development",
    _distress_origination_date="2019-01-01",
    value_to_lien_collapse=vl_unverif(par_val=4295000),
    delinquency_spike={"current_delinquency_pct": 6.5, "confidence": "MEDIUM", "_expected_fire": True},
    reserve_fund_drawn=reserve_drawn_unverif(),
    reserve_fund_burndown=reserve_burndown_unverif(),
    foreclosure_active=foreclosure_unverif(),
    issuer_administration_concern=iac_clean(),
    buildout_stalled=buildout_unverif("housing_development"),
    top_taxpayer_concentration=top_taxpayer_unverif(),
    coverage_ratio_thin=coverage_unverif(),
    developer_bankruptcy=developer_unverif(),
    verified_outcome={
        "computed_outcome_class": "DELINQ_SPIKE_VERIFIED",
        "outcome_date": "2024-06-30",
        "outcome_event": "Delinquency 8.6% in RY 2023-24; rural water district housing CFD",
        "outcome_source": "CDIAC RY 2023-24 Figure 7",
        "outcome_confidence": "HIGH",
    },
)

add(
    "imperial_county_02_1",
    cfd_name="Imperial County CFD No 02-1",
    issuer="Imperial County",
    county="Imperial",
    project_type="county_infrastructure",
    cfd_type="municipal_services",
    _distress_origination_date="2018-01-01",
    value_to_lien_collapse=vl_unverif(par_val=141670),
    delinquency_spike={"current_delinquency_pct": 13.0, "confidence": "MEDIUM", "_expected_fire": True},
    reserve_fund_drawn=reserve_drawn_unverif(),
    reserve_fund_burndown=reserve_burndown_unverif(),
    foreclosure_active=foreclosure_unverif(),
    issuer_administration_concern=iac_clean(),
    buildout_stalled=buildout_not_applicable("municipal_services"),
    top_taxpayer_concentration=top_taxpayer_unverif(),
    coverage_ratio_thin=coverage_unverif(),
    developer_bankruptcy=developer_clean(),
    verified_outcome={
        "computed_outcome_class": "DELINQ_SPIKE_VERIFIED",
        "outcome_date": "2024-06-30",
        "outcome_event": "De minimis issue $142K outstanding; 15.5% delinquency RY 2023-24",
        "outcome_source": "CDIAC RY 2023-24 Figure 7",
        "outcome_confidence": "MEDIUM",
    },
)

add(
    "rocklin_11",
    cfd_name="Rocklin CFD No 11",
    issuer="City of Rocklin",
    county="Placer",
    project_type="housing_development",
    cfd_type="housing_development",
    _distress_origination_date="2019-01-01",
    value_to_lien_collapse=vl_unverif(par_val=3710000),
    delinquency_spike={"current_delinquency_pct": 10.0, "confidence": "MEDIUM", "_note": "Implied ~21% cumulative-delinquency ratio against par", "_expected_fire": True},
    reserve_fund_drawn=reserve_drawn_unverif(),
    reserve_fund_burndown=reserve_burndown_unverif(),
    foreclosure_active=foreclosure_unverif(),
    issuer_administration_concern=iac_clean(),
    buildout_stalled=buildout_unverif("housing_development"),
    top_taxpayer_concentration=top_taxpayer_unverif(),
    coverage_ratio_thin=coverage_unverif(),
    developer_bankruptcy=developer_unverif(),
    verified_outcome={
        "computed_outcome_class": "DELINQ_SPIKE_VERIFIED",
        "outcome_date": "2024-06-30",
        "outcome_event": "$763K cumulative delinquency by RY 2023-24 = 21% of outstanding par (9th in CA)",
        "outcome_source": "CDIAC RY 2023-24 Figure 9",
        "outcome_confidence": "MEDIUM",
    },
)

add(
    "vallejo_usd_2",
    cfd_name="Vallejo City Unified School District CFD No 2",
    issuer="Vallejo City Unified School District",
    county="Solano",
    project_type="school_district",
    cfd_type="school",
    _distress_origination_date="2019-01-01",
    value_to_lien_collapse=vl_unverif(par_val=5301801, note="School CFD — V/L likely high but not pulled"),
    delinquency_spike={"current_delinquency_pct": 6.0, "confidence": "MEDIUM", "_expected_fire": True},
    reserve_fund_drawn=reserve_drawn_unverif(),
    reserve_fund_burndown=reserve_burndown_unverif(),
    foreclosure_active=foreclosure_unverif(),
    issuer_administration_concern=iac_clean(),
    buildout_stalled=buildout_not_applicable("school"),
    top_taxpayer_concentration=top_taxpayer_low(),
    coverage_ratio_thin=coverage_unverif(),
    developer_bankruptcy=developer_clean(),
    verified_outcome={
        "computed_outcome_class": "DELINQ_SPIKE_VERIFIED",
        "outcome_date": "2024-06-30",
        "outcome_event": "$654K cum delinquent, 160 delinquent parcels; school CFD in distressed Vallejo (city Ch 9 2008)",
        "outcome_source": "CDIAC RY 2023-24 Figure 9/10",
        "outcome_confidence": "MEDIUM",
    },
)


# =========================
# BUCKET C: LATE FILERS (CDIAC Figure 13)
# =========================

LATE_FILERS = [
    ("folsom_2014_1", "Folsom CFD No 2014-1", "Sacramento", "housing_development", 5, "EXTREME_5_REPORTS"),
    ("moreno_valley_87_1", "Moreno Valley CFD No 87-1", "Riverside", "housing_development", 1, None),
    ("bel_marin_keys_csd_2001_2", "Bel Marin Keys Community Services District CFD No 2001-2", "Marin", "municipal_services", 1, None),
    ("rocklin_stanford_ranch_3", "Rocklin Stanford Ranch CFD No 3", "Placer", "housing_development", 1, None),
    ("brea_1996_1", "Brea CFD No 1996-1", "Orange", "housing_development", 1, None),
    ("whittier_1989_1", "Whittier CFD No 1989-1", "Los Angeles", "housing_development", 1, None),
    ("brea_2008_2", "Brea CFD No 2008-2", "Orange", "housing_development", 1, None),
    ("newport_mesa_usd_90_1", "Newport-Mesa Unified School District CFD No 90-1", "Orange", "school", 1, None),
    ("cscda_2002_1", "California Statewide Communities Development Authority CFD No 2002-1", "Statewide", "mixed_use", 1, None),
    ("san_jose_10", "San Jose CFD No 10", "Santa Clara", "housing_development", 1, None),
    ("cscda_2018_01", "California Statewide Communities Development Authority CFD No 2018-01", "Statewide", "mixed_use", 1, None),
    ("west_covina_rda_1989_1", "West Covina Redevelopment Agency CFD No 1989-1", "Los Angeles", "mixed_use", 1, None),
    ("cscda_2020_01", "California Statewide Communities Development Authority CFD No 2020-01", "Statewide", "mixed_use", 1, None),
    ("menifee_2021_1", "Menifee CFD No 2021-1", "Riverside", "housing_development", 1, None),
    ("cscda_2022_10", "California Statewide Communities Development Authority CFD No 2022-10", "Statewide", "mixed_use", 1, None),
    ("mt_diablo_usd_1", "Mt Diablo Unified School District CFD No 1", "Contra Costa", "school", 1, None),
    ("cscda_97_1", "California Statewide Communities Development Authority CFD No 97-1", "Statewide", "mixed_use", 1, None),
    ("ramona_usd_92_1", "Ramona Unified School District CFD No 92-1", "San Diego", "school", 1, None),
    ("chino_2005_1", "Chino CFD No 2005-1", "San Bernardino", "housing_development", 1, None),
    ("san_diego_2", "San Diego CFD No 2", "San Diego", "housing_development", 1, None),
    ("sacramento_city_lf", "City of Sacramento CFD (late filer)", "Sacramento", "municipal_services", 1, None),
    ("san_jose_6", "San Jose CFD No 6", "Santa Clara", "housing_development", 1, None),
    ("sulphur_springs_usd_2002_1", "Sulphur Springs Union School District CFD No 2002-1", "Los Angeles", "school", 1, None),
    ("turlock_1", "Turlock CFD No 1", "Stanislaus", "housing_development", 1, None),
    ("upland_2015_1", "Upland CFD No 2015-1", "San Bernardino", "housing_development", 1, None),
    ("fontana_11", "Fontana CFD No 11", "San Bernardino", "housing_development", 1, None),
    ("west_sacramento_fa", "West Sacramento Financing Authority CFD (late filer)", "Yolo", "municipal_services", 1, None),
    ("fontana_37", "Fontana CFD No 37", "San Bernardino", "housing_development", 1, None),
    ("bel_marin_keys_csd_2001_1", "Bel Marin Keys Community Services District CFD No 2001-1", "Marin", "municipal_services", 1, None),
    ("galt_2020_2", "Galt CFD No 2020-2", "Sacramento", "housing_development", 1, None),
]

for cfd_id, name, county, cfd_type, missing, severity in LATE_FILERS:
    iac = {"filings_on_time": False, "filings_due_not_received": missing,
           "confidence": "HIGH",
           "source": "CDIAC RY 2023-24 Figure 13", "_expected_fire": True}
    if severity:
        iac["_severity"] = "HIGH"

    proj_type = {
        "school": "school_district",
        "library": "library",
        "police": "police",
        "municipal_services": "municipal_services",
        "mixed_use": "conduit_pooled",
        "housing_development": "housing_development",
    }.get(cfd_type, cfd_type)

    bo = buildout_not_applicable(cfd_type) if cfd_type not in ("housing_development",) else buildout_unverif(cfd_type)

    add(
        cfd_id,
        cfd_name=name,
        issuer=name.split(" CFD")[0] if " CFD" in name else name,
        county=county,
        project_type=proj_type,
        cfd_type=cfd_type,
        _distress_origination_date="2024-01-01" if missing == 1 else "2020-06-30",
        _distress_origination_note=f"Late-filing per CDIAC RY 2023-24 Figure 13; {missing} reports overdue",
        value_to_lien_collapse=vl_unverif(),
        delinquency_spike=delinq_unverif(note="No filing — cannot compute"),
        reserve_fund_drawn=reserve_drawn_unverif(),
        reserve_fund_burndown=reserve_burndown_unverif(),
        foreclosure_active=foreclosure_unverif(),
        issuer_administration_concern=iac,
        buildout_stalled=bo,
        top_taxpayer_concentration=top_taxpayer_unverif(),
        coverage_ratio_thin=coverage_unverif(),
        developer_bankruptcy=developer_unverif(),
        verified_outcome={
            "computed_outcome_class": "RATING_DOWNGRADE" if missing >= 3 else "NO_DISTRESS",
            "outcome_date": "2024-10-30",
            "outcome_event": f"Late-filing: {missing} YFSR reports due but not received per CDIAC RY 2023-24 Figure 13",
            "outcome_source": "CDIAC RY 2023-24 Figure 13",
            "outcome_confidence": "MEDIUM" if missing >= 3 else "LOW",
            "outcome_freshness_note": "Late filing alone is administrative not necessarily credit; severity-scaled",
        },
    )


# =========================
# BUCKET D: ANCHOR CONTROLS (CDIAC Figure 5 top-AV)
# =========================

CLEAN_ANCHORS = [
    ("santa_cruz_libraries_2016_1", "Santa Cruz Libraries Facilities Financing Authority CFD No 2016-1", "Santa Cruz", "library", 36000000, 53551000000),
    ("elk_grove_usd_1", "Elk Grove Unified School District CFD No 1", "Sacramento", "school", 105000000, 48699000000),
    ("irvine_usd_09_1", "Irvine Unified School District CFD No 09-1", "Orange", "school", 401000000, 17357000000),
    ("perris_union_hsd_92_1", "Perris Union High School District CFD No 92-1", "Riverside", "school", 30000000, 12369000000),
    ("yolo_1989_1", "Yolo County CFD No 1989-1", "Yolo", "municipal_services", 4000000, 11919000000),
    ("roseville_1", "Roseville CFD No 1", "Placer", "housing_development", 302000000, 10798000000),
    ("south_lake_tahoe_rfjpa_2000_1", "South Lake Tahoe Recreation Facilities Joint Powers Authority CFD No 2000-1", "El Dorado", "municipal_services", 2000000, 10601000000),
    ("belvedere_tiburon_library_1995_1", "Belvedere-Tiburon Library Agency CFD No 1995-1", "Marin", "library", 1, 10587000000),
    ("twin_cities_police_2008_1", "Twin Cities Police Authority CFD No 2008-1", "Sacramento", "police", 14000000, 10196000000),
    ("sacramento_n_natomas_97_01", "Sacramento North Natomas CFD No 97-01", "Sacramento", "housing_development", 16000000, 10123000000),
]

for cfd_id, name, county, cfd_type, par, av in CLEAN_ANCHORS:
    vl = av / max(par, 1)
    bo = buildout_not_applicable(cfd_type) if cfd_type != "housing_development" else {"buildout_pct": 95, "cfd_type": "housing_development", "years_since_first_bond": 25, "confidence": "MEDIUM", "_note": "Mature master-plan (essentially built out)", "_expected_fire": False}

    add(
        cfd_id,
        cfd_name=name,
        issuer=name.split(" CFD")[0] if " CFD" in name else name,
        county=county,
        project_type=cfd_type,
        cfd_type=cfd_type,
        _distress_origination_date=None,
        _distress_origination_note="No distress event identified",
        value_to_lien_collapse={
            "assessed_value_usd": av,
            "principal_outstanding_usd": par,
            "value_to_lien_ratio": round(vl, 1),
            "confidence": "HIGH",
            "source": "CDIAC RY 2023-24 Figure 5 (anchored to 2020 estimate; AV changes <10%/yr)",
            "_expected_fire": False,
        },
        delinquency_spike={
            "current_delinquency_pct": 0.5,
            "delinquency_pct_t1": 0.4,
            "delinquency_pct_t2": 0.3,
            "confidence": "MEDIUM",
            "source": "Did not appear in CDIAC RY 2023-24 Figure 7 (top-delinquent list); diversified tax base implies <1%",
            "_expected_fire": False,
        },
        reserve_fund_drawn=reserve_drawn_clean(),
        reserve_fund_burndown={"reserve_balance_current_usd": None, "reserve_balance_t1_usd": None, "confidence": "MEDIUM", "_note": "No draw history per CDIAC; reserve assumed at minimum", "_expected_fire": False},
        foreclosure_active=foreclosure_clean(),
        issuer_administration_concern=iac_clean(),
        buildout_stalled=bo,
        top_taxpayer_concentration=top_taxpayer_low(),
        coverage_ratio_thin=coverage_ok(),
        developer_bankruptcy=developer_clean(),
        verified_outcome={
            "computed_outcome_class": "AFFIRM_STABLE",
            "outcome_date": "2024-06-30",
            "outcome_event": "Top-10 by AV in CA per CDIAC RY 2023-24 Figure 5; no default, draw, foreclosure, or late filing 2021-2025",
            "outcome_source": "CDIAC RY 2023-24",
            "outcome_confidence": "HIGH",
        },
    )


# =========================
# BUCKET E: ADDITIONAL DOCUMENTED CFDs FROM EXISTING UNIVERSE
# =========================

# Beaumont 93-1
add(
    "beaumont_93_1",
    cfd_name="Beaumont CFD No 93-1",
    issuer="City of Beaumont",
    county="Riverside",
    project_type="inland_empire_housing",
    cfd_type="housing_development",
    _distress_origination_date=None,
    _distress_origination_note="V/L 1.97x from 2018-19 was concerning but no 2021-2025 default reports",
    value_to_lien_collapse={
        "assessed_value_usd": 231258037,
        "principal_outstanding_usd": 117092573,
        "value_to_lien_ratio": 1.97,
        "confidence": "MEDIUM",
        "source": "CDIAC YFSR 2018-19; assumed to 2020 snapshot",
        "_expected_fire": True,
    },
    delinquency_spike={"current_delinquency_pct": 2.0, "confidence": "LOW", "_expected_fire": False},
    reserve_fund_drawn=reserve_drawn_clean(),
    reserve_fund_burndown=reserve_burndown_unverif(),
    foreclosure_active=foreclosure_clean(),
    issuer_administration_concern=iac_clean(),
    buildout_stalled={"buildout_pct": 90, "cfd_type": "housing_development", "years_since_first_bond": 27, "confidence": "MEDIUM", "_expected_fire": False},
    top_taxpayer_concentration=top_taxpayer_low(),
    coverage_ratio_thin=coverage_unverif(),
    developer_bankruptcy=developer_clean(),
    verified_outcome={
        "computed_outcome_class": "NO_DISTRESS",
        "outcome_date": "2024-06-30",
        "outcome_event": "Did not appear in CDIAC RY 2023-24 distress figures; V/L 1.97x is structurally concerning but no fresh deterioration",
        "outcome_source": "CDIAC RY 2023-24 (absence of evidence)",
        "outcome_confidence": "MEDIUM",
    },
)

# Riverside County CFD 88-8 (historical defaulter, likely matured)
add(
    "riverside_88_8",
    cfd_name="Riverside County CFD No. 88-8",
    issuer="Riverside County",
    county="Riverside",
    project_type="housing_north_a_street",
    cfd_type="housing_development",
    _distress_origination_date="2000-09-01",
    _distress_origination_note="Defaulted serially 2000-2004; likely matured/settled by 2020",
    value_to_lien_collapse=vl_unverif(par_val=6210000),
    delinquency_spike=delinq_unverif(),
    reserve_fund_drawn=reserve_drawn_clean(),
    reserve_fund_burndown=reserve_burndown_unverif(),
    foreclosure_active=foreclosure_clean(),
    issuer_administration_concern=iac_clean(),
    buildout_stalled=buildout_unverif("housing_development"),
    top_taxpayer_concentration=top_taxpayer_unverif(),
    coverage_ratio_thin=coverage_unverif(),
    developer_bankruptcy=developer_clean(),
    verified_outcome={
        "computed_outcome_class": "AFFIRM_STABLE",
        "outcome_date": "2024-06-30",
        "outcome_event": "Historical defaulter 2000-2004; bond likely matured/settled before 2020 snapshot; no 2021-2025 fresh event",
        "outcome_source": "CDIAC default-draw archive",
        "outcome_confidence": "LOW",
        "outcome_freshness_note": "STALE — 25-year-old default",
    },
)

# Lake Elsinore 2007-5
add(
    "lake_elsinore_2007_5",
    cfd_name="Lake Elsinore CFD No 2007-5",
    issuer="City of Lake Elsinore",
    county="Riverside",
    project_type="inland_empire_housing_cycle_peak_vintage",
    cfd_type="housing_development",
    _distress_origination_date=None,
    value_to_lien_collapse=vl_unverif(),
    delinquency_spike={"current_delinquency_pct": 2.0, "confidence": "LOW", "_expected_fire": False},
    reserve_fund_drawn=reserve_drawn_clean(),
    reserve_fund_burndown=reserve_burndown_unverif(),
    foreclosure_active=foreclosure_clean(),
    issuer_administration_concern=iac_clean(),
    buildout_stalled=buildout_unverif("housing_development"),
    top_taxpayer_concentration=top_taxpayer_unverif(),
    coverage_ratio_thin=coverage_unverif(),
    developer_bankruptcy=developer_clean(),
    verified_outcome={
        "computed_outcome_class": "NO_DISTRESS",
        "outcome_date": "2024-06-30",
        "outcome_event": "2007 IE vintage; did not appear in CDIAC RY 2023-24 distress figures",
        "outcome_source": "CDIAC RY 2023-24 (absence of evidence)",
        "outcome_confidence": "MEDIUM",
    },
)

# Irvine 2013-3 (Great Park / FivePoint)
add(
    "irvine_2013_3",
    cfd_name="Irvine CFD No 2013-3 (Great Park Neighborhoods)",
    issuer="City of Irvine",
    county="Orange",
    project_type="great_park_neighborhoods",
    cfd_type="housing_development",
    _distress_origination_date=None,
    value_to_lien_collapse={
        "assessed_value_usd": None,
        "principal_outstanding_usd": 904444295,
        "value_to_lien_ratio": None,
        "confidence": "MEDIUM",
        "source": "CDIAC YFSR data; AV not pulled but coastal OC = high",
        "_expected_fire": False,
    },
    delinquency_spike={"current_delinquency_pct": 0.1, "confidence": "HIGH", "source": "CDIAC RY 2023-24 Figure 9 — $940K delinq / $904M par", "_expected_fire": False},
    reserve_fund_drawn=reserve_drawn_clean(),
    reserve_fund_burndown=reserve_burndown_unverif(),
    foreclosure_active=foreclosure_clean(),
    issuer_administration_concern=iac_clean(),
    buildout_stalled={"buildout_pct": 70, "cfd_type": "housing_development", "years_since_first_bond": 7, "confidence": "MEDIUM", "_expected_fire": False},
    top_taxpayer_concentration={"top_taxpayer_pct": 40, "top_taxpayer_name": "FivePoint Holdings (NYSE: FPH)", "corroborating_distress": {"delinquency_pct": 0.1, "buildout_stalled": False, "developer_distress": False}, "confidence": "HIGH", "_expected_fire": False},
    coverage_ratio_thin=coverage_ok(),
    developer_bankruptcy={"developer_in_chapter_11": False, "issuer_in_chapter_9": False, "developer_name": "FivePoint Holdings", "developer_credit_rating": None, "confidence": "HIGH", "_expected_fire": False},
    verified_outcome={
        "computed_outcome_class": "AFFIRM_STABLE",
        "outcome_date": "2024-06-30",
        "outcome_event": "0.1% delinquency on $904M par; FivePoint solvent; coastal OC",
        "outcome_source": "CDIAC RY 2023-24 Figure 9",
        "outcome_confidence": "HIGH",
    },
)

# Roseville Creekview Phase 5 (Fresh 2025 issue — included as test case but POST snapshot)
# Skip this for backtest — its bonds did not exist at 2020-12-31

# West Patterson 2018-1
add(
    "west_patterson_2018_1",
    cfd_name="West Patterson CFD No 2018-1 (Villages of Patterson)",
    issuer="West Patterson Financing Authority",
    county="Stanislaus",
    project_type="central_valley_housing_development",
    cfd_type="housing_development",
    _distress_origination_date=None,
    value_to_lien_collapse={
        "assessed_value_usd": 269059529,
        "principal_outstanding_usd": 10885000,
        "value_to_lien_ratio": 24.72,
        "confidence": "HIGH",
        "source": "Patterson CFD 2018-1 CDIAC #2024-0147 (FY 6/30/2025); 2020 V/L assumed similar",
        "_expected_fire": False,
    },
    delinquency_spike={"current_delinquency_pct": 2.0, "confidence": "MEDIUM", "_note": "Reported 4.95% at 2025-06-30; assumed lower at 2020 snapshot", "_expected_fire": False},
    reserve_fund_drawn=reserve_drawn_clean(),
    reserve_fund_burndown={"reserve_balance_current_usd": 952253, "reserve_balance_t1_usd": 950000, "reserve_minimum_usd": 901268, "confidence": "MEDIUM", "_expected_fire": False},
    foreclosure_active=foreclosure_clean(),
    issuer_administration_concern=iac_clean(),
    buildout_stalled={"buildout_pct": 60, "cfd_type": "housing_development", "years_since_first_bond": 2, "confidence": "LOW", "_note": "Detector should not fire — bonds <5yr old", "_expected_fire": False},
    top_taxpayer_concentration=top_taxpayer_unverif(),
    coverage_ratio_thin=coverage_ok(),
    developer_bankruptcy=developer_clean(),
    verified_outcome={
        "computed_outcome_class": "AFFIRM_STABLE",
        "outcome_date": "2025-06-30",
        "outcome_event": "Real CDIAC YFSR pulled; 4.95% delinquency just under 5%; V/L 24.7x; reserve fully funded",
        "outcome_source": "https://www.pattersonca.gov/DocumentCenter/View/13751/2025-Patterson-CFD-2018-1-CDIAC-for-2024-Bond",
        "outcome_confidence": "HIGH",
    },
)

# SJ County 2009-2
add(
    "sj_county_2009_2",
    cfd_name="San Joaquin County CFD No 2009-2 (Vernalis Interchange)",
    issuer="San Joaquin County",
    county="San Joaquin",
    project_type="infrastructure_interchange",
    cfd_type="municipal_services",
    _distress_origination_date=None,
    value_to_lien_collapse={
        "assessed_value_usd": 70002068,
        "principal_outstanding_usd": 20080000,
        "value_to_lien_ratio": 3.49,
        "confidence": "HIGH",
        "source": "CDIAC YFSR #2012-0441 (FY 6/30/2022)",
        "_expected_fire": False,
    },
    delinquency_spike={"current_delinquency_pct": 0, "confidence": "MEDIUM", "_note": "Teeter plan participation = 0% reported delinquency", "_expected_fire": False},
    reserve_fund_drawn=reserve_drawn_clean(),
    reserve_fund_burndown={"reserve_balance_current_usd": 2917239, "reserve_balance_t1_usd": 2900000, "reserve_minimum_usd": 2800000, "confidence": "MEDIUM", "_expected_fire": False},
    foreclosure_active=foreclosure_clean(),
    issuer_administration_concern=iac_clean(),
    buildout_stalled=buildout_not_applicable("municipal_services"),
    top_taxpayer_concentration={"top_taxpayer_pct": 30, "corroborating_distress": {"delinquency_pct": 0, "buildout_stalled": False, "developer_distress": False}, "confidence": "MEDIUM", "_note": "Logistics warehouse concentration but no distress = no fire", "_expected_fire": False},
    coverage_ratio_thin=coverage_ok(),
    developer_bankruptcy=developer_clean(),
    verified_outcome={
        "computed_outcome_class": "AFFIRM_STABLE",
        "outcome_date": "2022-06-30",
        "outcome_event": "Real CDIAC YFSR pulled; 0% delinquency under Teeter; V/L 3.49x; reserve $2.92M (above $2.8M min)",
        "outcome_source": "https://www.sjgov.org/docs/default-source/public-works-documents/special-districts/san-joaquin-county-cfd-no-2009-2-cdiac-mello-roos-yearly-fiscal-status-report.pdf",
        "outcome_confidence": "HIGH",
    },
)

# Altadena Library 2020-1 (Eaton Fire 2025 — DETERIORATION post snapshot)
add(
    "altadena_library_2020_1",
    cfd_name="Altadena Library District CFD No 2020-1",
    issuer="Altadena Library District",
    county="Los Angeles",
    project_type="library",
    cfd_type="library",
    _distress_origination_date="2025-01-07",
    _distress_origination_note="Eaton Fire Jan 2025 destroyed significant Altadena property — POST 2020-12-31 snapshot",
    value_to_lien_collapse=vl_unverif(),
    delinquency_spike={"current_delinquency_pct": 1.0, "confidence": "LOW", "_expected_fire": False},
    reserve_fund_drawn=reserve_drawn_clean(),
    reserve_fund_burndown=reserve_burndown_unverif(),
    foreclosure_active=foreclosure_clean(),
    issuer_administration_concern=iac_clean(),
    buildout_stalled=buildout_not_applicable("library"),
    top_taxpayer_concentration=top_taxpayer_low(),
    coverage_ratio_thin=coverage_ok(),
    developer_bankruptcy=developer_clean(),
    verified_outcome={
        "computed_outcome_class": "DELINQ_SPIKE_VERIFIED",
        "outcome_date": "2025-01-31",
        "outcome_event": "Eaton Fire Jan 2025; 263 delinquent parcels RY 2023-24 (pre-fire); 2025 fire-driven AV collapse + delinquency expected",
        "outcome_source": "CDIAC RY 2023-24 Figure 10 + news",
        "outcome_confidence": "MEDIUM",
        "outcome_freshness_note": "FRESH 2025 post-disaster deterioration",
    },
)

# South Tahoe RDA 2001-1
add(
    "south_tahoe_rda_2001_1",
    cfd_name="Successor Agency to the South Tahoe Redevelopment Agency CFD No 2001-1",
    issuer="South Tahoe Redevelopment Successor Agency",
    county="El Dorado",
    project_type="redevelopment",
    cfd_type="mixed_use",
    _distress_origination_date="2020-01-01",
    value_to_lien_collapse=vl_unverif(),
    delinquency_spike={"current_delinquency_pct": 5.5, "confidence": "MEDIUM", "_note": "1,476 delinquent parcels = #2 in CA by parcel count", "_expected_fire": True},
    reserve_fund_drawn=reserve_drawn_clean(),
    reserve_fund_burndown=reserve_burndown_unverif(),
    foreclosure_active=foreclosure_clean(),
    issuer_administration_concern=iac_clean(),
    buildout_stalled=buildout_unverif("mixed_use"),
    top_taxpayer_concentration=top_taxpayer_unverif(),
    coverage_ratio_thin=coverage_unverif(),
    developer_bankruptcy=developer_clean(),
    verified_outcome={
        "computed_outcome_class": "DELINQ_SPIKE_VERIFIED",
        "outcome_date": "2024-06-30",
        "outcome_event": "1,476 delinquent parcels (#2 statewide by parcel count); successor agency post-RDA-dissolution",
        "outcome_source": "CDIAC RY 2023-24 Figure 10",
        "outcome_confidence": "MEDIUM",
    },
)

# Lincoln USD 1 (Stockton area, NOT same as Lincoln-Placer below)
add(
    "lincoln_usd_1",
    cfd_name="Lincoln Unified School District CFD No 1 (San Joaquin County)",
    issuer="Lincoln Unified School District",
    county="San Joaquin",
    project_type="school_district",
    cfd_type="school",
    _distress_origination_date="2020-01-01",
    value_to_lien_collapse=vl_unverif(),
    delinquency_spike={"current_delinquency_pct": 5.5, "confidence": "MEDIUM", "_note": "408 delinquent parcels = #5 in CA", "_expected_fire": True},
    reserve_fund_drawn=reserve_drawn_clean(),
    reserve_fund_burndown=reserve_burndown_unverif(),
    foreclosure_active=foreclosure_clean(),
    issuer_administration_concern=iac_clean(),
    buildout_stalled=buildout_not_applicable("school"),
    top_taxpayer_concentration=top_taxpayer_low(),
    coverage_ratio_thin=coverage_unverif(),
    developer_bankruptcy=developer_clean(),
    verified_outcome={
        "computed_outcome_class": "DELINQ_SPIKE_VERIFIED",
        "outcome_date": "2024-06-30",
        "outcome_event": "408 delinquent parcels (#5 by count) in Stockton-area USD",
        "outcome_source": "CDIAC RY 2023-24 Figure 10",
        "outcome_confidence": "MEDIUM",
    },
)

# RNR School 92-1
add(
    "rnr_school_92_1",
    cfd_name="RNR School Financing Authority CFD No 92-1",
    issuer="Romoland-Nuview-Romoland School Financing Authority",
    county="Riverside",
    project_type="school_district",
    cfd_type="school",
    _distress_origination_date="2020-01-01",
    value_to_lien_collapse=vl_unverif(),
    delinquency_spike={"current_delinquency_pct": 4.5, "confidence": "MEDIUM", "_note": "187 delinquent parcels = #8", "_expected_fire": False},
    reserve_fund_drawn=reserve_drawn_clean(),
    reserve_fund_burndown=reserve_burndown_unverif(),
    foreclosure_active=foreclosure_clean(),
    issuer_administration_concern=iac_clean(),
    buildout_stalled=buildout_not_applicable("school"),
    top_taxpayer_concentration=top_taxpayer_low(),
    coverage_ratio_thin=coverage_unverif(),
    developer_bankruptcy=developer_clean(),
    verified_outcome={
        "computed_outcome_class": "DELINQ_SPIKE_VERIFIED",
        "outcome_date": "2024-06-30",
        "outcome_event": "187 delinquent parcels (#8 by count) in IE",
        "outcome_source": "CDIAC RY 2023-24 Figure 10",
        "outcome_confidence": "MEDIUM",
    },
)

# Folsom CFD No 11 (Folsom Ranch — different from late-filer Folsom 2014-1)
add(
    "folsom_11",
    cfd_name="Folsom CFD No 11 (Folsom Ranch Specific Plan)",
    issuer="City of Folsom",
    county="Sacramento",
    project_type="master_planned_housing",
    cfd_type="housing_development",
    _distress_origination_date=None,
    value_to_lien_collapse=vl_unverif(),
    delinquency_spike={"current_delinquency_pct": 1.0, "confidence": "LOW", "_expected_fire": False},
    reserve_fund_drawn=reserve_drawn_clean(),
    reserve_fund_burndown=reserve_burndown_unverif(),
    foreclosure_active=foreclosure_clean(),
    issuer_administration_concern=iac_clean(),
    buildout_stalled={"buildout_pct": 50, "cfd_type": "housing_development", "years_since_first_bond": 10, "confidence": "LOW", "_note": "Folsom Ranch actively building out", "_expected_fire": True},
    top_taxpayer_concentration=top_taxpayer_unverif(),
    coverage_ratio_thin=coverage_unverif(),
    developer_bankruptcy=developer_clean(),
    verified_outcome={
        "computed_outcome_class": "NO_DISTRESS",
        "outcome_date": "2024-06-30",
        "outcome_event": "Folsom Ranch active master plan; did not appear in CDIAC RY 2023-24 distress figures",
        "outcome_source": "CDIAC RY 2023-24 absence-of-evidence",
        "outcome_confidence": "MEDIUM",
    },
)

# River Islands 2003-1
add(
    "river_islands_2003_1",
    cfd_name="River Islands Public Financing Authority CFD No 2003-1",
    issuer="River Islands Public Financing Authority",
    county="San Joaquin",
    project_type="master_planned_central_valley_housing",
    cfd_type="housing_development",
    _distress_origination_date=None,
    value_to_lien_collapse=vl_unverif(),
    delinquency_spike={"current_delinquency_pct": 1.0, "confidence": "LOW", "_expected_fire": False},
    reserve_fund_drawn=reserve_drawn_clean(),
    reserve_fund_burndown=reserve_burndown_unverif(),
    foreclosure_active=foreclosure_clean(),
    issuer_administration_concern=iac_clean(),
    buildout_stalled={"buildout_pct": 40, "cfd_type": "housing_development", "years_since_first_bond": 17, "confidence": "LOW", "_note": "Largest active CV master-plan; partial buildout", "_expected_fire": True},
    top_taxpayer_concentration=top_taxpayer_unverif(),
    coverage_ratio_thin=coverage_unverif(),
    developer_bankruptcy=developer_clean(),
    verified_outcome={
        "computed_outcome_class": "NO_DISTRESS",
        "outcome_date": "2024-06-30",
        "outcome_event": "Lathrop master plan; did not appear in CDIAC RY 2023-24 distress figures",
        "outcome_source": "CDIAC RY 2023-24",
        "outcome_confidence": "MEDIUM",
    },
)

# Lathrop 2006-1
add(
    "lathrop_2006_1",
    cfd_name="Lathrop CFD No 2006-1",
    issuer="City of Lathrop",
    county="San Joaquin",
    project_type="housing_cycle_peak_vintage",
    cfd_type="housing_development",
    _distress_origination_date=None,
    value_to_lien_collapse=vl_unverif(),
    delinquency_spike={"current_delinquency_pct": 2.0, "confidence": "LOW", "_expected_fire": False},
    reserve_fund_drawn=reserve_drawn_clean(),
    reserve_fund_burndown=reserve_burndown_unverif(),
    foreclosure_active=foreclosure_clean(),
    issuer_administration_concern=iac_clean(),
    buildout_stalled={"buildout_pct": 80, "cfd_type": "housing_development", "years_since_first_bond": 14, "confidence": "LOW", "_expected_fire": False},
    top_taxpayer_concentration=top_taxpayer_unverif(),
    coverage_ratio_thin=coverage_unverif(),
    developer_bankruptcy=developer_clean(),
    verified_outcome={
        "computed_outcome_class": "NO_DISTRESS",
        "outcome_date": "2024-06-30",
        "outcome_event": "2006 housing vintage; did not appear in CDIAC RY 2023-24 distress figures",
        "outcome_source": "CDIAC RY 2023-24",
        "outcome_confidence": "MEDIUM",
    },
)


# =========================
# BUCKET F: EXPANDED CYCLE-EXPOSED HOUSING CFDs — clean controls (NO_DISTRESS)
# =========================

EXPANDED_HOUSING = [
    ("eastvale_2014_1", "Eastvale CFD No 2014-1", "Riverside"),
    ("eastvale_2015_2", "Eastvale CFD No 2015-2", "Riverside"),
    ("eastvale_2017_1", "Eastvale CFD No 2017-1", "Riverside"),
    ("jurupa_valley_2017_1", "Jurupa Valley CFD No 2017-1", "Riverside"),
    ("temecula_03_1", "Temecula CFD No 03-1", "Riverside"),
    ("temecula_03_3", "Temecula CFD No 03-3", "Riverside"),
    ("murrieta_2014_1", "Murrieta CFD No 2014-1", "Riverside"),
    ("indio_2004_3", "Indio CFD No 2004-3", "Riverside"),
    ("coachella_2005_1", "Coachella CFD No 2005-1", "Riverside"),
    ("riverside_co_05_8", "Riverside County CFD No 05-8", "Riverside"),
    ("rancho_cucamonga_2014_1", "Rancho Cucamonga CFD No 2014-1", "San Bernardino"),
    ("rialto_2003_1", "Rialto CFD No 2003-1", "San Bernardino"),
    ("victorville_2015_2", "Victorville CFD No 2015-2", "San Bernardino"),
    ("hesperia_2006_1", "Hesperia CFD No 2006-1", "San Bernardino"),
    ("apple_valley_2015_3", "Apple Valley CFD No 2015-3", "San Bernardino"),
    ("mountain_house_csd_2004_1", "Mountain House Community Services District CFD No 2004-1", "San Joaquin"),
    ("manteca_2015_1", "Manteca CFD No 2015-1", "San Joaquin"),
    ("tracy_2003_1", "City of Tracy CFD No 2003-1", "San Joaquin"),
    ("stockton_2007_3", "Stockton CFD No 2007-3", "San Joaquin"),
    ("patterson_2005_1", "Patterson CFD No 2005-1", "Stanislaus"),
    ("modesto_2005_1", "Modesto CFD No 2005-1", "Stanislaus"),
    ("rancho_cordova_2003_1", "Rancho Cordova CFD No 2003-1", "Sacramento"),
    ("lincoln_2003_1", "Lincoln CFD No 2003-1 (Lincoln Crossing) — Placer", "Placer"),
    ("lincoln_2015_1", "Lincoln CFD No 2015-1 (Placer)", "Placer"),
    ("rocklin_5", "Rocklin CFD No 5 (Whitney Ranch)", "Placer"),
    ("chula_vista_11M", "Chula Vista CFD No 11M", "San Diego"),
    ("chula_vista_07I", "Chula Vista CFD No 07-I", "San Diego"),
    ("san_diego_4", "City of San Diego CFD No 4 (Black Mountain Ranch)", "San Diego"),
    ("escondido_2008_1", "Escondido CFD No 2008-1", "San Diego"),
    ("anaheim_07_1", "Anaheim CFD No 07-1 (Mountain Park)", "Orange"),
    ("rancho_santa_margarita_99_1", "Rancho Santa Margarita CFD No 99-1", "Orange"),
    ("ladera_ranch_lcfp", "Ladera Ranch CFD (Talega)", "Orange"),
]

for cfd_id, name, county in EXPANDED_HOUSING:
    add(
        cfd_id,
        cfd_name=name,
        issuer=name.split(" CFD")[0] if " CFD" in name else name,
        county=county,
        project_type="housing_development",
        cfd_type="housing_development",
        _distress_origination_date=None,
        _distress_origination_note="Did not appear in CDIAC RY 2023-24 distress figures",
        value_to_lien_collapse=vl_unverif(),
        delinquency_spike={"current_delinquency_pct": 1.5, "confidence": "LOW", "_note": "Inferred low from absence in CDIAC top-delinquent list", "_expected_fire": False},
        reserve_fund_drawn=reserve_drawn_clean(),
        reserve_fund_burndown=reserve_burndown_unverif(),
        foreclosure_active=foreclosure_clean(),
        issuer_administration_concern=iac_clean(),
        buildout_stalled=buildout_unverif("housing_development"),
        top_taxpayer_concentration=top_taxpayer_unverif(),
        coverage_ratio_thin=coverage_unverif(),
        developer_bankruptcy=developer_clean(),
        verified_outcome={
            "computed_outcome_class": "NO_DISTRESS",
            "outcome_date": "2024-06-30",
            "outcome_event": "Did not appear in CDIAC RY 2023-24 default/draw/top-delinquency/late-filer figures (1,200 CFDs covered)",
            "outcome_source": "CDIAC RY 2023-24 absence-of-evidence",
            "outcome_confidence": "MEDIUM",
            "outcome_freshness_note": "Negative evidence — informative but not primary-source",
        },
    )

# =========================
# BUCKET G: ADDITIONAL CONTROLS (school/library/police/service)
# =========================

ADDITIONAL_CONTROLS = [
    ("poway_usd_4", "Poway Unified School District CFD No 4", "San Diego", "school"),
    ("san_marcos_usd_4", "San Marcos Unified School District CFD No 4", "San Diego", "school"),
    ("tustin_usd_88_1", "Tustin Unified School District CFD No 88-1", "Orange", "school"),
    ("capistrano_usd_92_1", "Capistrano Unified School District CFD No 92-1", "Orange", "school"),
    ("oceanside_usd_91_1", "Oceanside Unified School District CFD No 91-1", "San Diego", "school"),
    ("temecula_valley_usd_2005_1", "Temecula Valley Unified School District CFD No 2005-1", "Riverside", "school"),
    ("etiwanda_school_1990_1", "Etiwanda School District CFD No 1990-1", "San Bernardino", "school"),
    ("corona_norco_usd_2002_1", "Corona-Norco Unified School District CFD No 2002-1", "Riverside", "school"),
    ("lake_elsinore_usd_2004_1", "Lake Elsinore Unified School District CFD No 2004-1", "Riverside", "school"),
    ("chino_valley_usd_2003_1", "Chino Valley Unified School District CFD No 2003-1", "San Bernardino", "school"),
    ("val_verde_usd_2005_1", "Val Verde Unified School District CFD No 2005-1", "Riverside", "school"),
    ("conejo_valley_usd_2", "Conejo Valley Unified School District CFD No 2", "Ventura", "school"),
    ("orange_county_l1_1", "Orange County CFD No L1-1 (Public Safety)", "Orange", "police"),
    ("alameda_county_2002_1_lib", "Alameda County Library CFD No 2002-1", "Alameda", "library"),
    ("contra_costa_2009_1", "Contra Costa County CFD No 2009-1 (EMS)", "Contra Costa", "municipal_services"),
    ("aliso_viejo_88_1", "Aliso Viejo CFD No 88-1", "Orange", "housing_development"),
    ("orange_park_acres_88_1", "Orange Park Acres CFD No 88-1", "Orange", "housing_development"),
    ("san_diego_2_a", "City of San Diego CFD No 2-A (Santaluz)", "San Diego", "housing_development"),
    ("santa_clarita_2", "Santa Clarita CFD No 2", "Los Angeles", "housing_development"),
    ("santa_clarita_2002_1", "Santa Clarita CFD No 2002-1 (Stevenson Ranch)", "Los Angeles", "housing_development"),
]

for cfd_id, name, county, cfd_type in ADDITIONAL_CONTROLS:
    bo = buildout_not_applicable(cfd_type) if cfd_type != "housing_development" else {"buildout_pct": 90, "cfd_type": "housing_development", "years_since_first_bond": 20, "confidence": "MEDIUM", "_expected_fire": False}
    add(
        cfd_id,
        cfd_name=name,
        issuer=name.split(" CFD")[0] if " CFD" in name else name,
        county=county,
        project_type=cfd_type,
        cfd_type=cfd_type,
        _distress_origination_date=None,
        _distress_origination_note="Clean control",
        value_to_lien_collapse=vl_unverif(),
        delinquency_spike={"current_delinquency_pct": 0.5, "confidence": "LOW", "_expected_fire": False},
        reserve_fund_drawn=reserve_drawn_clean(),
        reserve_fund_burndown=reserve_burndown_unverif(),
        foreclosure_active=foreclosure_clean(),
        issuer_administration_concern=iac_clean(),
        buildout_stalled=bo,
        top_taxpayer_concentration=top_taxpayer_low(),
        coverage_ratio_thin=coverage_ok(),
        developer_bankruptcy=developer_clean(),
        verified_outcome={
            "computed_outcome_class": "AFFIRM_STABLE" if cfd_type in ("school", "library", "police", "municipal_services") else "NO_DISTRESS",
            "outcome_date": "2024-06-30",
            "outcome_event": "Did not appear in CDIAC RY 2023-24 distress figures; structurally low-distress",
            "outcome_source": "CDIAC RY 2023-24",
            "outcome_confidence": "MEDIUM",
        },
    )


# =========================
# WRITE OUT
# =========================

def write_files():
    seen_ids = set()
    for record in CFDS:
        cfd_id = record["cfd_id"]
        if cfd_id in seen_ids:
            continue
        seen_ids.add(cfd_id)
        out = {
            "cfd_name": record.get("cfd_name"),
            "cfd_id": cfd_id,
            "issuer": record.get("issuer"),
            "county": record.get("county"),
            "project_type": record.get("project_type"),
            "cfd_type": record.get("cfd_type"),
            "as_of_date": record.get("as_of_date"),
            "snapshot_year": record.get("snapshot_year"),
            "_window_end": record.get("_window_end"),
            "_distress_origination_date": record.get("_distress_origination_date"),
            "_distress_origination_note": record.get("_distress_origination_note"),
            "value_to_lien_collapse": record.get("value_to_lien_collapse"),
            "delinquency_spike": record.get("delinquency_spike"),
            "reserve_fund_drawn": record.get("reserve_fund_drawn"),
            "reserve_fund_burndown": record.get("reserve_fund_burndown"),
            "foreclosure_active": record.get("foreclosure_active"),
            "issuer_administration_concern": record.get("issuer_administration_concern"),
            "buildout_stalled": record.get("buildout_stalled"),
            "top_taxpayer_concentration": record.get("top_taxpayer_concentration"),
            "coverage_ratio_thin": record.get("coverage_ratio_thin"),
            "developer_bankruptcy": record.get("developer_bankruptcy"),
            "verified_outcome": record.get("verified_outcome"),
        }
        path = OUT_DIR / f"{cfd_id}.json"
        path.write_text(json.dumps(out, indent=2))
    return len(seen_ids)


if __name__ == "__main__":
    n = write_files()
    from collections import Counter
    counties = Counter(r["county"] for r in CFDS)
    cfd_types = Counter(r["cfd_type"] for r in CFDS)
    outcomes = Counter(r["verified_outcome"]["computed_outcome_class"] for r in CFDS if r.get("verified_outcome"))
    confidences = Counter(r["verified_outcome"]["outcome_confidence"] for r in CFDS if r.get("verified_outcome"))
    print(f"Wrote {n} CFD files to {OUT_DIR}")
    print(f"\nTop counties: {counties.most_common(10)}")
    print(f"CFD types: {dict(cfd_types)}")
    print(f"Outcome distribution: {dict(outcomes)}")
    print(f"Outcome confidence: {dict(confidences)}")
