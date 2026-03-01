import re
from enum import StrEnum

from pydantic import model_validator

from coreason_manifest.core.common.base import CoreasonModel


class SkeletonType(StrEnum):
    TEXT_SHIMMER = "text_shimmer"
    MEDIA_BLOCK = "media_block"
    CHART_PULSE = "chart_pulse"
    TABLE_ROWS = "table_rows"
    SPINNER = "spinner"


class SuspenseConfig(CoreasonModel):
    fallback_type: SkeletonType = SkeletonType.SPINNER
    estimated_duration_ms: int | None = None
    reserved_height: str | None = None

    @model_validator(mode="after")
    def validate_reserved_height(self) -> "SuspenseConfig":
        if self.reserved_height is not None:
            # Check if it's a valid CSS dimension
            pattern = re.compile(r"^\d+(?:\.\d+)?(?:px|rem|em|vh|vw|%)$")
            if not pattern.match(self.reserved_height):
                raise ValueError(f"Invalid CSS dimension: {self.reserved_height}")
        return self
