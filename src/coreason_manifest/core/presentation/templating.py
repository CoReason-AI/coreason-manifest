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
from typing import Any, Literal

from pydantic import Field, model_validator

from coreason_manifest.core.common.base import CoreasonModel


class ArrayEncodingStyle(StrEnum):
    COMMA = "COMMA"
    REPEAT = "REPEAT"
    BRACKET = "BRACKET"


class TemplateVariable(CoreasonModel):
    pointer: str = Field(..., description="The ephemeral state pointer, e.g., '$local.selected_brands'.")
    array_encoding: ArrayEncodingStyle = Field(default=ArrayEncodingStyle.COMMA)
    fallback_value: Any | None = Field(
        default=None, description="Value to use if the local variable is currently null."
    )
    required: bool = Field(
        default=False,
        description="If true and the local variable is null with no fallback, the client aborts the network fetch.",
    )

    @model_validator(mode="after")
    def validate_pointer(self) -> "TemplateVariable":
        if not self.pointer.startswith("$local."):
            raise ValueError("pointer must strictly start with '$local.'")
        return self


class TemplateString(CoreasonModel):
    template: str = Field(..., description="The parameterized URI, e.g., '/api/search?q={query}&b={brands}'.")
    variables: dict[str, TemplateVariable] = Field(
        ..., description="Maps template placeholders to variable definitions."
    )

    @model_validator(mode="after")
    def validate_placeholders(self) -> "TemplateString":
        placeholders = set(re.findall(r"\{([a-zA-Z0-9_]+)\}", self.template))
        for p in placeholders:
            if p not in self.variables:
                raise ValueError(f"Placeholder '{p}' extracted from template is missing from variables dictionary.")
        return self


class StateDependencyConfig(CoreasonModel):
    trigger_pointers: list[str] = Field(
        ...,
        description="List of $local pointers that should trigger a network re-fetch when mutated.",
    )
    debounce_ms: int = Field(default=300, description="Network throttling delay after the last state mutation.")
    auto_suspend: bool = Field(
        default=True,
        description="If true, the widget automatically drops into its Suspense skeleton while the new fetch resolves.",
    )

    @model_validator(mode="after")
    def validate_config(self) -> "StateDependencyConfig":
        if self.debounce_ms < 50:
            raise ValueError("debounce_ms must be strictly >= 50.")
        for pointer in self.trigger_pointers:
            if not pointer.startswith("$local."):
                raise ValueError(f"trigger_pointer '{pointer}' must strictly start with '$local.'")
        return self


class ParameterizedDataRef(CoreasonModel):
    uri_template: TemplateString
    method: Literal["GET", "POST"] = Field(default="GET")
    headers: dict[str, str] | None = Field(default=None)
    dependency_config: StateDependencyConfig
