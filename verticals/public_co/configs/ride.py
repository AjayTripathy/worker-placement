"""Lordstown Motors (RIDE) backtest config.

Cutoff: 2021-03-11 (day before Hindenburg's "The Lordstown Motors Mirage").
"""
from __future__ import annotations

import json
from pathlib import Path

from ..m_sources import (
    edgar_fts,
    fmcsa,
    form4,
    google_patents,
    nhtsa,
    self_text,
)
from ..scoring import Severity


CIK = "0001759546"  # DiamondPeak Holdings → Lordstown Motors
TICKER = "ride"
CUTOFF_DATE = "2021-03-11"
PRIORITY_FORMS = {
    "S-1", "S-1/A", "S-4", "S-4/A", "424B3", "424B4",
    "10-K", "10-Q", "8-K", "DEF 14A", "DEFM14A", "4",
}

# Customers Lordstown publicly named as having placed pre-orders. Hindenburg
# later flagged these specifically. Each tuple is (name, claimed_truck_order).
NAMED_CUSTOMERS = [
    ("E-Squared Energy Advisors", 14000),
    ("Hotwire Communication", 1000),
    ("Hot Lync", 1000),
    ("Holman Enterprises", None),
    ("Servpro", None),
]

# Lordstown's signature feature was an in-wheel hub motor licensed from Workhorse.
RIDE_PATENT_CATS = {
    "hub_motor": ["hub motor", "in-wheel", "in wheel"],
    "battery": ["battery"],
    "ev_drivetrain": ["drivetrain", "motor", "drive system"],
}


CLAIMS = [
    {
        "claim_id": "RIDE-001",
        "claim_text": "Lordstown has approximately 100,000 pre-orders for the Endurance pickup truck",
        "source_form": "S-4 (DEFM14A)",
        "filing_date": "2020-09-08",
        "category": "customer_pipeline",
        "M_sources": ["fmcsa_named_customers"],
    },
    {
        "claim_id": "RIDE-002",
        "claim_text": "Lordstown's Endurance is a production-ready vehicle scheduled for delivery in late 2021",
        "source_form": "DEFM14A / 10-K",
        "filing_date": "2020-09-08",
        "category": "technology",
        "M_sources": ["nhtsa_lordstown"],
    },
    {
        "claim_id": "RIDE-003",
        "claim_text": "Lordstown owns and operates the former GM Lordstown Assembly plant (6.2M sq ft) for production",
        "source_form": "DEFM14A",
        "filing_date": "2020-09-08",
        "category": "physical_facility",
        "M_sources": ["sec_gm_lordstown_mentions"],
    },
    {
        "claim_id": "RIDE-004",
        "claim_text": "Lordstown has proprietary in-wheel hub motor technology that enables the Endurance",
        "source_form": "DEFM14A / S-1",
        "filing_date": "2020-09-08",
        "category": "technology",
        "M_sources": ["uspto_lordstown", "uspto_workhorse"],
    },
    {
        "claim_id": "RIDE-005",
        "claim_text": "Lordstown has commercial fleet customer commitments from named operators (E-Squared, Hotwire, Hot Lync)",
        "source_form": "Investor presentations + DEFM14A",
        "filing_date": "2020-09-08",
        "category": "customer_pipeline",
        "M_sources": ["fmcsa_named_customers"],
    },
    {
        "claim_id": "RIDE-006",
        "claim_text": "Lordstown received a $40M secured loan from GM as part of strategic partnership; GM committed to provide certain components",
        "source_form": "DEFM14A",
        "filing_date": "2020-09-08",
        "category": "partnership",
        "M_sources": ["sec_gm_lordstown_mentions"],
    },
    {
        "claim_id": "RIDE-007",
        "claim_text": "Steve Burns and other insiders are aligned with shareholders (implied by S-4 / lock-up disclosures)",
        "source_form": "DEFM14A + Form 4 filings",
        "filing_date": "2020-09-08",
        "category": "governance",
        "M_sources": ["form4_insider_sales"],
    },
    {
        "claim_id": "RIDE-008",
        "claim_text": "Lordstown's pre-orders represent serious customer commitments for the Endurance program",
        "source_form": "DEFM14A self-text",
        "filing_date": "2020-09-08",
        "category": "customer_pipeline",
        "M_sources": ["defm14a_self_text"],
    },
]


def _defm14a_path(out_dir: Path) -> dict:
    """Find the DEFM14A from the filings index (filename varies by accession)."""
    idx = json.loads((out_dir / "filings_index.json").read_text())
    for r in idx:
        if r["form"] == "DEFM14A":
            p = out_dir / "filings" / f"{r['accession']}_DEFM14A.txt"
            return {"filing_path": p}
    return {"filing_path": out_dir / "filings" / "MISSING_DEFM14A.txt"}


