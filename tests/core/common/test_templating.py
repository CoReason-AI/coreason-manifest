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

from coreason_manifest.core.common.templating import (
    ArrayEncodingStyle,
    ParameterizedDataRef,
    StateDependencyConfig,
    TemplateString,
    TemplateVariable,
)


def test_template_variable_valid():
    var = TemplateVariable(pointer="$local.selected_brands")
    assert var.pointer == "$local.selected_brands"
    assert var.array_encoding == ArrayEncodingStyle.COMMA
    assert var.fallback_value is None


def test_template_variable_invalid_pointer():
    with pytest.raises(ValidationError) as exc_info:
        TemplateVariable(pointer="selected_brands")
    assert "pointer must strictly start with '$local.'" in str(exc_info.value)


def test_template_string_valid():
    ts = TemplateString(
        template="/api/search?q={query}&b={brands}",
        variables={
            "query": TemplateVariable(pointer="$local.query"),
            "brands": TemplateVariable(pointer="$local.brands", array_encoding=ArrayEncodingStyle.BRACKET),
        },
    )
    assert ts.template == "/api/search?q={query}&b={brands}"
    assert "query" in ts.variables
    assert "brands" in ts.variables


def test_template_string_missing_variable():
    with pytest.raises(ValidationError) as exc_info:
        TemplateString(
            template="/api/search?q={query}&b={brands}",
            variables={
                "query": TemplateVariable(pointer="$local.query"),
                # Missing 'brands'
            },
        )
    assert "Placeholder 'brands' extracted from template is missing from variables dictionary." in str(
        exc_info.value
    )


def test_state_dependency_config_valid():
    config = StateDependencyConfig(
        trigger_pointers=["$local.selected_brands", "$local.query"],
        debounce_ms=300,
        auto_suspend=True,
    )
    assert config.debounce_ms == 300
    assert config.trigger_pointers == ["$local.selected_brands", "$local.query"]


def test_state_dependency_config_invalid_debounce():
    with pytest.raises(ValidationError) as exc_info:
        StateDependencyConfig(
            trigger_pointers=["$local.selected_brands"],
            debounce_ms=49,
        )
    assert "debounce_ms must be strictly >= 50." in str(exc_info.value)


def test_state_dependency_config_invalid_pointer():
    with pytest.raises(ValidationError) as exc_info:
        StateDependencyConfig(
            trigger_pointers=["$local.selected_brands", "query"],
        )
    assert "trigger_pointer 'query' must strictly start with '$local.'" in str(exc_info.value)


def test_parameterized_data_ref_valid():
    ref = ParameterizedDataRef(
        uri_template=TemplateString(
            template="/api/search?q={query}",
            variables={"query": TemplateVariable(pointer="$local.query")},
        ),
        method="GET",
        headers={"Authorization": "Bearer token"},
        dependency_config=StateDependencyConfig(
            trigger_pointers=["$local.query"],
            debounce_ms=100,
        ),
    )
    assert ref.method == "GET"
    assert ref.headers == {"Authorization": "Bearer token"}
    assert ref.uri_template.template == "/api/search?q={query}"
    assert ref.dependency_config.debounce_ms == 100
