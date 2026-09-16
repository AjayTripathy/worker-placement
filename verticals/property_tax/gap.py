from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from core.models import Entity, GapResult, Record

from .cap_law import CapLaw
from .models import Deed, Parcel, Sale

# Default thresholds — overridden by jurisdiction config when injected
_DEFAULT_LOOKBACK_YEARS = 3
_DEFAULT_CAPPED_THRESHOLD = 0.92
_DEFAULT_MIN_TV_DELTA = Decimal("500")
_DEFAULT_AV_RATIO = Decimal("0.5")  # Michigan: AV (SEV) = 50% of market; CA overrides to 1.0


class PropertyTaxGapFunction:
    """
    Computes the gap between current Taxable Value (R) and what it should be (f(M)).

    Method A — sale-based:  expected_tv = sale_price * SEV_RATIO
    Method B — SEV-based:   expected_tv = current SEV (legally definitive under MCL 211.27a)

    method_agreement in metadata:
        "both"      — both methods confirm gap (highest confidence)
        "sev_only"  — TV below assessor's own SEV (legally definitive even without sale)
        "sale_only" — sale price confirms but TV >= SEV (data quality dependent)
        "neither"   — no gap detected
    """

    def __init__(
        self,
        cap_law: CapLaw,
        lookback_years: int = _DEFAULT_LOOKBACK_YEARS,
        capped_threshold: float = _DEFAULT_CAPPED_THRESHOLD,
        min_tv_delta: Decimal = _DEFAULT_MIN_TV_DELTA,
        av_ratio: Decimal = _DEFAULT_AV_RATIO,
    ):
        self.cap_law = cap_law
        self.lookback_years = lookback_years
        self.capped_threshold = Decimal(str(capped_threshold))
        self.min_tv_delta = min_tv_delta
        self.av_ratio = Decimal(str(av_ratio))  # assessed / market: 0.5 (MI) or 1.0 (CA)

    def compute(self, entity: Entity, records: list[Record]) -> GapResult | None:
        parcel = _extract_parcel(records)
        if parcel is None or parcel.taxable_value is None:
            return None

        all_sales = _extract_sales(records)
        deeds = _extract_deeds(records)

        # Filter sales to lookback window — older transfers are no longer actionable
        cutoff = date.today().replace(year=date.today().year - self.lookback_years)
        sales = [s for s in all_sales if s.sale_date >= cutoff]

        best_transfer = _best_transfer(sales, deeds, self.cap_law)

        # Even without a transfer event, a PRE-on-entity violation is an
        # independent fraud signal — the millage rate is wrong on its own,
        # no transfer needed. If the parcel matches that pattern, we
        # synthesize a GapResult so the rule chain + scorer can process it.
        pre_entity_only = (parcel.owner_is_entity
                            and (parcel.homestead_pct or 0) > 0)

        if best_transfer is None and not pre_entity_only:
            return None
        if best_transfer is None and pre_entity_only:
            return _synthesize_pre_entity_only(entity, parcel)

        tv = parcel.taxable_value
        sev = parcel.sev

        # Method B — SEV-based
        sev_gap = (
            (sev - tv)
            if (sev and tv and sev > tv
                and (tv / sev) < self.capped_threshold
                and (sev - tv) >= self.min_tv_delta)
            else None
        )

        # Method A — sale-based
        sale_gap = None
        sale_price = None
        transfer_year = None
        data_quality = "no_sale"

        if best_transfer:
            sale_price = _transfer_price(best_transfer)
            transfer_year = _transfer_year(best_transfer)

            if sale_price and sale_price > 0:
                expected_tv_sale = sale_price * self.av_ratio
                raw_sale_gap = expected_tv_sale - tv
                # Apply same threshold to Method A
                sale_gap = (
                    raw_sale_gap
                    if (raw_sale_gap >= self.min_tv_delta
                        and tv > 0
                        and (expected_tv_sale / tv) > (1 + float(self.capped_threshold)))
                    else None
                )
                data_quality = _assess_data_quality(sale_price, sev, expected_tv_sale)
            elif sale_price == 0 or (isinstance(best_transfer, Deed) and best_transfer.is_zero_consideration):
                data_quality = "zero_consideration"
            else:
                data_quality = "no_sale_price"

        # Determine method agreement and primary gap signal
        method_agreement, raw_gap, market_value, expected_regulated = _resolve_methods(
            sale_gap, sev_gap, tv, sev, sale_price, self.av_ratio
        )

        if raw_gap is None or raw_gap <= 0:
            return None  # no gap — clean or no signal

        overdue = (
            transfer_year is not None
            and self.cap_law.is_overdue(parcel, transfer_year)
        )

        flags = []
        if data_quality in ("zero_consideration", "sale_suppressed"):
            flags.append(data_quality)
        if isinstance(best_transfer, Deed) and best_transfer.is_quit_claim:
            flags.append("quit_claim_deed")
        if not overdue and transfer_year is not None:
            flags.append("upcoming")

        return GapResult(
            entity_id=entity.id,
            regulated_value=tv,
            market_value=market_value,
            expected_regulated=expected_regulated,
            raw_gap=raw_gap,
            gap_pct=float(raw_gap / expected_regulated) if expected_regulated else 0.0,
            gap_direction="under_reported" if raw_gap > 0 else "compliant",
            data_quality_flags=flags,
            metadata={
                "method_agreement": method_agreement,
                "data_quality": data_quality,
                "sev_gap": float(sev_gap) if sev_gap else None,
                "sale_gap": float(sale_gap) if sale_gap else None,
                "sale_price": float(sale_price) if sale_price else None,
                "transfer_year": transfer_year,
                "overdue": overdue,
                "owner": parcel.owner,
                "owner_is_entity": parcel.owner_is_entity,
                "nez_district": parcel.nez_district,
                "homestead_pct": parcel.homestead_pct,
                "homeowner_exemption": (parcel.extra or {}).get("homeowner_exemption", False),
                "address": parcel.address,
                "zip_code": parcel.zip_code,
                "tax_status": parcel.tax_status,
                "taxable_value": float(tv) if tv else None,
            },
        )