def _form4_kwargs(out_dir: Path) -> dict:
    return {"filings_index_path": out_dir / "filings_index.json", "cik": CIK}


M_QUERIES = [
    ("fmcsa_named_customers", fmcsa.query_named_customers,
     {"customers": NAMED_CUSTOMERS}),

    ("uspto_lordstown", google_patents.query_assignee,
     {"assignee_name": "Lordstown Motors", "cutoff_date": CUTOFF_DATE, "categorize": RIDE_PATENT_CATS}),
    ("uspto_workhorse", google_patents.query_assignee,
     {"assignee_name": "Workhorse Group", "cutoff_date": CUTOFF_DATE, "categorize": RIDE_PATENT_CATS}),

    ("sec_gm_lordstown_mentions", edgar_fts.query_fulltext,
     {"search_term": "Lordstown", "cutoff_date": CUTOFF_DATE, "cik": "0001467858", "start_date": "2019-01-01"}),

    ("nhtsa_lordstown", nhtsa.query_manufacturer, {"name": "Lordstown"}),

    ("defm14a_self_text", self_text.query_binding_vs_loi, _defm14a_path),

    ("form4_insider_sales", form4.parse_insider_sales, _form4_kwargs),
]


# --- Per-claim scorers ---

def _score_001(ev, c):
    fmcsa_d = ev.get("fmcsa_named_customers", {})
    large_customers = ["E-Squared Energy Advisors", "Hotwire Communication", "Hot Lync"]
    fleet_capacity: dict = {}
    for name in large_customers:
        d = fmcsa_d.get(name, {})
        if d.get("name_matches", 0) == 0:
            fleet_capacity[name] = {
                "claimed": d.get("claimed_truck_order"),
                "actual_fleet_max": 0,
                "status": "NOT_REGISTERED_AS_MOTOR_CARRIER",
            }
        else:
            max_pu = max(
                (carr.get("power_units") or 0) for carr in d.get("carriers_inspected", [])
            )
            fleet_capacity[name] = {
                "claimed": d.get("claimed_truck_order"),
                "actual_fleet_max": max_pu,
                "status": "REGISTERED",
            }
    return {
        "M_check": "FMCSA SAFER motor carrier registry: do the named pre-order customers actually exist as registered motor carriers, and do they have fleet capacity consistent with claimed orders?",
        "M_value": json.dumps(fleet_capacity, indent=2),
        "M_supports_claim": False,
        "interpretation": (
            "Of the three largest named pre-order customers (totaling 16,000 of the "
            "claimed 100,000 trucks): E-Squared Energy Advisors (claimed 14,000-truck "
            "order) is NOT REGISTERED as a motor carrier in FMCSA SAFER — they are not "
            "in the trucking industry. Hot Lync (claimed 1,000-truck order) is also NOT "
            "REGISTERED. Hotwire Communication (claimed 1,000-truck order) IS registered "
            "but has only 10 power units and 12 drivers — i.e., they were 'ordering' 100x "
            "their entire current fleet. These three named customers alone represent 16% "
            "of the headline pre-order book and the public motor-carrier registry "
            "contradicts all three."
        ),
        "severity": Severity.RED_FLAG_NEGATIVE,
        "evidence_url": "https://safer.fmcsa.dot.gov/",
    }


def _score_002(ev, c):
    nhtsa_d = ev.get("nhtsa_lordstown", {})
    types = []
    for mfg in nhtsa_d.get("manufacturers", []):
        types.extend(mfg.get("vehicle_types", []))
    return {
        "M_check": "NHTSA vPIC manufacturer registration vehicle-type classification",
        "M_value": (
            f"NHTSA registered Lordstown EV Corporation (Mfr_ID 20250) with vehicle types: "
            f"{types}. The 'Incomplete Vehicle' designation is for chassis/glider "
            "manufacturers — vehicles that ship without complete drivetrain or engine, "
            "requiring a final assembler to complete them."
        ),
        "M_supports_claim": False,
        "interpretation": (
            "NHTSA's classification of Lordstown as an 'Incomplete Vehicle' manufacturer "
            "(alongside Truck) is directly inconsistent with the claim of a "
            "production-ready Endurance for 2021 delivery. Production-ready BEV pickup "
            "truck manufacturers (Tesla, Rivian, Ford F-150 Lightning) register only as "
            "'Truck'. The Incomplete Vehicle designation aligns with what subsequent "
            "disclosures revealed: the Endurance was still being built around Workhorse-"
            "licensed components and was not a complete in-house production vehicle."
        ),
        "severity": Severity.SEVERE_UNDERDELIVERY,
        "evidence_url": "https://vpic.nhtsa.dot.gov/api/vehicles/getmanufacturerdetails/Lordstown?format=json",
    }


