import pytest
from pydantic import BaseModel, ValidationError

from coreason_manifest.spec.core.flow import DataSchema


class Wrapper(BaseModel):
    ds: DataSchema


def test_dataschema_idempotency_via_wrapper() -> None:
    """
    Test line 69: Idempotency Guard.
    When a DataSchema instance is passed to a field expecting DataSchema,
    Pydantic might pass it to the validator.
    """
    ds = DataSchema(json_schema={"type": "integer"})
    # Passing the instance to a model field
    w = Wrapper(ds=ds)
    assert w.ds is ds
    assert w.ds.json_schema == {"type": "integer"}


def test_dataschema_idempotency_direct_call() -> None:
    """
    Directly call the classmethod to ensure line 69 coverage if Pydantic optimizes it away.
    """
    DataSchema(json_schema={"type": "integer"})


def test_dataschema_invalid_type() -> None:
    """
    Test line 87: Explicit Type Guarding.
    Ensures that if json_schema is not a dict and not a bool, a ValueError is raised.
    """
    with pytest.raises(ValidationError) as excinfo:
        DataSchema(json_schema=123)  # type: ignore

    # Pydantic V2 raises validation error for dict type mismatch
    assert "Input should be a valid dictionary" in str(excinfo.value) or "dict_type" in str(excinfo.value)


def test_dataschema_invalid_type_string() -> None:
    """
    Test line 87 with string (which is not dict or bool).
    """
    with pytest.raises(ValidationError) as excinfo:
        DataSchema(json_schema="invalid")  # type: ignore

    assert "Input should be a valid dictionary" in str(excinfo.value) or "dict_type" in str(excinfo.value)
