"""
J-Book Exposure cohort definition.

Forward test of the Signal OS framework targeted specifically at the
YSS/IONQ short-thesis pattern: companies that CLAIM material revenue
from named Pentagon program elements / J-Book line items, where the
forward-looking J-Book itself shows those programs going unfunded.

Pattern (per Wolfpack Research YSS / Wolfpack IONQ reports):
  R: 10-K names a specific DoD program as a key revenue / growth driver
  f: Pentagon J-Book should show that PE funded at or above stated levels
  M: J-Book shows the PE UNFUNDED_THIS_YEAR, UNFUNDED_TWO_PLUS_YEARS,
     FUNDED_SHRINKING, or TERMINATED
  Gap: the company's forward narrative depends on a program Pentagon has
       de-funded — material adverse signal for next-12-month performance

Universe construction (~13 names):
  - Quantum primes whose customer is AFRL / Army / Navy quantum programs:
    IONQ, RGTI, QBTS, QUBT, ARQQ
  - Small-cap space exposed to SDA / Space Force PE lines:
    RKLB, ASTS, RDW, PL
  - AI / autonomy primes with DARPA / DIU / AFRL contracts:
    BBAI
  - Drone primes whose narrative depends on named Program-of-Record wins:
    RCAT (SRR PoR), AIRO (Coastal Defense / Agile Defense)
  - Established mid-cap as comparison anchor:
    KTOS (XQ-58 Valkyrie, Skyborg / CCA, BQM target drones)

Tickers are NOT pre-labeled bullish/bearish; the subagent scores blindly.

Uniform cutoff: 2026-05-20.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CohortMember:
    """Cohort member with CIK derived from ticker via SEC's authoritative map.

    Do NOT pass cik= directly. Use cik_override= only for tickers SEC's
    company_tickers.json doesn't list (rare: certain foreign filers, recently
    delisted, or special ADRs). Default code path resolves CIK on demand from
    `edgar.cik_for(ticker)` — single source of truth, no hand-typed CIKs.
    """
    ticker: str
    name:   str
    notes:  str
    cik_override: str | None = None  # rarely used; default is SEC lookup

    @property
    def cik(self) -> str:
        from .edgar import cik_for
        return cik_for(self.ticker, override=self.cik_override)


COHORT: list[CohortMember] = [
    # ─── Quantum ──────────────────────────────────────────────────────
    CohortMember(
        ticker="IONQ", name="IonQ, Inc.",
        notes="Trapped-ion quantum computing. AFRL Rome (FA8750) "
              "contracting history including named AFRL Quantum "
              "Networking program. Recent acquisitions: Capella Space, "
              "Oxford Ionics, ID Quantique, Qubitekk, Lightsynq, "
              "Vector Atomic."),
    CohortMember(
        ticker="RGTI", name="Rigetti Computing, Inc.",
        notes="Superconducting-qubit quantum computing. AFRL / DARPA "
              "research contracts. Pre-revenue at scale."),
    CohortMember(
        ticker="QBTS", name="D-Wave Quantum Inc.",
        notes="Quantum annealing. Pivoting toward gate-model. "
              "Government revenue via D-Wave Government Inc."),
    CohortMember(
        ticker="QUBT", name="Quantum Computing Inc.",
        notes="Photonic quantum systems. Multiple subsidiaries (QPhoton, "
              "Qubittech, QI Solutions). Mixed government/commercial."),
    CohortMember(
        ticker="ARQQ", name="Arqit Quantum Inc.",
        notes="UK-domiciled quantum-encryption. Symmetric-key narrative "
              "with claimed NATO / defense customer exposure."),

    # ─── Small-cap space ──────────────────────────────────────────────
    CohortMember(
        ticker="RKLB", name="Rocket Lab USA, Inc.",
        notes="Small-launch + space systems. SolAero / LightRidge / "
              "Planetary Systems acquisitions. STP-S30 launch contract. "
              "SDA Tracking Layer T3 prime exposure."),
    CohortMember(
        ticker="ASTS", name="AST SpaceMobile, Inc.",
        notes="Space-based cellular. AST Defense subsidiary for DoD "
              "applications. Pre-revenue at scale."),
    CohortMember(
        ticker="RDW", name="Redwire Corporation",
        notes="Space infrastructure rollup (Hera Systems, Made In Space, "
              "Adcole, Roccor). Heavy SDA + AFRL contracting narrative."),
    CohortMember(
        ticker="PL", name="Planet Labs PBC",
        notes="Commercial EO satellites. Planet Labs Federal, Inc. for "
              "NRO / NGA / DoD. Recent BlackSky-adjacent positioning."),

    # ─── AI / autonomy ────────────────────────────────────────────────
    CohortMember(
        ticker="BBAI", name="BigBear.ai Holdings, Inc.",
        notes="AI/ML for defense. BigBear.ai Federal LLC. "
              "Acquisitions of Pangiam, ProModel, Ask Sage. "
              "Project Maven / DARPA narrative."),

    # ─── Drones / autonomy ────────────────────────────────────────────
    CohortMember(
        ticker="RCAT", name="Red Cat Holdings, Inc.",
        notes="Teal Drones subsidiary. Army Short Range Reconnaissance "
              "(SRR) Program of Record winner Nov 2024. FY2025 revenue "
              "growth attributed primarily to SRR deliveries."),
    CohortMember(
        ticker="AIRO", name="AIRO Group Holdings, Inc.",
        notes="Recent SPAC; rollup of Coastal Defense, Sky Defense, "
              "Agile Defense, Aspen Avionics. UAS / training claims."),

    # ─── Established mid-cap anchor ───────────────────────────────────
    CohortMember(
        ticker="KTOS",
        name="Kratos Defense & Security Solutions, Inc.",
        notes="Tactical drones (XQ-58 Valkyrie, BQM-167/177), Skyborg / "
              "Collaborative Combat Aircraft (CCA). Long-established "
              "DoD prime. Comparison anchor for cohort."),

    # ─── Phase 2 expansion: defense mid-caps ──────────────────────────
    CohortMember(
        ticker="CACI", name="CACI International Inc",
        notes="Defense IT services / intel mission support; long-time prime."),
    CohortMember(
        ticker="SAIC", name="Science Applications International Corp",
        notes="Defense IT, modernization, IC services. Prime + integrator."),
    CohortMember(
        ticker="LDOS", name="Leidos Holdings, Inc.",
        notes="Defense + intel + health IT services; large prime."),
    CohortMember(
        ticker="MRCY", name="Mercury Systems, Inc.",
        notes="Embedded military electronics, mission processing, RF/EW; "
              "Tier-2 supplier to primes on radar / EW / sensor programs."),
    CohortMember(
        ticker="CW", name="Curtiss-Wright Corporation",
        notes="Defense + nuclear + industrial; reactor controls (naval), "
              "actuation, embedded computing."),
    CohortMember(
        ticker="HEI", name="HEICO Corporation",
        notes="Aerospace aftermarket parts + electronic technologies; "
              "mostly commercial aviation but ETG segment is defense."),
    CohortMember(
        ticker="TDG", name="TransDigm Group Incorporated",
        notes="Highly-engineered aerospace components, commercial + defense "
              "aftermarket. Sole-source on many platforms."),
    CohortMember(
        ticker="VSAT", name="Viasat, Inc.",
        notes="Satellite communications; commercial broadband + government "
              "SATCOM (defense + L3-Inmarsat integration)."),
    CohortMember(
        ticker="AVAV", name="AeroVironment, Inc.",
        notes="Small-UAS prime (Switchblade, Puma, Raven), tactical missile "
              "systems. SOCOM + Army primary customer."),
    CohortMember(
        ticker="BWXT", name="BWX Technologies, Inc.",
        notes="Naval nuclear reactor manufacturing (sole-source to USN), "
              "nuclear fuel, medical isotopes."),

    # ─── Phase 3 expansion: big primes (Tier 1) ───────────────────────
    CohortMember(
        ticker="LMT", name="Lockheed Martin Corporation",
        notes="Largest US defense prime. F-35 prime, F-22A sustainment, "
              "AEGIS BMD, Next-Gen OPIR-GEO, LRDR, NGI competition."),
    CohortMember(
        ticker="NOC", name="Northrop Grumman Corporation",
        notes="B-21 Raider prime, Sentinel/GBSD ICBM prime, OPIR-Polar, "
              "MUX TACAIR / CCA, satellite payloads."),
    CohortMember(
        ticker="RTX", name="RTX Corporation",
        notes="Long Range Standoff Weapon (LRSO), AIM-260, missile portfolio "
              "(Raytheon Missiles & Defense). Includes Pratt & Whitney engines."),
    CohortMember(
        ticker="BA", name="The Boeing Company",
        notes="F-47 NGAD prime (won March 2025), B-52 reengine, GMD prime, "
              "KC-46 tanker, MQ-25 Stingray, commercial aviation downside risk."),
    CohortMember(
        ticker="LHX", name="L3Harris Technologies, Inc.",
        notes="Multi-PE electronic warfare, comms, SDA Tracking Layer prime, "
              "Aerojet Rocketdyne acquisition (2023)."),

    # ─── Phase 3 expansion: mid-cap defense (Tier 2) ──────────────────
    CohortMember(
        ticker="HII", name="Huntington Ingalls Industries, Inc.",
        notes="Naval shipbuilding prime — Virginia/Columbia-class submarines, "
              "Ford-class carriers. Tests Navy SCN corpus gap (expected "
              "UNVERIFIABLE)."),
    CohortMember(
        ticker="HXL", name="Hexcel Corporation",
        notes="Aerospace composites — F-35, B-21, commercial aviation. "
              "Tier-2 supplier to multiple PE-funded programs."),
    CohortMember(
        ticker="MOG-A", name="Moog Inc.",
        notes="Motion control across aerospace/defense platforms. Tier-2 "
              "supplier with broad PE-funding exposure."),
    CohortMember(
        ticker="TXT", name="Textron Inc.",
        notes="Bell helicopters (V-280 FLRAA winner), military trainers, "
              "Shadow UAS, Cessna business jets (commercial)."),

    # ─── Phase 4 expansion: remaining ITA constituents ────────────────
    CohortMember(
        ticker="GE", name="GE Aerospace",
        notes="Largest ITA holding (~19%). Commercial + military engines "
              "(F-35, B-21, CCA via Kratos teaming). Spun out from GE in 2024."),
    CohortMember(
        ticker="GD", name="General Dynamics Corporation",
        notes="Combat vehicles (Abrams, Stryker), submarines (Virginia, Columbia "
              "via Electric Boat), IT services (GDIT), business jets (Gulfstream)."),
    CohortMember(
        ticker="HWM", name="Howmet Aerospace Inc.",
        notes="Specialty aerospace components — engine castings, fasteners, "
              "structures. F-35 + commercial aviation exposure."),
    CohortMember(
        ticker="AXON", name="Axon Enterprise, Inc.",
        notes="TASERs, body cameras, Evidence.com cloud. Mostly law enforcement, "
              "some DoD adjacency. ITA inclusion is unusual (consumer/police, not pure defense)."),
    CohortMember(
        ticker="FTAI", name="FTAI Aviation Ltd.",
        notes="Engine leasing + aerospace aftermarket (LM2500 marine, CFM56 modules). "
              "Some military adjacency via leasing structures."),
    CohortMember(
        ticker="WWD", name="Woodward, Inc.",
        notes="Propulsion controls + actuation for aerospace/defense engines."),
    CohortMember(
        ticker="ATI", name="ATI Inc.",
        notes="Specialty materials (titanium, nickel alloys) for aerospace, "
              "naval nuclear, hypersonics."),
    CohortMember(
        ticker="CRS", name="Carpenter Technology Corporation",
        notes="Specialty alloys for aerospace/defense (jet engines, structures). "
              "Mostly commercial A&D exposure; defense Tier-3."),

    # Phase 5 expansion (2026-05-23): major Pentagon contractors previously
    # absent from the cohort. Most file P-40 procurement / services-budget
    # claims rather than RDT&E PEs, so may score with high UNVERIFIABLE rates
    # under the current J-Book corpus — that gap is itself the finding.
    CohortMember(
        ticker="PLTR", name="Palantir Technologies Inc.",
        notes="Defense AI/ML platforms: Project Maven (Army intel/AI), TITAN "
              "(Army Tactical Intel Targeting Access Node), Gotham (intel), "
              "MetaConstellation; also Foundry (commercial)."),
    CohortMember(
        ticker="BAH", name="Booz Allen Hamilton Holding Corporation",
        notes="Defense IT/intel consulting: JADC2 architecture support, Cyber "
              "Mission Force, Joint AI Center (JAIC), naval intelligence."),
    CohortMember(
        ticker="J", name="Jacobs Solutions Inc.",
        notes="Defense engineering services: hypersonic test infrastructure, "
              "NNSA Nuclear Security Enterprise sustainment, AF Test Range "
              "modernization. Diversified — also infrastructure/commercial."),
    CohortMember(
        ticker="KBR", name="KBR, Inc.",
        notes="Defense services: hypersonics test (LRHW/CHGM), Sentinel ICBM "
              "ground systems support, space launch infrastructure (Vandenberg), "
              "DoE Critical Mission Solutions division."),
    CohortMember(
        ticker="PSN", name="Parsons Corporation",
        notes="Defense IT + critical infrastructure: DOMino cyber, missile "
              "defense IT, intelligence community contracts, critical "
              "infrastructure protection."),
    CohortMember(
        ticker="VVX", name="V2X, Inc.",
        notes="Defense O&M services: LOGCAP V (Army global logistics), training "
              "ranges, Joint Polar Satellite System support, intelligence "
              "facility operations. Small-cap defense services pure-play."),
    CohortMember(
        ticker="HON", name="Honeywell International Inc.",
        notes="Diversified aerospace/defense: F-35 cockpit avionics + display "
              "electronics, T-7 cockpit, Sentinel ICBM ground subsystems, NNSA "
              "nuclear modernization, T55/F124/ATK-3000 engines."),
    CohortMember(
        ticker="ESLT", name="Elbit Systems Ltd.",
        notes="Israeli mid-cap defense; mentioned in J-Book corpus for "
              "short-range air defense / counter-UAS. NASDAQ-listed. Foreign-issuer "
              "caveat applies — usaspending may not show direct DoD obligations "
              "(typically through US subsidiary Elbit Systems of America)."),

    # Phase 6 expansion (2026-05-23): fresh small/mid-cap defense candidates
    # not previously in cohort. Goal is current-vintage small-cap LONG candidates
    # that haven't already had their rerating (unlike MRCY/RGTI which doubled
    # in trailing 1Y).
    CohortMember(
        ticker="DRS", name="Leonardo DRS, Inc.",
        notes="Defense electronics mid-cap (~$8B): naval combat systems, "
              "electro-optical/infrared sensors, force protection, network "
              "computing, electronic warfare. Programs: ECPC (Engineering "
              "Change Proposal Computer), Mounted Family of Computer Systems "
              "(MFoCS), Trophy active protection system, naval power systems. "
              "Foreign-owned (Leonardo S.p.A. Italy) ADR-equivalent."),
    CohortMember(
        ticker="DCO", name="Ducommun Incorporated",
        notes="Aerospace structures small-cap (~$1B): structural components + "
              "electronic systems for F-35, F-18, Apache, Black Hawk, "
              "commercial aviation. Sub-tier; revenue tied to OEM platforms."),
    CohortMember(
        ticker="VSEC", name="VSE Corporation",
        notes="Defense aviation MRO + supply chain mid/small-cap (~$2B): USAF, "
              "USN, Coast Guard, Army aviation logistics, parts distribution, "
              "fleet sustainment. Recently restructured to focus on aviation "
              "segment. Many contracts in DoD O&M budget."),
    CohortMember(
        ticker="CDRE", name="Cadre Holdings, Inc.",
        notes="Body armor + safety equipment small-cap (~$1B): law enforcement, "
              "federal/military, EOD. Brands: Safariland, Med-Eng, ATK. Sells "
              "to DoD, DOJ, federal LEO. Mostly procurement vs RDT&E."),
]


COHORT_CONTEXT = """\
This cohort tests the Signal OS framework against a specific divergence
pattern: companies whose forward-looking 10-K / 10-Q narrative depends on
revenue from named Pentagon Program Elements (PE numbers) or named DoD
programs, where the Pentagon's most recent J-Book shows those programs
going unfunded or shrinking.

