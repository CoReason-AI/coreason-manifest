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


class AnomalyDetectedError(ValueError):
    """
    Raised when the Antibody layer intercepts dangerous data.
    Carries the payload of detected anomalies for telemetry.
    """

    def __init__(self, anomalies: list[DataAnomaly]):
        self.anomalies = anomalies
        super().__init__(f"Antibody intercepted {len(anomalies)} data anomalies.")


def _scan_recursive(data: Any, path: str, anomalies: list[DataAnomaly]) -> None:
    """
    Recursively scans the raw input structure for anomalies.
    """
    if isinstance(data, dict):
        for k, v in data.items():
            _scan_recursive(v, f"{path}.{k}" if path else k, anomalies)
    elif isinstance(data, list):
        for i, v in enumerate(data):
            _scan_recursive(v, f"{path}[{i}]", anomalies)
    elif isinstance(data, float) and (math.isnan(data) or math.isinf(data)):
        anomalies.append(
            DataAnomaly(
                code="CRSN-ANTIBODY-FLOAT",
                path=path,
                value_repr=str(data),
                description="Floating point value is not finite (NaN/Inf).",
            )
        )
    # Additional checks for un-serializable objects could go here
    # e.g. checking for complex numbers, or arbitrary objects if strict JSON is required.


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
        Scans for anomalies before Pydantic attempts strict validation.
        """
        if isinstance(data, (dict, list)):
            anomalies: list[DataAnomaly] = []
            _scan_recursive(data, "$", anomalies)

            if anomalies:
                raise AnomalyDetectedError(anomalies)

        return data
