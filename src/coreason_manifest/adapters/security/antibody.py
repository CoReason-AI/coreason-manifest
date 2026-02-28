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
    if not isinstance(v, (dict, list)) and not isinstance(v, VALID_PRIMITIVES):
        return DataAnomaly(
            code="CRSN-ANTIBODY-UNSERIALIZABLE",
            path=path,
            value_repr=str(type(v)),
            description="Object is not deterministically serializable.",
        ).model_dump()
    return None


def _scan_and_quarantine(data: Any, path: str) -> None:
    """
    Recursively scans the raw input structure and MUTATES it in-place
    to replace anomalies (NaN, Inf) or un-serializable types with
    DataAnomaly dictionaries.
    """
    if isinstance(data, dict):
        for k, v in list(data.items()):
            current_path = f"{path}.{k}" if path else k
            anomaly = _get_anomaly(v, current_path)
            if anomaly:
                data[k] = anomaly
            elif isinstance(v, (dict, list)):
                _scan_and_quarantine(v, current_path)

    elif isinstance(data, list):
        for i, v in enumerate(data):
            current_path = f"{path}[{i}]"
            anomaly = _get_anomaly(v, current_path)
            if anomaly:
                data[i] = anomaly
            elif isinstance(v, (dict, list)):
                _scan_and_quarantine(v, current_path)


class AntibodyBase(BaseModel):
    """
    Base class for Zero-Trust Boundary objects.
    Enforces a 'Quarantine' stage (Stage 1) before standard Pydantic Validation (Stage 2).
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    @model_validator(mode="before")
    @classmethod
    def run_quarantine(cls, data: Any) -> Any:
        """
        Stage 1: Quarantine.
        Scans for anomalies and MUTATES them into DataAnomaly objects
        before Pydantic attempts strict validation.
        """
        if isinstance(data, (dict, list)):
            # We must mutate the data in-place.
            # If data is a dict (likely for a Model), we scan it.
            _scan_and_quarantine(data, "$")

        return data
