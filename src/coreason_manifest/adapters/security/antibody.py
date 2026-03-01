import math
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class DataAnomaly(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    code: str = Field(..., description="The error code associated with the anomaly.", examples=["CRSN-ANTIBODY-FLOAT"])
    path: str = Field(..., description="The JSON path to the anomalous field.", examples=["$.inputs.temperature"])
    value_repr: str = Field(..., description="A string representation of the anomalous value.", examples=["NaN"])
    description: str = Field(
        ...,
        description="A detailed description of the anomaly.",
        examples=["Floating point value is not finite (NaN/Inf)."],
    )


VALID_PRIMITIVES = (str, int, float, bool, type(None), datetime)


def _get_anomaly(v: Any, path: str) -> dict[str, Any] | None:
    """Evaluate a single value and return a serialized anomaly if invalid."""
    if isinstance(v, BaseModel):
        # We can recursively validate BaseModels later, or just trust their serialization
        return None
    if isinstance(v, float) and not math.isfinite(v):
        anomaly = DataAnomaly(
            code="CRSN-ANTIBODY-FLOAT",
            path=path,
            value_repr=str(v),
            description="Floating point value is not finite (NaN/Inf).",
        )
        return anomaly.model_dump()
    if not isinstance(v, (dict, list, tuple)) and not isinstance(v, VALID_PRIMITIVES):
        return DataAnomaly(
            code="CRSN-ANTIBODY-UNSERIALIZABLE",
            path=path,
            value_repr=str(type(v)),
            description="Object is not deterministically serializable.",
        ).model_dump()
    return None


def _scan_and_quarantine(data: Any, path: str) -> Any:
    """Recursively scan and rebuild the input structure, replacing anomalies with DataAnomaly objects."""
    if isinstance(data, dict):
        return {
            k: _get_anomaly(v, f"{path}.{k}" if path else k)
            or (_scan_and_quarantine(v, f"{path}.{k}" if path else k) if isinstance(v, (dict, list, tuple)) else v)
            for k, v in data.items()
        }
    if isinstance(data, list):
        return [
            _get_anomaly(v, f"{path}[{i}]")
            or (_scan_and_quarantine(v, f"{path}[{i}]") if isinstance(v, (dict, list, tuple)) else v)
            for i, v in enumerate(data)
        ]
    if isinstance(data, tuple):
        # Tuples are immutable; reconstruct them functionally
        return tuple(
            _get_anomaly(v, f"{path}[{i}]")
            or (_scan_and_quarantine(v, f"{path}[{i}]") if isinstance(v, (dict, list, tuple)) else v)
            for i, v in enumerate(data)
        )
    return data


class AntibodyBase(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    @model_validator(mode="before")
    @classmethod
    def run_quarantine(cls, data: Any) -> Any:
        if isinstance(data, (dict, list, tuple)):
            # Assign the functionally rebuilt structure
            data = _scan_and_quarantine(data, "$")
        return data
