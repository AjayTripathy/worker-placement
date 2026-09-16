from core.models import SignalRule

RULES: list[SignalRule] = [
    SignalRule(
        rule_id="AUCTION_TO_DONATION_MATCH",
        vertical="art_donation_fraud",
        jurisdiction="*",
        rule_type="gap_modifier",
        detectable=True,
        statutory_ref="IRC §170(e)(1)(A); Treas. Reg. §1.170A-13(c)",
        description=(
            "Same buyer-of-record acquires a work at public auction in year Y "
            "and gifts that same work to a §501(c)(3) museum within 36 months. "
            "Donor's claimed FMV deduction must reconcile to the recent auction "
            "price unless a substantiated change in market value can be shown."
        ),
        implementation=(
            "verticals.art_donation_fraud.rules.auction_to_donation.apply"
        ),
        priority=10,
        source_text=(
            "IRC §170(e)(1)(A) reduces the deduction for ordinary-income "
            "property to basis. §170(e)(1)(B) similarly reduces it for "
            "tangible personal property put to a use unrelated to the donee's "
            "exempt purpose. Treas. Reg. §1.170A-13(c) requires a qualified "
            "appraisal that reflects the price a willing buyer would pay a "
            "willing seller in the regular market for the property. A recent "
            "(within ~3 years) arm's-length auction purchase by the same "
            "taxpayer is the most directly comparable market evidence."
        ),
    ),
    SignalRule(
        rule_id="EARLY_DEACCESSION_RECAPTURE",
        vertical="art_donation_fraud",
        jurisdiction="*",
        rule_type="gap_modifier",
        detectable=True,
        statutory_ref="IRC §170(e)(7)",
        description=(
            "Museum deaccessions (sells/transfers) the gifted work within 3 "
            "years of receipt for less than the claimed FMV. §170(e)(7) "
            "mandatorily recomputes the donor's deduction to the disposition "
            "price; excess deduction is recaptured as ordinary income."
        ),
        implementation=None,
        confidence_if_llm=0.8,
        priority=5,
        source_text=(
            "IRC §170(e)(7), enacted by Pension Protection Act of 2006: if "
            "the donee disposes of applicable property within 3 years of the "
            "contribution, the donor must recapture the deduction in excess "
            "of basis. A statement of intended use under §170(f)(11) signed "
            "by the donee is the only safe harbor against this recapture."
        ),
    ),
]
