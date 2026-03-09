"""
AGENT INSTRUCTION: This module defines the Hollow Data Plane for N-Dimensional tensors.
It strictly enforces topological and cryptographic boundaries at compile-time.
"""

import math
from enum import StrEnum

from pydantic import Field, model_validator

from coreason_manifest.core.base import CoreasonBaseModel


class TensorDType(StrEnum):
    """Mathematical data types for tensor payloads."""

    FLOAT32 = "float32"
    FLOAT64 = "float64"
    INT8 = "int8"
    UINT8 = "uint8"
    INT32 = "int32"
    INT64 = "int64"

    @property
    def bytes_per_element(self) -> int:
        """Returns the byte footprint per element."""
        mapping = {"float32": 4, "float64": 8, "int8": 1, "uint8": 1, "int32": 4, "int64": 8}
        return mapping[self.value]


class NDimensionalTensorManifest(CoreasonBaseModel):
    """
    Cryptographic shadow of an N-Dimensional spatial or mathematical array.
    Used for routing multi-dimensional compute without passing raw bytes.
    """

    dtype: TensorDType = Field(..., description="Data type of the tensor elements.")
    shape: tuple[int, ...] = Field(..., description="N-Dimensional shape tuple.")
    memory_footprint_bytes: int = Field(..., description="Exact byte size of the uncompressed tensor.")
    merkle_root: str = Field(
        ..., pattern=r"^[a-fA-F0-9]{64}$", description="SHA-256 Merkle root of the payload chunks."
    )
    storage_uri: str = Field(..., description="Strict URI pointer to the physical bytes.")

    @model_validator(mode="after")
    def _enforce_physics_engine(self) -> "NDimensionalTensorManifest":
        """Mathematically prove the topology matches the declared memory footprint."""
        if len(self.shape) < 1:
            raise ValueError("Tensor shape must have at least 1 dimension.")

        for dim in self.shape:
            if dim <= 0:
                raise ValueError(f"Tensor dimensions must be strictly positive integers. Got: {self.shape}")

        # Ensure we can get the bytes_per_element whether it's currently evaluated as the Enum or as its string value
        bytes_per_element = self.dtype.bytes_per_element if isinstance(self.dtype, TensorDType) else TensorDType(self.dtype).bytes_per_element
        calculated_bytes = math.prod(self.shape) * bytes_per_element
        if calculated_bytes != self.memory_footprint_bytes:
            raise ValueError(
                f"Topological mismatch: Shape {self.shape} of {self.dtype.value} "
                f"requires {calculated_bytes} bytes, but manifest declares {self.memory_footprint_bytes} bytes."
            )
        return self
