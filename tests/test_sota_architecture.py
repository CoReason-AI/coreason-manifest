import json
from typing import Any

from pydantic import AliasChoices, Field

from coreason_manifest.spec.common_base import CoreasonModel
from coreason_manifest.spec.core.flow import Manifest
from coreason_manifest.spec.core.types import CoercibleStringList


class AliasModel(CoreasonModel):
    timeout_sec: int = Field(alias="timeout-sec")
    name: str


class CollectionModel(CoreasonModel):
    tags: CoercibleStringList


def test_alias_integrity() -> None:
    """Test that aliases are respected and not funneled into annotations."""
    data = {"timeout-sec": 60, "name": "test"}
    model = AliasModel.model_validate(data)
    assert model.timeout_sec == 60
    assert model.name == "test"
    # Ensure it wasn't moved to annotations
    assert "timeout-sec" not in model.annotations
    assert "timeout_sec" not in model.annotations

    # Test funneling of actual extra fields
    data_extra = {"timeout-sec": 60, "name": "test", "extra_field": "val"}
    model_extra = AliasModel.model_validate(data_extra)
    assert model_extra.timeout_sec == 60
    assert model_extra.annotations.get("extra_field") == "val"


class CanonicalModel(CoreasonModel):
    tags: list[str]


def test_canonical_hash_determinism() -> None:
    """Test that model_dump_canonical produces deterministic output for unordered inputs."""
    # Create data that would produce different json dumps order if set-to-list conversion is random
    # We simulate this by manually creating lists in different orders
    m1 = CanonicalModel(tags=["a", "b", "c"])
    m2 = CanonicalModel(tags=["c", "b", "a"])

    # They are logically different lists, but if we treat them as sets for canonicalization...
    # Wait, the fix says "recursively sort lists".
    # If the input is a list, it sorts it.
    # This implies lists are treated as sets for canonicalization?
    # "SOTA Fix: Recursively sort lists to prevent non-deterministic set-to-list casting"
    # Yes, it seems it treats all lists as sortable collections.

    dump1 = m1.model_dump_canonical()
    dump2 = m2.model_dump_canonical()

    assert dump1 == dump2


def test_coercion_string_list() -> None:
    """Test that comma-separated strings are coerced into lists."""
    model = CollectionModel(tags="research, scraper")  # type: ignore[arg-type]
    assert model.tags == ["research", "scraper"]

    model2 = CollectionModel(tags=" single ")  # type: ignore[arg-type]
    assert model2.tags == ["single"]

    model3 = CollectionModel(tags=["already", "list"])
    assert model3.tags == ["already", "list"]


def test_json_schema_export_meta() -> None:
    """Test that export_json_schema includes meta tags."""
    schema_str = Manifest.export_json_schema()
    schema = schema_str

    assert schema["$schema"] == "http://json-schema.org/draft-07/schema#"
    assert schema["title"] == "Coreason Manifest Specification v2"


class AliasChoicesModel(CoreasonModel):
    """Test model with AliasChoices."""

    priority: int = Field(validation_alias=AliasChoices("prio", "importance"))


def test_alias_choices_integrity() -> None:
    """Test that AliasChoices are respected and not funneled."""
    # Case 1: Use first choice
    data1 = {"prio": 1}
    m1 = AliasChoicesModel.model_validate(data1)
    assert m1.priority == 1
    assert "prio" not in m1.annotations

    # Case 2: Use second choice
    data2 = {"importance": 2}
    m2 = AliasChoicesModel.model_validate(data2)
    assert m2.priority == 2
    assert "importance" not in m2.annotations


class ComplexCanonicalModel(CoreasonModel):
    items: list[dict[str, Any]]


def test_canonical_hash_unorderable() -> None:
    """Test canonicalization of lists containing unorderable items (dicts)."""
    # List of dicts cannot be sorted in Python 3 directly
    m = ComplexCanonicalModel(items=[{"b": 2}, {"a": 1}])

    # This should not raise TypeError (hits the except TypeError block)
    m.model_dump_canonical()


def test_model_dump_json_determinism() -> None:
    """Test model_dump_json ensures sorted keys and handles indent."""
    # Use field name to instantiate
    m = AliasModel(name="test", timeout_sec=60)

    # Check default dump (no indent, sorted keys)
    json_out = m.model_dump_json()

    # Verify keys are sorted alphabetically
    loaded = json.loads(json_out)
    keys = list(loaded.keys())
    assert keys == sorted(keys)
    assert keys == ["annotations", "name", "timeout_sec"]

    # Test indent
    json_indent = m.model_dump_json(indent=2)
    assert '  "name": "test",' in json_indent
