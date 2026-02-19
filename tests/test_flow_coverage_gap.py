import pytest
from pydantic import BaseModel, ValidationError
from coreason_manifest.spec.core.flow import DataSchema

class Wrapper(BaseModel):
    ds: DataSchema

def test_dataschema_idempotency_via_wrapper():
    """
    Test line 69: Idempotency Guard.
    When a DataSchema instance is passed to a field expecting DataSchema,
    Pydantic might pass it to the validator.
    """
    ds = DataSchema(json_schema={"type": "string"})
    # Passing the instance to a model field
    w = Wrapper(ds=ds)
    assert w.ds is ds
    assert w.ds.json_schema == {"type": "string"}

def test_dataschema_idempotency_direct_call():
    """
    Directly call the classmethod to ensure line 69 coverage if Pydantic optimizes it away.
    """
    ds = DataSchema(json_schema={"type": "integer"})
    result = DataSchema.validate_meta_schema(ds)
    assert result is ds

def test_dataschema_invalid_type():
    """
    Test line 87: Explicit Type Guarding.
    Ensures that if json_schema is not a dict and not a bool, a ValueError is raised.
    """
    with pytest.raises(ValidationError) as excinfo:
        DataSchema(json_schema=123)  # type: ignore

    # We expect the inner ValueError to be caught and wrapped by Pydantic's ValidationError
    # The message from line 88 should be present.
    assert "JSON Schema must be a dictionary or a boolean" in str(excinfo.value)

def test_dataschema_invalid_type_string():
    """
    Test line 87 with string (which is not dict or bool).
    """
    with pytest.raises(ValidationError) as excinfo:
        DataSchema(json_schema="invalid")  # type: ignore

    assert "JSON Schema must be a dictionary or a boolean" in str(excinfo.value)
