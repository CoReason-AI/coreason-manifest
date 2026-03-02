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

from coreason_manifest.core.common.highlighting import HighlightConfig, HighlightRule, HighlightStyle, MatchType
from coreason_manifest.core.common.search_layout import (
    HybridSearchLayout,
    LayoutPartitionConfig,
    PartitionType,
    SearchPartitionNode,
)
from coreason_manifest.core.common.templating import (
    ParameterizedDataRef,
    StateDependencyConfig,
    TemplateString,
    TemplateVariable,
)
from coreason_manifest.core.common.transform import DataSortRule, DataTransformSchema, SortDirection
from coreason_manifest.core.common.typeahead import SuggestionMapper, TypeaheadConfig, TypeaheadEndpoint


def test_layout_partition_config_valid() -> None:
    config = LayoutPartitionConfig(flex_ratio=2, mobile_stack_order=0)
    assert config.flex_ratio == 2
    assert config.mobile_stack_order == 0


def test_layout_partition_config_invalid_flex_ratio() -> None:
    with pytest.raises(ValidationError, match="flex_ratio must be strictly >= 1"):
        LayoutPartitionConfig(flex_ratio=0)


def test_layout_partition_config_invalid_mobile_stack_order() -> None:
    with pytest.raises(ValidationError, match="mobile_stack_order must be >= 0"):
        LayoutPartitionConfig(mobile_stack_order=-1)


def test_search_partition_node_initialization() -> None:
    transform = DataTransformSchema(sort=[DataSortRule(field_pointer="/title", direction=SortDirection.ASC)])

    data_ref = ParameterizedDataRef(
        uri_template=TemplateString(
            template="/api/search?q={query}", variables={"query": TemplateVariable(pointer="$local.q")}
        ),
        dependency_config=StateDependencyConfig(trigger_pointers=["$local.q"]),
    )

    highlighting = HighlightConfig(
        rules=[HighlightRule(pattern="query", match_type=MatchType.LITERAL, style=HighlightStyle.MARKER_YELLOW)]
    )

    node = SearchPartitionNode(
        target_node_id="test_node_1",
        partition_type=PartitionType.LEXICAL_RESULTS,
        layout=LayoutPartitionConfig(flex_ratio=2, mobile_stack_order=1),
        data_ref=data_ref,
        transform=transform,
        highlighting=highlighting,
    )

    assert node.target_node_id == "test_node_1"
    assert node.partition_type == PartitionType.LEXICAL_RESULTS
    assert node.layout.flex_ratio == 2
    assert node.layout.mobile_stack_order == 1
    assert node.data_ref is not None
    assert node.transform is not None
    assert node.highlighting is not None


def test_hybrid_search_layout_valid() -> None:
    node1 = SearchPartitionNode(target_node_id="results_panel", partition_type=PartitionType.LEXICAL_RESULTS)
    node2 = SearchPartitionNode(target_node_id="ai_overview", partition_type=PartitionType.GENERATIVE_ANSWER)

    layout = HybridSearchLayout(partitions=[node1, node2])

    assert len(layout.partitions) == 2
    assert layout.partitions[0].target_node_id == "results_panel"
    assert layout.partitions[1].target_node_id == "ai_overview"


def test_hybrid_search_layout_duplicate_target_node_id() -> None:
    node1 = SearchPartitionNode(target_node_id="results_panel", partition_type=PartitionType.LEXICAL_RESULTS)
    node2 = SearchPartitionNode(target_node_id="results_panel", partition_type=PartitionType.GENERATIVE_ANSWER)

    with pytest.raises(ValidationError, match="Duplicate target_node_id found: 'results_panel'"):
        HybridSearchLayout(partitions=[node1, node2])


def test_hybrid_search_layout_with_typeahead() -> None:
    typeahead = TypeaheadConfig(
        endpoint=TypeaheadEndpoint(uri="/api/suggest"),
        mapper=SuggestionMapper(results_path="/data", title_pointer="/title", value_pointer="/value"),
    )

    node = SearchPartitionNode(target_node_id="main_panel", partition_type=PartitionType.LEXICAL_RESULTS)

    layout = HybridSearchLayout(search_bar_typeahead=typeahead, partitions=[node])

    assert layout.search_bar_typeahead is not None
    assert layout.search_bar_typeahead.endpoint.uri == "/api/suggest"
    assert len(layout.partitions) == 1
