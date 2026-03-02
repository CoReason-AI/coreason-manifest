import pytest
from pydantic import ValidationError

from coreason_manifest.core.common.transform import (
    DataSortRule,
    DataTransformSchema,
    FilterGroup,
    FilterRule,
    LogicalOperator,
    SortDirection,
    TransformOperator,
)


def test_valid_data_transform_schema_instantiation() -> None:
    """Test valid DataTransformSchema with nested FilterGroup"""
    filter_rule_1 = FilterRule(
        field_pointer="/item/price",
        operator=TransformOperator.GREATER_THAN,
        value=10.0,
    )

    filter_rule_2 = FilterRule(
        field_pointer="/item/category",
        operator=TransformOperator.EQUALS,
        value_pointer="$local.selected_category",
    )

    filter_group = FilterGroup(logic=LogicalOperator.AND, conditions=[filter_rule_1, filter_rule_2])

    sort_rule = DataSortRule(
        field_pointer="/item/price",
        direction=SortDirection.DESC,
    )

    schema = DataTransformSchema(
        filter=filter_group,
        sort=[sort_rule],
        limit=50,
    )

    assert schema.filter is not None
    assert len(schema.sort) == 1
    assert schema.limit == 50


def test_filter_rule_missing_slash_rejection() -> None:
    """Test FilterRule validator rejects missing '/' on field_pointer"""
    with pytest.raises(ValidationError, match="field_pointer must be a valid RFC 6901 JSON pointer starting with '/'"):
        FilterRule(
            field_pointer="item/price",  # Missing leading slash
            operator=TransformOperator.EQUALS,
            value=10,
        )


def test_filter_rule_mutual_exclusivity() -> None:
    """Test FilterRule enforces mutual exclusivity of value vs value_pointer"""
    with pytest.raises(ValidationError, match="Exactly one of value or value_pointer must be provided"):
        FilterRule(
            field_pointer="/item/price",
            operator=TransformOperator.EQUALS,
            value=10,
            value_pointer="$local.price",
        )

    with pytest.raises(ValidationError, match="Exactly one of value or value_pointer must be provided"):
        FilterRule(
            field_pointer="/item/price",
            operator=TransformOperator.EQUALS,
            # Neither value nor value_pointer provided
        )


def test_filter_rule_value_pointer_format() -> None:
    """Test FilterRule blocks value_pointers that do not start with $local."""
    with pytest.raises(ValidationError, match=r"value_pointer MUST start with '\$local.'"):
        FilterRule(
            field_pointer="/item/price",
            operator=TransformOperator.EQUALS,
            value_pointer="global.price",  # Missing $local.
        )


def test_filter_group_recursion_depth_limit() -> None:
    """Test FilterGroup raises ValueError if nesting depth exceeds 3"""
    rule = FilterRule(
        field_pointer="/item/price",
        operator=TransformOperator.EQUALS,
        value=10,
    )

    group_level_4 = FilterGroup(logic=LogicalOperator.OR, conditions=[rule])
    group_level_3 = FilterGroup(logic=LogicalOperator.AND, conditions=[group_level_4])
    group_level_2 = FilterGroup(logic=LogicalOperator.OR, conditions=[group_level_3])

    with pytest.raises(ValidationError, match="FilterGroup recursion depth cannot exceed 3 levels"):
        FilterGroup(logic=LogicalOperator.AND, conditions=[group_level_2])
