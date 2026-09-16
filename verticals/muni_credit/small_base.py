"""small_base — flag a small/concentrated tax base.

A small assessed-value (AV) base — or a small enrollment — means a single taxpayer, one new development,
one assessment appeal, or a handful of movers can swing the levy base materially (the prospect's "small
tax base — relatively few people moving can have impact"). An unlimited ad-valorem GO still PAYS on a
small base (Paradise USD was tiny and never defaulted — the unlimited rate simply rises to cover a
shrunken base), so this is a VOLATILITY / REVIEW signal, NOT a default flag. The genuinely fragile case
is the COMBINATION: a small base AND a concentrated top taxpayer (pairs with av_concentration).

Inputs are pulled from the av_concentration cache (av_total, top1 share) + fiscal_health (enrollment).
All flags are soft (REVIEW).
"""
AV_SMALL = 1_000_000_000     # < $1.0B AV = small base
AV_TINY  = 400_000_000       # < $400M  = very small
ENR_SMALL = 2500             # < 2,500 students = small district


def small_base(av_total=None, enrollment=None, top1_share=None):
    flags = []; note = None
    if av_total is not None:
        if av_total < AV_TINY:  flags.append(f"very-small-AV:${av_total/1e6:.0f}M")
        elif av_total < AV_SMALL: flags.append(f"small-AV:${av_total/1e6:.0f}M")
    if enrollment is not None and enrollment < ENR_SMALL:
        flags.append(f"small-enroll:{int(enrollment)}")
    if av_total is not None and av_total < AV_SMALL and (top1_share or 0) >= 10:
        note = "small base AND concentrated top taxpayer — the fragile combination"
        flags.append("small-base+concentrated")
    return {"base_av": av_total, "enrollment": enrollment,
            "small_base": bool(flags), "small_base_note": note}, flags
