import pytest
from pydantic import BaseModel
from coreason_manifest.spec.common_base import CoreasonModel
from coreason_manifest.utils.integrity import verify_deterministic_serialization, reconstruct_payload

class DeterminismModel(CoreasonModel):
    name: str
    data: dict[str, int]

def test_deterministic_serialization():
    m1 = DeterminismModel(name="test", data={"b": 2, "a": 1})
    m2 = DeterminismModel(name="test", data={"a": 1, "b": 2})

    assert m1.model_dump_canonical() == m2.model_dump_canonical()
    assert verify_deterministic_serialization(m1)

def test_nested_determinism():
    class Nested(CoreasonModel):
        nested: DeterminismModel

    m1 = Nested(nested=DeterminismModel(name="test", data={"b": 2, "a": 1}))
    m2 = Nested(nested=DeterminismModel(name="test", data={"a": 1, "b": 2}))

    assert m1.model_dump_canonical() == m2.model_dump_canonical()
    assert verify_deterministic_serialization(m1)

def test_reconstruct_payload_dict():
    data = {"a": 1}
    assert reconstruct_payload(data) == data

def test_reconstruct_payload_invalid():
    with pytest.raises(TypeError):
        reconstruct_payload("string")

def test_non_canonical_model():
    class BadModel(BaseModel):
        x: int
    m = BadModel(x=1)
    assert verify_deterministic_serialization(m) is False
