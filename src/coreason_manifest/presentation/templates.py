from pydantic import Field

from coreason_manifest.core.base import CoreasonBaseModel


class DynamicLayoutTemplate(CoreasonBaseModel):
    """Schema representing a template for dynamic grid layouts."""

    layout_tstring: str = Field(
        description="A Python 3.14 t-string template definition for dynamic UI grid evaluation."
    )
