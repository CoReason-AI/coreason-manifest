from typing import Any

import pytest
from pydantic import ValidationError

from coreason_manifest.spec.interop.antibody import AntibodyBase


class PayloadModel(AntibodyBase):
    foo: str
    bar: float | None = None
    nested: dict[str, Any] | None = None


def test_antibody_clean_data() -> None:
    data = {"foo": "valid", "bar": 1.23}
    model = PayloadModel.model_validate(data)
    assert model.foo == "valid"
    assert model.bar == 1.23


def test_antibody_strict_float_failure() -> None:
    """
    If a strict float field receives NaN, Antibody converts it to DataAnomaly.
    Pydantic then validates the field against 'float', which fails because DataAnomaly (dict) is not float.
    This is expected behavior: we reject bad data for strict fields, but avoid crashing on NaN itself.
    """
    data = {"foo": "invalid", "bar": float("nan")}

    with pytest.raises(ValidationError) as exc:
        PayloadModel.model_validate(data)

    errors = exc.value.errors()
    # Pydantic standard validation error because DataAnomaly dict is not a float
    assert errors[0]["type"] == "float_type" or "Input should be a valid number" in errors[0]["msg"]


def test_antibody_any_field_mutation_dict_in_dict() -> None:
    """
    Test recursive dict inside dict.
    """
    data = {"foo": "valid", "nested": {"deep": float("nan")}}

    model = PayloadModel.model_validate(data)

    assert model.nested is not None
    anomaly = model.nested["deep"]
    assert isinstance(anomaly, dict)
    assert anomaly["code"] == "CRSN-ANTIBODY-FLOAT"
    assert anomaly["path"] == "$.nested.deep"
    assert anomaly["value_repr"] == "nan"


def test_antibody_any_field_mutation_list_in_dict() -> None:
    """
    Test recursive list inside dict.
    """
    data = {"foo": "valid", "nested": {"list": [float("nan")]}}

    model = PayloadModel.model_validate(data)

    assert model.nested is not None
    anomaly = model.nested["list"][0]
    assert isinstance(anomaly, dict)
    assert anomaly["code"] == "CRSN-ANTIBODY-FLOAT"
    assert anomaly["path"] == "$.nested.list[0]"


def test_antibody_list_mutation_dict_in_list() -> None:
    """
    Test recursive dict inside list.
    """

    class ListPayload(AntibodyBase):
        items: list[Any]

    data = {"items": [{"val": float("nan")}]}

    model = ListPayload.model_validate(data)

    anomaly = model.items[0]["val"]
    assert isinstance(anomaly, dict)
    assert anomaly["path"] == "$.items[0].val"


def test_antibody_list_mutation_list_in_list() -> None:
    """
    Test recursive list inside list.
    """

    class ListPayload(AntibodyBase):
        items: list[Any]

    data = {"items": [[float("nan")]]}

    model = ListPayload.model_validate(data)

    anomaly = model.items[0][0]
    assert isinstance(anomaly, dict)
    assert anomaly["path"] == "$.items[0][0]"
