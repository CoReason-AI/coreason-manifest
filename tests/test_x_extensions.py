from typing import Any

from coreason_manifest.spec.common_base import CommonBase


def test_x_extensions_funnel() -> None:
    class MyModel(CommonBase):
        field: str

    # Extra field
    data: dict[str, Any] = {"field": "val", "x-custom": 123, "random": "stuff"}

    model = MyModel(**data)

    assert model.field == "val"
    # Should not prevent instantiation

    # Check annotations
    assert model.annotations["x-custom"] == 123
    assert model.annotations["random"] == "stuff"

    # Check dump
    dump = model.model_dump()
    assert "x-custom" not in dump
    assert "random" not in dump
    assert dump["annotations"]["x-custom"] == 123
