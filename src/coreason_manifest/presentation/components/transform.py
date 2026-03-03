from enum import StrEnum
from typing import Any, Union

from pydantic import Field, model_validator

from coreason_manifest.core.common.base import CoreasonModel


class TransformOperator(StrEnum):
    EQUALS = "EQUALS"
    NOT_EQUALS = "NOT_EQUALS"
    GREATER_THAN = "GREATER_THAN"
    LESS_THAN = "LESS_THAN"
    GREATER_THAN_OR_EQUAL = "GREATER_THAN_OR_EQUAL"
    LESS_THAN_OR_EQUAL = "LESS_THAN_OR_EQUAL"
    CONTAINS = "CONTAINS"
    STARTS_WITH = "STARTS_WITH"
    ENDS_WITH = "ENDS_WITH"
    REGEX_MATCH = "REGEX_MATCH"
    IN_LIST = "IN_LIST"
    NOT_IN_LIST = "NOT_IN_LIST"
    IS_NULL = "IS_NULL"
    IS_NOT_NULL = "IS_NOT_NULL"


class LogicalOperator(StrEnum):
    AND = "AND"
    OR = "OR"
    NOT = "NOT"


class SortDirection(StrEnum):
    ASC = "ASC"
    DESC = "DESC"


class FilterRule(CoreasonModel):
    field_pointer: str = Field(description="The JSON Pointer to the data key being evaluated, e.g., `/item/price`.")
    operator: TransformOperator
    value: Any | None = None
    value_pointer: str | None = None

    @model_validator(mode="after")
    def validate_pointers_and_values(self) -> "FilterRule":
        if not self.field_pointer.startswith("/"):
            raise ValueError("field_pointer must be a valid RFC 6901 JSON pointer starting with '/'")

        if self.value_pointer is not None and not self.value_pointer.startswith("$local."):
            raise ValueError("value_pointer MUST start with '$local.'")

        if self.operator not in (TransformOperator.IS_NULL, TransformOperator.IS_NOT_NULL) and (
            (self.value is not None and self.value_pointer is not None)
            or (self.value is None and self.value_pointer is None)
        ):
            raise ValueError("Exactly one of value or value_pointer must be provided")

        return self


class FilterGroup(CoreasonModel):
    logic: LogicalOperator
    conditions: list[Union["FilterRule", "FilterGroup"]]

    @model_validator(mode="after")
    def validate_recursion_depth(self) -> "FilterGroup":
        def _get_depth(group: "FilterGroup") -> int:
            max_depth = 1
            for condition in group.conditions:
                if isinstance(condition, FilterGroup):
                    max_depth = max(max_depth, 1 + _get_depth(condition))
            return max_depth

        depth = _get_depth(self)
        if depth > 3:
            raise ValueError("FilterGroup recursion depth cannot exceed 3 levels")

        return self


class DataSortRule(CoreasonModel):
    field_pointer: str
    direction: SortDirection

    @model_validator(mode="after")
    def validate_pointer(self) -> "DataSortRule":
        if not self.field_pointer.startswith("/"):
            raise ValueError("field_pointer must be a valid RFC 6901 JSON pointer starting with '/'")
        return self


class DataTransformSchema(CoreasonModel):
    filter: FilterGroup | FilterRule | None = Field(default=None, description="The AST defining edge-filtering logic.")
    sort: list[DataSortRule] = Field(default_factory=list, description="Ordered array of sorting instructions.")
    limit: int | None = Field(default=None, description="Optional integer for client-side truncation/pagination.")