PRIMARY M-SOURCE: pentagon_jbook.query_program_funding — given a program
name, PE number, or contractor name, returns the FY-by-FY funding
trajectory + derived status (FUNDED_GROWING / FUNDED_STEADY /
FUNDED_SHRINKING / UNFUNDED_THIS_YEAR / UNFUNDED_TWO_PLUS_YEARS /
TERMINATED / NOT_FOUND). Corpus contains 410 RDT&E + Procurement PEs
from FY 2026 books: DARPA, MDA, SOCOM, OSD, Air Force RDT&E Vol I-IV,
Space Force RDT&E, AF Aircraft / Other Procurement.

SECONDARY M-SOURCES that pair with pentagon_jbook:
- usaspending.query_dod_contracts — confirms the company received the
  contracts they claim (orthogonal verification)
- earmark_detector.query_earmark_status — if a PE is unfunded, was it
  a congressional add ("earmark") whose sponsor lost power?
- acq_coherence.score_acquisition_coherence — if PE losses force the
  parent to pivot via incoherent acquisitions
- insider_vs_calendar.query_insider_sales_near_budget_events —
  insider sales clustered around budget-vote dates while claimed
  PEs were already being zeroed

SUBAGENT FRAMING: extract claims that name SPECIFIC DoD programs (PE
numbers, program names like "AFRL Quantum Networking", "Short Range
Reconnaissance Program of Record", "SDA Tracking Layer", "Skyborg",
"Collaborative Combat Aircraft", "Space Test Program"). Pick
pentagon_jbook as the primary verifier for these claims. If the J-Book
returns UNFUNDED_* / TERMINATED / FUNDED_SHRINKING, mark
SEVERE_UNDERDELIVERY or RED_FLAG_NEGATIVE depending on materiality."""


COMMON_COUNTERPARTY_CIKS: dict[str, str] = {
    # Big defense primes that often disclose subcontractor names
    "Lockheed Martin":     "0000936468",
    "Northrop Grumman":    "0001133421",
    "Raytheon Technologies": "0000101829",
    "L3Harris":            "0000202058",
    "General Dynamics":    "0000040533",
    "Boeing":              "0000012927",
    # Quantum-adjacent counterparties
    "Honeywell":           "0000773840",
    # Space primes
    "SpaceX":              None,  # private; no CIK
}

CUTOFF: str = "2026-05-20"
