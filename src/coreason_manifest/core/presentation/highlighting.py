# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import re
from enum import StrEnum

from pydantic import Field, model_validator

from coreason_manifest.core.common.base import CoreasonModel


class HighlightStyle(StrEnum):
    MARKER_YELLOW = "MARKER_YELLOW"
    MARKER_RED = "MARKER_RED"
    MARKER_GREEN = "MARKER_GREEN"
    TEXT_BOLD = "TEXT_BOLD"
    TEXT_INVERTED = "TEXT_INVERTED"
    SQUIGGLY_RED_LINE = "SQUIGGLY_RED_LINE"


class MatchType(StrEnum):
    LITERAL = "LITERAL"
    REGEX = "REGEX"
    WORD_BOUNDARY = "WORD_BOUNDARY"


class HighlightRule(CoreasonModel):
    pattern: str = Field(
        ...,
        description="The string to find, a Regex pattern, or an ephemeral pointer (e.g., '$local.search_query').",
    )
    match_type: MatchType = Field(
        default=MatchType.LITERAL,
        description="How the client should evaluate the pattern.",
    )
    style: HighlightStyle = Field(
        default=HighlightStyle.MARKER_YELLOW,
        description="The native visual style to apply.",
    )
    case_sensitive: bool = Field(
        default=False,
        description="Whether the match should respect casing.",
    )

    @model_validator(mode="after")
    def validate_regex(self) -> "HighlightRule":
        if self.match_type == MatchType.REGEX and not self.pattern.startswith("$local."):
            try:
                re.compile(self.pattern)
            except re.error as e:
                raise ValueError(f"Invalid Regex pattern: '{self.pattern}'. Error: {e}") from e
        return self


class HighlightConfig(CoreasonModel):
    rules: list[HighlightRule] = Field(
        default_factory=list,
        description="An ordered list of overlay rules. The client evaluates them in sequence.",
    )
