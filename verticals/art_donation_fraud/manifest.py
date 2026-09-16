from core.models import VerticalManifest

ART_DONATION_FRAUD_MANIFEST = VerticalManifest(
    vertical="art_donation_fraud",
    required_source_types=["museum_acquisition"],
    optional_source_types=["auction_lot"],
)