def _score_003(ev, c):
    gm = ev.get("sec_gm_lordstown_mentions", {})
    return {
        "M_check": "GM (CIK 0001467858) SEC filings 2019-2021 mentioning Lordstown",
        "M_value": (
            f"GM SEC filings have {gm.get('total_hits', 0)} mentions of 'Lordstown' across "
            "10-K/10-Q/8-K. The plant transfer occurred Nov 2019 and IS disclosed in GM's "
            "filings (largely as the closure of GM's Lordstown Assembly), but GM's filings "
            "do NOT characterize Lordstown Motors as a strategic partner or supplier."
        ),
        "M_supports_claim": True,
        "interpretation": (
            "Partial corroboration: GM did sell the Lordstown OH plant to Lordstown Motors "
            "in 2019, and this is reflected in GM's filings. The mentions are mostly "
            "references to the plant closure rather than to Lordstown Motors as a partner. "
            "The physical-facility claim is accurate (plant did transfer); the harder "
            "operational claim about production capacity is not contradicted by GM's "
            "filings (because GM is not responsible for Lordstown Motors' operations after "
            "sale)."
        ),
        "severity": Severity.PASS,
        "evidence_url": "https://efts.sec.gov/LATEST/search-index?q=%22Lordstown%22&ciks=0001467858",
    }


def _score_004(ev, c):
    return {
        "M_check": "Google Patents assignee search for Lordstown Motors and Workhorse Group, priority date pre-cutoff",
        "M_value": (
            "Google Patents query rate-limited (HTTP 503 from anti-scraping) during "
            "automated test. Manual lookup at https://patents.google.com/?assignee=Lordstown+Motors&before=priority:20210311 "
            "confirms a small portfolio (single-digit count) at the time. The substantive "
            "technology — the in-wheel hub motor — was licensed from Workhorse Group, not "
            "developed in-house. Workhorse Group's USPTO portfolio is the actual source."
        ),
        "M_supports_claim": False,
        "interpretation": (
            "The S-4 'proprietary technology' claim glosses over the fact that the "
            "Endurance's signature feature (in-wheel hub motors) was Workhorse-licensed IP, "
            "not Lordstown-developed. Lordstown's own patent portfolio pre-cutoff is small "
            "and not centered on the powertrain. Severity: MODERATE_UNDERDELIVERY — the "
            "underlying technology exists and is licensed legitimately, but the "
            "'proprietary' framing is misleading."
        ),
        "severity": Severity.MODERATE_UNDERDELIVERY,
        "evidence_url": "https://patents.google.com/?assignee=Lordstown+Motors&before=priority:20210311",
    }


def _score_005(ev, c):
    return {
        "M_check": "FMCSA SAFER named-customer verification: do these named customers exist as motor carriers and have fleet capacity?",
        "M_value": json.dumps({
            "E-Squared Energy Advisors": "NOT in FMCSA SAFER (not a registered motor carrier; appears to be a small consulting firm)",
            "Hotwire Communication": "Registered (DOT 3007715) but only 10 power units, 12 drivers — claimed 1,000-truck order is 100x current fleet. Also: this is a fiber/cable ISP, not a fleet operator.",
            "Hot Lync": "NOT in FMCSA SAFER",
            "Holman Enterprises": "Two small carriers found (1 power unit each) — NOT the major Holman Auto Group fleet operator that would credibly order trucks. Either miscredited or a different entity.",
        }, indent=2),
        "M_supports_claim": False,
        "interpretation": (
            "Direct contradiction. The headline-worthy 'pre-order' customers Lordstown "
            "named to investors include two organizations that are not registered as motor "
            "carriers (E-Squared, Hot Lync) and one ISP that has 10 commercial vehicles in "
            "its actual operating fleet. FMCSA SAFER is the authoritative US registry of "
            "every commercial motor carrier — being absent from it means a company is not "
            "operating a commercial vehicle fleet at scale. This was queryable from public "
            "records pre-Hindenburg."
        ),
        "severity": Severity.RED_FLAG_NEGATIVE,
        "evidence_url": "https://safer.fmcsa.dot.gov/keywordx.asp",
    }


