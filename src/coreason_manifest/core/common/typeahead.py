# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from typing import Literal

from pydantic import Field, model_validator

from coreason_manifest.core.common.base import CoreasonModel


class SuggestionMapper(CoreasonModel):
    """
    Mapping Engine for external fast-path APIs to JSON shapes.
    Uses RFC 6901 JSON Pointers to tell the frontend exactly how to extract data
    from the API response to render the dropdown UI.
    """

    results_path: str
    title_pointer: str
    subtitle_pointer: str | None = None
    icon_pointer: str | None = None
    value_pointer: str

    @model_validator(mode="after")
    def validate_pointers(self) -> "SuggestionMapper":
        pointers = [
            self.results_path,
            self.title_pointer,
            self.subtitle_pointer,
            self.icon_pointer,
            self.value_pointer,
        ]

        for pointer in pointers:
            if pointer is not None and not pointer.startswith("/"):
                raise ValueError(f"JSON pointer '{pointer}' must start with '/'")

        return self


class TypeaheadEndpoint(CoreasonModel):
    """
    Defines the exact network connection the client should make.
    """

    uri: str
    method: Literal["GET", "POST"] = "GET"
    headers: dict[str, str] | None = None
    cache_ttl_seconds: int = Field(default=60, description="How long the client should locally cache queries.")


class TypeaheadConfig(CoreasonModel):
    """
    Groups the endpoint, mapper, and essential network throttling disciplines.
    """

    endpoint: TypeaheadEndpoint
    mapper: SuggestionMapper
    debounce_ms: int = Field(
        default=300,
        description="Milliseconds to wait after the last keystroke before firing the network request.",
    )
    min_chars_to_trigger: int = Field(
        default=2,
        description="Minimum characters required in the input before initiating a search.",
    )
    on_select_trigger: str | None = Field(
        default=None,
        description=(
            "Optional UIEventMap trigger name. If defined, selecting a suggestion "
            "instantly fires this event to the AI backend, bypassing standard input population."
        ),
    )

    @model_validator(mode="after")
    def validate_security_guards(self) -> "TypeaheadConfig":
        if self.debounce_ms < 100:
            raise ValueError("debounce_ms must be strictly >= 100 to prevent DDoS.")
        if self.min_chars_to_trigger < 1:
            raise ValueError("min_chars_to_trigger must be strictly >= 1.")
        return self