def _synthesize_pre_entity_only(entity: Entity, parcel: Parcel) -> GapResult:
    """Build a GapResult for the PRE-on-entity-only case (no TV-uncap fraud
    detected, but owner is an entity claiming PRE). The TV-gap is 0; the
    PRE_ENTITY_VIOLATION rule computes the millage-differential dollar gap
    from metadata. Without this synthesis, the engine would return None
    and the violation would never reach the rule chain."""
    tv = parcel.taxable_value
    sev = parcel.sev or tv
    return GapResult(
        entity_id=entity.id,
        regulated_value=tv,
        market_value=sev,
        expected_regulated=tv,
        raw_gap=Decimal(0),
        gap_pct=0.0,
        gap_direction="compliant",
        data_quality_flags=["pre_entity_only"],
        metadata={
            "method_agreement": "pre_entity_only",
            "data_quality": "no_transfer",
            "owner": parcel.owner,
            "owner_is_entity": True,
            "nez_district": parcel.nez_district,
            "homestead_pct": parcel.homestead_pct,
            "address": parcel.address,
            "zip_code": parcel.zip_code,
            "tax_status": parcel.tax_status,
            "taxable_value": float(tv) if tv else None,
            "overdue": False,
        },
    )


def _resolve_methods(sale_gap, sev_gap, tv, sev, sale_price, av_ratio):
    """Returns (method_agreement, raw_gap, market_value, expected_regulated)."""
    sale_confirms = sale_gap is not None and sale_gap > 0
    sev_confirms = sev_gap is not None and sev_gap > 0

    if sale_confirms and sev_confirms:
        # Use SEV/AV gap as primary (legally definitive); sale gap as corroboration
        return "both", sev_gap, sev, sev
    elif sev_confirms:
        return "sev_only", sev_gap, sev, sev
    elif sale_confirms:
        expected = sale_price * av_ratio
        return "sale_only", sale_gap, sale_price, expected
    else:
        return "neither", None, None, None


def _assess_data_quality(sale_price: Decimal, sev: Decimal | None, expected_tv: Decimal) -> str:
    if sev is None:
        return "no_sev"
    market_est = sev * 2  # SEV is 50% of market
    if sale_price > market_est * 3:
        return "sale_inflated"
    if sale_price < market_est * Decimal("0.3"):
        return "sale_suppressed"
    return "consistent"


def _best_transfer(sales: list[Sale], deeds: list[Deed], cap_law: CapLaw) -> Sale | Deed | None:
    """Most recent arm's-length transfer, preferring deeds over MLS sales."""
    arm_length_deeds = [d for d in deeds if cap_law.is_arms_length(d)]
    if arm_length_deeds:
        return max(arm_length_deeds, key=lambda d: d.sale_date)
    arm_length_sales = [s for s in sales if s.is_arms_length is not False]
    if arm_length_sales:
        return max(arm_length_sales, key=lambda s: s.sale_date)
    # Fall back to any transfer for data quality flagging
    all_transfers = list(deeds) + list(sales)
    return max(all_transfers, key=lambda t: t.sale_date) if all_transfers else None


def _transfer_price(t: Sale | Deed) -> Decimal | None:
    if isinstance(t, Deed):
        return t.consideration if t.consideration > 0 else None
    return t.sale_price


def _transfer_year(t: Sale | Deed) -> int:
    return t.sale_date.year


def _extract_parcel(records: list[Record]) -> Parcel | None:
    for r in records:
        if r.record_type == "assessment":
            return Parcel(**r.data)
    return None


def _extract_sales(records: list[Record]) -> list[Sale]:
    out = []
    for r in records:
        if r.record_type == "sale":
            try:
                out.append(Sale(**r.data))
            except Exception:
                pass
        elif r.record_type == "assessment":
            # Inject the assessor's own transfer record as a baseline sale signal.
            # This is the primary signal for the SEV-only method and the overdue check
            # when no MLS/deed data is available — same logic as the original detroit_fraud tool.
            td = r.data.get("transfer_date")
            if td:
                try:
                    from datetime import date as date_type
                    sale_date = (
                        date_type.fromisoformat(str(td)[:10])
                        if isinstance(td, str) else td
                    )
                    out.append(Sale(
                        parcel_id=r.entity_id,
                        sale_date=sale_date,
                        sale_price=r.data.get("sale_price_record"),
                        source="assessor_record",
                        is_arms_length=None,
                    ))
                except Exception:
                    pass
    return out


def _extract_deeds(records: list[Record]) -> list[Deed]:
    out = []
    for r in records:
        if r.record_type == "deed":
            try:
                out.append(Deed(**r.data))
            except Exception:
                pass
    return out
