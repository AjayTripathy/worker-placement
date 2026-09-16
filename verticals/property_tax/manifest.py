from core.models import VerticalManifest

PROPERTY_TAX_MANIFEST = VerticalManifest(
    vertical="property_tax",
    required_source_types=["assessment"],
    optional_source_types=["sale", "deed"],
)
