# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import pytest
from pydantic import ValidationError

from coreason_manifest.core.common.typeahead import (
    SuggestionMapper,
    TypeaheadConfig,
    TypeaheadEndpoint,
)


def test_suggestion_mapper_valid() -> None:
    """Test SuggestionMapper instantiates with valid pointers."""
    mapper = SuggestionMapper(
        results_path="/hits",
        title_pointer="/name",
        subtitle_pointer="/desc",
        icon_pointer="/icon",
        value_pointer="/id",
    )
    assert mapper.results_path == "/hits"
    assert mapper.title_pointer == "/name"
    assert mapper.subtitle_pointer == "/desc"
    assert mapper.icon_pointer == "/icon"
    assert mapper.value_pointer == "/id"


def test_suggestion_mapper_invalid_pointer() -> None:
    """Test SuggestionMapper raises ValidationError if any pointer does not start with /."""
    with pytest.raises(ValidationError) as exc_info:
        SuggestionMapper(
            results_path="hits",  # Invalid
            title_pointer="/name",
            value_pointer="/id",
        )
    assert "must start with '/'" in str(exc_info.value)

    with pytest.raises(ValidationError) as exc_info:
        SuggestionMapper(
            results_path="/hits",
            title_pointer="name",  # Invalid
            value_pointer="/id",
        )
    assert "must start with '/'" in str(exc_info.value)

    with pytest.raises(ValidationError) as exc_info:
        SuggestionMapper(
            results_path="/hits",
            title_pointer="/name",
            subtitle_pointer="desc",  # Invalid
            value_pointer="/id",
        )
    assert "must start with '/'" in str(exc_info.value)

    with pytest.raises(ValidationError) as exc_info:
        SuggestionMapper(
            results_path="/hits",
            title_pointer="/name",
            icon_pointer="icon",  # Invalid
            value_pointer="/id",
        )
    assert "must start with '/'" in str(exc_info.value)


def test_typeahead_config_valid() -> None:
    """Test TypeaheadConfig instantiates with valid data."""
    mapper = SuggestionMapper(
        results_path="/data/hits",
        title_pointer="/name",
        value_pointer="/id",
    )
    endpoint = TypeaheadEndpoint(
        uri="https://api.example.com/search?q=$query",
        method="GET",
        headers={"Authorization": "Bearer token"},
        cache_ttl_seconds=120,
    )
    config = TypeaheadConfig(
        endpoint=endpoint,
        mapper=mapper,
        debounce_ms=300,
        min_chars_to_trigger=2,
        on_select_trigger="submit_search",
    )
    assert config.debounce_ms == 300
    assert config.min_chars_to_trigger == 2
    assert config.on_select_trigger == "submit_search"


def test_typeahead_config_debounce_too_low() -> None:
    """Test TypeaheadConfig raises ValidationError if debounce_ms is strictly less than 100."""
    mapper = SuggestionMapper(
        results_path="/data/hits",
        title_pointer="/name",
        value_pointer="/id",
    )
    endpoint = TypeaheadEndpoint(
        uri="https://api.example.com/search?q=$query",
    )
    with pytest.raises(ValidationError) as exc_info:
        TypeaheadConfig(
            endpoint=endpoint,
            mapper=mapper,
            debounce_ms=99,
            min_chars_to_trigger=2,
        )
    assert "debounce_ms must be strictly >= 100" in str(exc_info.value)


def test_typeahead_config_min_chars_too_low() -> None:
    """Test TypeaheadConfig raises ValidationError if min_chars_to_trigger is strictly less than 1."""
    mapper = SuggestionMapper(
        results_path="/data/hits",
        title_pointer="/name",
        value_pointer="/id",
    )
    endpoint = TypeaheadEndpoint(
        uri="https://api.example.com/search?q=$query",
    )
    with pytest.raises(ValidationError) as exc_info:
        TypeaheadConfig(
            endpoint=endpoint,
            mapper=mapper,
            debounce_ms=300,
            min_chars_to_trigger=0,
        )
    assert "min_chars_to_trigger must be strictly >= 1" in str(exc_info.value)
