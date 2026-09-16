"""Biotech f-library: marketing-claim masking channels → verification against M.

Each BioRule encodes one way IR/marketing can inflate the perceived probability
of a catalyst, plus how to check it: the claim shape it applies to (R), the
verification method (f), the authoritative source (M), and the adjudication
criteria an evaluator uses to call the claim AFFIRMED / REFUTED / UNVERIFIABLE.

These are not numeric-formula rules like the real-estate f_library — biotech
verification is semantic (did the registered primary endpoint change? is an
open-label number being extrapolated to a controlled readout?). So adjudication
is reasoning over fetched M-evidence, not an arithmetic tolerance. The rules are
the knowledge: the channel catalog IS the product, independent of any one name.

Design priority is PRECISION (honesty-validator standard): a rule should fire
only when the marketing claim is genuinely unsupported or contradicted by an
authoritative source, never merely because the science is hard. UNVERIFIABLE is
a distinct, non-clean verdict — absence of confirmation is not confirmation.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from verticals.buyside_dd.schemas import ReferentType, Severity


@dataclass(frozen=True)
class BioRule:
    rule_id: str
    channel: str                      # the masking mechanism family
    claim_predicate: str              # predicate tag the extractor assigns to matching claims
    referent_type: ReferentType
    r_pattern: str                    # the marketing-claim shape this rule judges
    f_method: str                     # how to verify against M
    m_source: str                     # authoritative source(s)
    m_connector: str                  # module/function that fetches M (or 'manual')
    refutes_if: str                   # condition under which the claim is REFUTED
    affirms_if: str                   # condition under which the claim is AFFIRMED
    severity_if_refuted: Severity
    applies_when: str = "any catalyst"  # gating note (catalyst_type / indication)
    notes: str = ""


# ─────────────────────────────────────────────────────────────────────────────
# The channel catalog
# ─────────────────────────────────────────────────────────────────────────────
BIOTECH_RULES: list[BioRule] = [

    # ── ENDPOINT INTEGRITY ───────────────────────────────────────────────────
    BioRule(
        rule_id="bio.endpoint_integrity",
        channel="endpoint_manipulation",
        claim_predicate="trial_primary_endpoint",
        referent_type=ReferentType.TRIAL,
        r_pattern="Marketing names the endpoint the pivotal trial WILL SUCCEED / be approved on — the success-determining slot, not merely an endpoint it measures.",
        f_method="Identify which registered endpoint occupies the success-determining slot for THIS catalyst (the registered PRIMARY whose timeFrame aligns with the catalyst readout), then test whether the marketed success-basis endpoint is that one. Two axes are independent: efficacy-vs-safety (what it measures) and primary-vs-secondary (its hierarchy slot). A secondary endpoint can be a legitimate efficacy endpoint — describing one is NOT masking. Also inspect version HISTORY for a CONSTRUCT/TYPE change of the registered primary near readout.",
        m_source="ClinicalTrials.gov registration + version history",
        m_connector="public_co.m_sources.multi_venue_disclosure_consistency.ingest_clinicaltrials_gov_history",
        refutes_if="EITHER (a) the registered primary's CONSTRUCT or TYPE was changed mid-trial (clinical->surrogate, scale-family swap, co-primary dropped), especially near readout; OR (b) marketing places a NON-PRIMARY endpoint (secondary/subgroup/biomarker) into the success-determining slot — i.e. presents it as the basis on which the catalyst succeeds or approval rests, displacing the registered primary that actually gates the catalyst. NOT a refute: merely describing a secondary efficacy endpoint, or emphasizing the near-term co-primary of a trial with STAGGERED co-primaries (different timeFrames for different approval pathways) when that near-term co-primary is the one the catalyst reads out.",
        affirms_if="The marketed success-basis endpoint IS a registered primary whose timeFrame aligns with the catalyst, with construct unchanged across versions through cutoff.",
        severity_if_refuted=Severity.SEVERE,
    ),
    BioRule(
        rule_id="bio.endpoint_emphasis_shift",
        channel="endpoint_manipulation",
        claim_predicate="efficacy_emphasis",
        referent_type=ReferentType.TRIAL,
        r_pattern="Marketing foregrounds a SECONDARY / biomarker / subgroup endpoint as the headline evidence of likely success.",
        f_method="Check whether the emphasized metric is the registered PRIMARY. De-emphasis of the primary in favor of a secondary is a tell the primary is expected to be weak.",
        m_source="ClinicalTrials.gov registration (primary vs secondary outcomes)",
        m_connector="public_co.m_sources.clinical_trials + CT.gov v2 outcomes",
        refutes_if="The promoted evidence is a secondary/post-hoc/biomarker measure while the registered primary is barely mentioned or is a different, harder endpoint.",
        affirms_if="Promotion centers on the registered primary endpoint.",
        severity_if_refuted=Severity.MODERATE,
    ),

    # ── EVIDENCE-QUALITY OVERREACH ───────────────────────────────────────────
    BioRule(
        rule_id="bio.open_label_extrapolation",
        channel="evidence_quality_overreach",
        claim_predicate="efficacy_claim",
        referent_type=ReferentType.DRUG_PROGRAM,
        r_pattern="Efficacy ('improved cognition', 'X% response') asserted from OPEN-LABEL / single-arm / uncontrolled data and used to imply a controlled pivotal will succeed.",
        f_method="Establish whether the cited data were placebo-controlled and blinded. Uncontrolled improvement in progressive/relapsing diseases is routinely erased by placebo effect and regression to the mean.",
        m_source="ClinicalTrials.gov design module (allocation, masking, control arm); the cited trial's registration",
        m_connector="CT.gov v2 designModule",
        refutes_if="The headline efficacy derives from an uncontrolled/open-label cohort and is generalized to the controlled catalyst readout.",
        affirms_if="The cited efficacy is from a randomized, placebo-controlled, blinded comparison.",
        severity_if_refuted=Severity.SEVERE,
        notes="Dominant Alzheimer's/CNS masking channel; open-label 'improvement' has near-zero predictive value for controlled readouts.",
    ),
    BioRule(
        rule_id="bio.biomarker_to_clinical_leap",
        channel="evidence_quality_overreach",
        claim_predicate="surrogate_predicts_outcome",
        referent_type=ReferentType.DRUG_PROGRAM,
        r_pattern="A biomarker / target-engagement / imaging change is framed as predictive of the clinical primary endpoint.",
        f_method="Determine whether the biomarker is an FDA-accepted surrogate for the indication. Most are not; target engagement ≠ clinical benefit.",
        m_source="FDA surrogate-endpoint table; Drugs@FDA precedent in the indication",
        m_connector="public_co.m_sources.openfda + manual FDA guidance",
        refutes_if="The biomarker is not a validated/accepted surrogate for the indication and is used to predict the clinical readout.",
        affirms_if="The biomarker is an FDA-accepted surrogate (e.g. an approved accelerated-approval endpoint for this indication).",
        severity_if_refuted=Severity.MODERATE,
    ),
    BioRule(
        rule_id="bio.naive_cross_trial_benchmark",
        channel="evidence_quality_overreach",
        claim_predicate="comparative_efficacy",
        referent_type=ReferentType.DRUG_PROGRAM,
        r_pattern="Efficacy framed as superior to standard-of-care / competitors via cross-trial comparison rather than a concurrent control.",
        f_method="Check whether the comparison is within-trial (randomized) or a naive cross-study benchmark against historical/published numbers.",
        m_source="CT.gov design (comparator arm) + the referenced external trial",
        m_connector="CT.gov v2 designModule",
        refutes_if="Superiority rests on cross-trial comparison with no head-to-head or concurrent control.",
        affirms_if="Comparison is a concurrent randomized control or a registered head-to-head.",
        severity_if_refuted=Severity.MINOR,
    ),
    BioRule(
        rule_id="bio.mechanism_validation",
        channel="evidence_quality_overreach",
        claim_predicate="mechanism_of_action",
        referent_type=ReferentType.DRUG_PROGRAM,
        r_pattern="A novel mechanism is presented as a credible path to benefit in an indication with a long history of MoA failures.",
        f_method="Assess whether the target/MoA has ANY precedent of clinical translation in the indication; weigh the indication's base-rate of Phase 3 success.",
        m_source="Drugs@FDA approvals by indication; class base-rate priors",
        m_connector="public_co.m_sources.openfda.query_approved_drugs + manual base rates",
        refutes_if="The MoA is unprecedented in the indication AND the only support is preclinical/mechanistic with weak controlled clinical data.",
        affirms_if="The MoA class has prior clinical validation, or strong controlled data already exist.",
        severity_if_refuted=Severity.MINOR,
        notes="A prior, not a refutation by itself; combine with evidence-quality channels.",
    ),

    # ── POWERING / STATISTICS ────────────────────────────────────────────────
    BioRule(
        rule_id="bio.powering_adequacy",
        channel="statistical_framing",
        claim_predicate="trial_powering",
        referent_type=ReferentType.TRIAL,
        r_pattern="'Well-powered' / 'adequately sized' pivotal claim.",
        f_method="Compare registered enrollment to the N implied by the observed/assumed effect size and the indication's typical variance; flag if the assumed effect is implausibly large vs class.",
        m_source="CT.gov enrollment + prior controlled effect sizes in class",
        m_connector="CT.gov v2 enrollmentInfo + manual class effect sizes",
        refutes_if="Powering assumes an effect size far above what controlled data in the class support, so realistic power is low.",
        affirms_if="Enrollment is sufficient for a conservative, class-consistent effect size.",
        severity_if_refuted=Severity.MODERATE,
    ),

    # ── OPERATIONAL CLAIMS ───────────────────────────────────────────────────
    BioRule(
        rule_id="bio.timeline_slippage",
        channel="operational_masking",
        claim_predicate="catalyst_timeline",
        referent_type=ReferentType.TRIAL,
        r_pattern="'On track for [period] topline / readout' guidance.",
        f_method="Compare guided readout timing to the CT.gov primary-completion date and its DRIFT across registration versions.",
        m_source="ClinicalTrials.gov primaryCompletionDate history",
        m_connector="multi_venue_disclosure_consistency.ingest_clinicaltrials_gov_history",
        refutes_if="Registered primary-completion date has repeatedly slipped while guidance stays 'on track', or guidance is inconsistent with the registered date.",
        affirms_if="Guidance matches a stable registered completion date.",
        severity_if_refuted=Severity.MINOR,
    ),
    BioRule(
        rule_id="bio.enrollment_consistency",
        channel="operational_masking",
        claim_predicate="enrollment_status",
        referent_type=ReferentType.TRIAL,
        r_pattern="'Fully enrolled' / 'enrollment on plan' claims.",
        f_method="Compare claimed enrollment/status to CT.gov registered enrollment count and overall status as-of cutoff.",
        m_source="ClinicalTrials.gov status + enrollment",
        m_connector="CT.gov v2 statusModule + enrollmentInfo",
        refutes_if="Claimed status materially overstates the registered status/enrollment.",
        affirms_if="Claim matches registered status and enrollment.",
        severity_if_refuted=Severity.MINOR,
    ),

    # ── REGULATORY PATH ──────────────────────────────────────────────────────
    BioRule(
        rule_id="bio.regulatory_path_precedent",
        channel="regulatory_spin",
        claim_predicate="regulatory_path",
        referent_type=ReferentType.DRUG_PROGRAM,
        r_pattern="'Clear path to approval' / 'aligned with FDA' / accelerated-approval availability.",
        f_method="Verify against FDA precedent: is there an approved drug / accepted endpoint in the indication? Any prior CRLs in class? Is the claimed accelerated-approval surrogate actually accepted?",
        m_source="Drugs@FDA; FDA accelerated-approval endpoint precedent",
        m_connector="public_co.m_sources.openfda.query_approved_drugs",
        refutes_if="The asserted regulatory path lacks precedent (no accepted endpoint/surrogate, or prior class CRLs) and is presented as settled.",
        affirms_if="An accepted endpoint/surrogate or prior approval in the indication supports the claimed path.",
        severity_if_refuted=Severity.MODERATE,
    ),

    # ── CROSS-VENUE CONSISTENCY ──────────────────────────────────────────────
    BioRule(
        rule_id="bio.venue_consistency",
        channel="selective_disclosure",
        claim_predicate="efficacy_number",
        referent_type=ReferentType.DRUG_PROGRAM,
        r_pattern="A specific efficacy/safety number stated in a press release or deck.",
        f_method="Cross-check the number against the same fact in CT.gov results, conference abstracts, and SEC filings; flag divergence across venues.",
        m_source="multi-venue: CT.gov results, ASCO/AACR/conference abstracts, SEC filings",
        m_connector="public_co.m_sources.multi_venue_disclosure_consistency.audit_disclosure_chain",
        refutes_if="The same fact is stated with materially different values across venues, or the PR number is absent from the registered/peer-reviewed record.",
        affirms_if="The number is consistent across venues / matches the registered results.",
        severity_if_refuted=Severity.MODERATE,
    ),

    # ── SCIENCE-CORPUS OVERREACH (marketing runs ahead of the data) ──────────
    BioRule(
        rule_id="bio.marketing_exceeds_source",
        channel="evidence_quality_overreach",
        claim_predicate="efficacy_number",
        referent_type=ReferentType.DRUG_PROGRAM,
        r_pattern="A specific TREATMENT-EFFECT magnitude in marketing: % change / point change in an efficacy endpoint or biomarker, response/remission rate, effect size, hazard ratio, or p-value.",
        f_method="SCOPE: this rule adjudicates EFFICACY-EFFECT magnitudes ONLY. If the number is operational — enrollment / sample size / patient count, dose (mg), trial duration, number of sites/arms, or a date — return UNVERIFIABLE for this rule (those are handled by enrollment/timeline/venue rules, and a small operational discrepancy is NOT efficacy overreach). For an efficacy-effect number: locate the actual scientific source it derives from (paper/preprint/poster in the science corpus, dated <= cutoff) and test whether the source SUPPORTS it. Distinguish: was the result CONTROLLED (vs the marketed implication of efficacy)? Was it the PRESPECIFIED primary, or a post-hoc/subgroup analysis marketed as the headline? Does the marketed magnitude match the reported effect or overstate it?",
        m_source="Science corpus: Europe PMC peer-reviewed + preprint reports (as-of cutoff)",
        m_connector="public_biotech.science_corpus.load_science_corpus",
        refutes_if="The marketed EFFICACY-EFFECT magnitude materially exceeds what the underlying scientific source supports: an uncontrolled/open-label effect marketed as evidence of efficacy, a post-hoc/subgroup effect presented as the primary finding, or a magnitude larger than the source reports (e.g. marketing '38% tau reduction' when the source paper reports 20%). Operational-count discrepancies do NOT qualify.",
        affirms_if="The marketed efficacy-effect magnitude matches a controlled, prespecified result actually reported in a dated scientific source.",
        severity_if_refuted=Severity.SEVERE,
        notes="The science corpus is the M that lets the evidence-quality channel CONFIRM rather than abstain. SCOPED to efficacy-effect magnitudes — enrollment/dose/operational numbers route here under efficacy_number but must be returned UNVERIFIABLE so they do not inflate the decisive gate.",
    ),

    # ── DISCLOSURE INTEGRITY (honesty overlay) ───────────────────────────────
    BioRule(
        rule_id="bio.prior_disclosure_integrity",
        channel="disclosure_integrity",
        claim_predicate="data_credibility",
        referent_type=ReferentType.DRUG_PROGRAM,
        r_pattern="Continued reliance in marketing on prior pivotal/preclinical data for THIS program.",
        f_method="Check for authoritative findings that the program's prior data disclosures were misleading: SEC/DOJ actions, journal retractions or expressions of concern, institutional misconduct findings.",
        m_source="SEC litigation releases / 8-K disclosures; journal retraction notices; PubMed",
        m_connector="EDGAR corpus (8-K) + manual journal/PubMed",
        refutes_if="An authority (SEC, journal, institution) has found the program's prior data disclosures misleading, retracted, or under unresolved integrity concern.",
        affirms_if="No authoritative integrity finding against the program's data through cutoff.",
        severity_if_refuted=Severity.SEVERE,
        notes="Cassava overlay: SEC negligence-based disclosure settlement re: 2020 Phase 2b simufilam results; journal expressions of concern on key papers.",
    ),
    BioRule(
        rule_id="bio.data_independence",
        channel="disclosure_integrity",
        claim_predicate="data_provenance",
        referent_type=ReferentType.DRUG_PROGRAM,
        r_pattern="Pivotal efficacy/biomarker data presented without noting they were generated or analyzed by conflicted/insider parties.",
        f_method="Determine whether pivotal data were produced/analyzed by independent parties vs insiders later found conflicted or subject to misconduct findings.",
        m_source="Institutional misconduct findings; SEC filings; journal notices",
        m_connector="manual + EDGAR corpus",
        refutes_if="Pivotal data were generated/analyzed by parties under unresolved misconduct/conflict findings.",
        affirms_if="Pivotal data have independent generation/adjudication.",
        severity_if_refuted=Severity.MODERATE,
    ),

    # ── SAFETY FRAMING ───────────────────────────────────────────────────────
    BioRule(
        rule_id="bio.safety_signal_framing",
        channel="safety_masking",
        claim_predicate="safety_claim",
        referent_type=ReferentType.DRUG_PROGRAM,
        r_pattern="'Well-tolerated' / 'clean safety' framing.",
        f_method="Compare safety framing to registered adverse-event/serious-AE data and any FDA holds; flag downplayed SAEs or discontinuations.",
        m_source="CT.gov results adverse-events module; OpenFDA enforcement; FDA holds",
        m_connector="CT.gov v2 results + public_co.m_sources.openfda.query_inspection_history",
        refutes_if="Registered SAE/discontinuation data or an FDA hold contradicts the 'well-tolerated' framing.",
        affirms_if="Safety framing is consistent with the registered safety record.",
        severity_if_refuted=Severity.MINOR,
    ),
]


# Index helpers ──────────────────────────────────────────────────────────────
def rules_by_predicate() -> dict[str, list[BioRule]]:
    out: dict[str, list[BioRule]] = {}
    for r in BIOTECH_RULES:
        out.setdefault(r.claim_predicate, []).append(r)
    return out


def get_rule(rule_id: str) -> BioRule:
    for r in BIOTECH_RULES:
        if r.rule_id == rule_id:
            return r
    raise KeyError(rule_id)


CLAIM_PREDICATES = sorted({r.claim_predicate for r in BIOTECH_RULES})
CHANNELS = sorted({r.channel for r in BIOTECH_RULES})