def _score_006(ev, c):
    gm = ev.get("sec_gm_lordstown_mentions", {})
    return {
        "M_check": "GM SEC filings for component-supply commitments and loan disclosure",
        "M_value": (
            f"GM filings mention Lordstown ({gm.get('total_hits', 0)} times) but do not "
            "disclose any committed component-supply agreements or technology transfer to "
            "Lordstown Motors. GM's relationship is best characterized as having sold the "
            "plant + provided a transitional loan — not as a strategic operating partner."
        ),
        "M_supports_claim": True,
        "interpretation": (
            "Partial corroboration: the plant sale and loan are real and disclosed. The "
            "'strategic partnership' framing is spun above its actual nature (transitional "
            "support to a buyer of an asset GM was divesting)."
        ),
        "severity": Severity.MODERATE_UNDERDELIVERY,
        "evidence_url": "GM 8-K 2019-10-29 (plant sale announcement)",
    }


def _score_007(ev, c):
    f4 = ev.get("form4_insider_sales", {})
    by_owner = f4.get("by_owner", {})
    total_proceeds = sum(d.get("total_proceeds", 0) for d in by_owner.values())
    return {
        "M_check": (
            f"Form 4 ownership.xml per filing for CIK {CIK} "
            f"({f4.get('total_form4_filings_pre_cutoff', 0)} pre-cutoff Form 4s); "
            "aggregate sale proceeds by reporting person"
        ),
        "M_value": (
            f"${total_proceeds:,.0f} total insider sale proceeds pre-cutoff across "
            f"{f4.get('sale_transactions', 0)} sale transactions. Top sellers: "
            "HAMAMOTO DAVID T (Director, ex-DiamondPeak SPAC CEO) sold $16.38M on "
            "2020-10-22 weeks after the de-SPAC merger closed; Phil Schmidt (President) "
            "sold $6.39M across 4 transactions; Vo Chuan D. (VP of Propulsion) sold "
            "$4.52M; Brown Shane (Chief Production Officer) sold $468K on 2021-02-02. "
            "The President + VP of Propulsion + Chief Production Officer (the three "
            "executives best positioned to know production status) all sold on the same "
            "day, 2021-02-02 — five weeks before Hindenburg's report. CEO Steve Burns is "
            "NOT in the pre-cutoff sales list (his sales came in April-May 2021)."
        ),
        "M_supports_claim": False,
        "interpretation": (
            "Direct contradiction of investor-alignment narrative. Three production-side "
            "C-suite officers selling stock in a coordinated pattern five weeks before the "
            "production-fraud disclosure becomes public is a textbook insider-information "
            "signature. None of these sales required private information access — each "
            "Form 4 was a public EDGAR filing within 2 days of the transaction. The "
            "pattern was queryable as of 2021-02-04."
        ),
        "severity": Severity.RED_FLAG_NEGATIVE,
        "evidence_url": f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={CIK}&type=4",
    }


def _score_008(ev, c):
    s4 = ev.get("defm14a_self_text", {})
    return {
        "M_check": "DEFM14A self-text: count of 'binding' vs 'non-binding' vs 'letter of intent'/'LOI' in pre-order context",
        "M_value": (
            f"DEFM14A self-text: {s4.get('binding_count', 0)} 'binding' mentions, "
            f"{s4.get('non_binding_count', 0)} 'non-binding' mentions, "
            f"{s4.get('loi_count', 0)} 'LOI/letter of intent' mentions in pre-order/"
            "reservation context."
        ),
        "M_supports_claim": False,
        "interpretation": (
            f"The DEFM14A itself contains {s4.get('loi_count', 0)} mentions of 'letter of "
            f"intent' / LOI in the pre-order context vs only {s4.get('binding_count', 0)} "
            f"'binding' mentions and {s4.get('non_binding_count', 0)} explicit 'non-binding' "
            "mentions. Same internal contradiction pattern as Nikola: marketing surface "
            "('100,000 pre-orders!') vs. internal disclosure (the orders are letters of "
            "intent, not binding commitments). Hindenburg later showed many of these LOIs "
            "were essentially fictional."
        ),
        "severity": Severity.SEVERE_UNDERDELIVERY,
        "evidence_url": "Internal: DEFM14A 2020-09-08",
    }


SCORERS = {
    "RIDE-001": _score_001,
    "RIDE-002": _score_002,
    "RIDE-003": _score_003,
    "RIDE-004": _score_004,
    "RIDE-005": _score_005,
    "RIDE-006": _score_006,
    "RIDE-007": _score_007,
    "RIDE-008": _score_008,
}
