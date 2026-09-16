"""insurer_strength — bond-insurance (wrap) quality, with the rating-conditional lens.

Two parts: (1) which monoline insures the bond and its financial-strength rating; (2) the framework
insight that wrap value is RATING-CONDITIONAL — an insurance wrap compresses spread only when the
UNDERLYING credit is weak (AGM measured ~0 / 140 / 360 bps of compression at AA- / BBB- / CCC). On a
strong unlimited-ad-valorem-GO underlying (our whole book, ~Aa2/Aa3), the wrap adds almost nothing — the
bond stands on its own. So for us this screen is mostly INFORMATIONAL; it only FLAGS the rare case of a
WEAK underlying that is genuinely relying on the wrap (where insurer strength actually matters).

EMMA's free tier gives insured Yes/No but not the insurer name — the insurer is read from the OS cover.
If the insurer can't be confirmed, we say so (insured-insurer-UNVERIFIABLE), never assume a strong wrap.
"""
import re

# current monoline financial-strength ratings (S&P), stable and well-known
INSURER_FSR = [
    (re.compile(r"\bASSURED GUARANTY MUNICIPAL\b|\bAGM\b", re.I),       ("AA", "Assured Guaranty Municipal (AGM)")),
    (re.compile(r"\bBUILD AMERICA MUTUAL\b|\bBAM\b", re.I),             ("AA", "Build America Mutual (BAM)")),
    (re.compile(r"\bASSURED GUARANTY CORP\b|\bAGC\b", re.I),            ("AA", "Assured Guaranty Corp (AGC)")),
    (re.compile(r"\bASSURED GUARANTY\b|\bASSURED\b", re.I),             ("AA", "Assured Guaranty")),
    (re.compile(r"\bNATIONAL PUBLIC FINANCE\b|\bNPFG\b|\bNATIONAL\b", re.I), ("A", "National Public Finance Guarantee")),
    (re.compile(r"\bBERKSHIRE HATHAWAY ASSURANCE\b|\bBHAC\b", re.I),    ("AA+", "Berkshire Hathaway Assurance")),
]


def _detect(insurer, os_text):
    s = (insurer or "") + " " + (os_text or "")     # full OS text — insurer can appear past the cover
    for rx, (fsr, nm) in INSURER_FSR:
        if rx.search(s):
            return nm, fsr
    return None, None


def insurer_strength(insured=None, insurer=None, underlying_rating=None, credit_score=None, os_text=None):
    nm, fsr = _detect(insurer, os_text)
    # The OS cover is authoritative for insurance; EMMA's free-tier "Insured" boolean is often wrong
    # (it read FALSE on AGM-wrapped Lynwood/Natomas). If the OS names a monoline, the bond IS insured,
    # regardless of the EMMA flag.
    if nm:
        insured = True
    if not insured:
        return {"insured": False, "wrap": "uninsured (stands on the GO pledge)"}, []
    weak_underlying = (credit_score is not None and credit_score < 70) or \
                      (str(underlying_rating).upper() in ("BBB", "BBB-", "BB", "B", "CCC"))
    flags = []
    # NOT knowing which AA monoline wraps a STRONG-GO bond is not a risk (the wrap is a tie-break, minimal
    # value) -> insurer-name unknown is a FIELD note, not a flag. Only the genuinely concerning case flags:
    # a WEAK underlying that actually leans on the wrap (where insurer strength matters).
    if weak_underlying:
        flags.append(f"wrap-reliant:weak-underlying/{nm or 'insurer-unknown'}")
    return {"insured": True, "insurer": nm, "insurer_fsr": fsr,
            "wrap_value": ("material — weak underlying genuinely leans on the wrap" if weak_underlying
                           else "minimal — strong underlying stands on its own pledge (wrap is a tie-break, not a crutch)")}, flags
