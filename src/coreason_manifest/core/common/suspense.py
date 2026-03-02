import re
from enum import StrEnum

from pydantic import Field, model_validator

from coreason_manifest.core.common.base import CoreasonModel


class SkeletonType(StrEnum):
    TEXT_SHIMMER = "text_shimmer"
    MEDIA_BLOCK = "media_block"
    CHART_PULSE = "chart_pulse"
    TABLE_ROWS = "table_rows"
    SPINNER = "spinner"


class SuspenseConfig(CoreasonModel):
    fallback_type: SkeletonType = SkeletonType.SPINNER
    estimated_duration_ms: int | None = Field(
        default=None, description="The estimated duration in milliseconds before the content is expected to load."
    )
    reserved_height: str | None = Field(
        default=None,
        description="CSS dimension to reserve space while the component is suspended, preventing layout shift.",
    )

    @model_validator(mode="after")
    def validate_reserved_height(self) -> "SuspenseConfig":
        """Enforce dimensional constraints on visual presentation slots.

        Raises:
            ValueError: Yields a validation error if input logic fails syntactic or topological constraints.
        """
        if self.reserved_height is not None:
            # Check if it's a valid CSS dimension
            pattern = re.compile(r"^\d+(?:\.\d+)?(?:px|rem|em|vh|vw|%)$")
            if not pattern.match(self.reserved_height):
                raise ValueError(f"Invalid CSS dimension: {self.reserved_height}")
        return self
