import pytest
import math
from typing import Any
from pydantic import ValidationError
from coreason_manifest.spec.interop.antibody import AntibodyBase, AnomalyDetectedError, DataAnomaly

class PayloadModel(AntibodyBase):
    foo: str
    bar: float | None = None
    nested: dict[str, Any] | None = None

def test_antibody_clean_data() -> None:
    data = {"foo": "valid", "bar": 1.23}
    model = PayloadModel.model_validate(data)
    assert model.foo == "valid"

def test_antibody_nan_detection() -> None:
    data = {"foo": "invalid", "bar": float("nan")}

    with pytest.raises(ValidationError) as exc:
        PayloadModel.model_validate(data)

    errors = exc.value.errors()
    assert len(errors) == 1

    # Access original exception
    original_err = errors[0].get("ctx", {}).get("error")
    assert isinstance(original_err, AnomalyDetectedError)
    assert len(original_err.anomalies) == 1
    assert original_err.anomalies[0].code == "CRSN-ANTIBODY-FLOAT"
    # Expected path starts with $
    assert original_err.anomalies[0].path == "$.bar"

def test_antibody_inf_detection() -> None:
    data = {"foo": "invalid", "bar": float("inf")}

    with pytest.raises(ValidationError) as exc:
        PayloadModel.model_validate(data)

    errors = exc.value.errors()
    original_err = errors[0].get("ctx", {}).get("error")
    assert isinstance(original_err, AnomalyDetectedError)
    assert len(original_err.anomalies) == 1

def test_antibody_nested_detection() -> None:
    data = {
        "foo": "valid",
        "nested": {
            "deep": float("nan")
        }
    }

    with pytest.raises(ValidationError) as exc:
        PayloadModel.model_validate(data)

    errors = exc.value.errors()
    original_err = errors[0].get("ctx", {}).get("error")
    assert isinstance(original_err, AnomalyDetectedError)

    # Path: "$.nested.deep"
    assert original_err.anomalies[0].path == "$.nested.deep"

def test_antibody_list_detection() -> None:
    class ListPayload(AntibodyBase):
        items: list[float]

    data = {"items": [1.0, float("nan"), 3.0]}

    with pytest.raises(ValidationError) as exc:
        ListPayload.model_validate(data)

    errors = exc.value.errors()
    original_err = errors[0].get("ctx", {}).get("error")
    assert isinstance(original_err, AnomalyDetectedError)

    # Path: "$.items[1]"
    assert original_err.anomalies[0].path == "$.items[1]"
