import math
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, model_validator


class DataAnomaly(BaseModel):
    """
    Represents a quarantined data segment that failed strict validation
    due to non-computable values (NaN, Inf) or un-serializable types.
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    code: str
    path: str
    value_repr: str
    description: str


VALID_PRIMITIVES = (str, int, float, bool, type(None), datetime)


def _get_anomaly(v: Any, path: str) -> dict[str, Any] | None:
    """Evaluates a single value and returns a serialized anomaly if invalid."""
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
    """
    Recursively scans and functionally rebuilds the input structure,
    replacing anomalies (NaN, Inf, Un-serializable) with DataAnomaly dicts.
    """
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
    """
    Base class for Zero-Trust Boundary objects.
    Enforces a 'Quarantine' stage (Stage 1) before standard Pydantic Validation (Stage 2).
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    @model_validator(mode="before")
    @classmethod
    def run_quarantine(cls, data: Any) -> Any:
        if isinstance(data, (dict, list, tuple)):
            # Assign the functionally rebuilt structure
            data = _scan_and_quarantine(data, "$")
        return data
