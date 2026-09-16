from core.models import VerticalManifest

RENT_STABILIZATION_MANIFEST = VerticalManifest(
    vertical="rent_stabilization",
    required_source_types=["stabilization"],
    optional_source_types=["listing"],
)
