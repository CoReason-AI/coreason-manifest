import math
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


def _scan_and_quarantine(data: Any, path: str) -> None:
    """
    Recursively scans the raw input structure and MUTATES it in-place
    to replace anomalies (NaN, Inf) with DataAnomaly objects.
    """
    if isinstance(data, dict):
        for k, v in data.items():
            current_path = f"{path}.{k}" if path else k

            # Check value
            if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                data[k] = DataAnomaly(
                    code="CRSN-ANTIBODY-FLOAT",
                    path=current_path,
                    value_repr=str(v),
                    description="Floating point value is not finite (NaN/Inf).",
                )
            elif isinstance(v, (dict, list)):
                _scan_and_quarantine(v, current_path)

    elif isinstance(data, list):
        for i, v in enumerate(data):
            current_path = f"{path}[{i}]"

            # Check item
            if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                data[i] = DataAnomaly(
                    code="CRSN-ANTIBODY-FLOAT",
                    path=current_path,
                    value_repr=str(v),
                    description="Floating point value is not finite (NaN/Inf).",
                )
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
