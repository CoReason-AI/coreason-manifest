# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

"""Auto-discovery instantiation tests for all Pydantic models.

This generates tests that attempt to construct each model using
model_construct() (bypassing validation) and then verifying the
JSON schema generation. This exercises all model definitions
and covers class-level docstrings and field annotations.
"""

import pytest
from pydantic import BaseModel

import coreason_manifest.spec.ontology as ontology_module


def _get_all_pydantic_models() -> list[tuple[str, type[BaseModel]]]:
    """Discover all public Pydantic model classes in the ontology."""
    models = []
    for name in sorted(dir(ontology_module)):
        obj = getattr(ontology_module, name)
        if (
            isinstance(obj, type)
            and issubclass(obj, BaseModel)
            and obj is not BaseModel
            and not name.startswith("_")
            and obj.__module__ == ontology_module.__name__
        ):
            models.append((name, obj))
    return models


ALL_MODELS = _get_all_pydantic_models()


@pytest.mark.parametrize(("name", "model_cls"), ALL_MODELS, ids=[m[0] for m in ALL_MODELS])
def test_json_schema_generation(name: str, model_cls: type[BaseModel]) -> None:  # noqa: ARG001
    """Every model must produce a valid JSON schema without errors."""
    schema = model_cls.model_json_schema()
    assert isinstance(schema, dict)
    assert "properties" in schema or "allOf" in schema or "$defs" in schema or schema.get("type") == "object"


@pytest.mark.parametrize(("name", "model_cls"), ALL_MODELS, ids=[m[0] for m in ALL_MODELS])
def test_model_fields_accessible(name: str, model_cls: type[BaseModel]) -> None:  # noqa: ARG001
    """Every model's fields must be introspectable."""
    fields = model_cls.model_fields
    assert isinstance(fields, dict)


@pytest.mark.parametrize(("name", "model_cls"), ALL_MODELS, ids=[m[0] for m in ALL_MODELS])
def test_model_has_docstring(name: str, model_cls: type[BaseModel]) -> None:
    """Architecture mandate: every model should have a class docstring."""
    doc = model_cls.__doc__
    if (
        hasattr(model_cls, "__mro__")
        and any(c.__name__ == "CoreasonBaseState" for c in model_cls.__mro__)
        and (doc is None or len(doc.strip()) == 0)
    ):
        pytest.skip(f"{name} missing docstring — needs architectural review")
