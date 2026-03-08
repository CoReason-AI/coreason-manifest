# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

"""AGENT INSTRUCTION: This file maps Parameter-Efficient Fine-Tuning (PEFT) adapter schemas. This is a STRICTLY
KINETIC BOUNDARY. These schemas represent friction, hardware limits, and physical execution. This boundary
governs probabilistic tensor logic, VRAM geometries, and exogenous spatial actuation.
"""

from pydantic import Field

from coreason_manifest.core.base import CoreasonBaseModel


class PeftAdapterContract(CoreasonBaseModel):
    """Declarative PEFT Adapter Contract for dynamically mounting a hot-swappable tensor overlay."""

    adapter_id: str = Field(
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark for the requested LoRA adapter."
    )
    safetensors_hash: str = Field(
        pattern=r"^[a-f0-9]{64}$",
        description="The SHA-256 hash of the cold-storage adapter weights file ensuring supply-chain zero-trust.",
    )
    base_model_hash: str = Field(
        pattern=r"^[a-f0-9]{64}$",
        description="The SHA-256 hash of the exact foundational model this adapter was mathematically trained against.",
    )
    adapter_rank: int = Field(
        gt=0,
        description="The low-rank intrinsic Rank Dimensionality (r) of the update matrices, "
        "used by the orchestrator to calculate VRAM Geometry footprint.",
    )
    target_modules: list[str] = Field(
        min_length=1, description="The explicit list of attention head modules to inject (e.g., ['q_proj', 'v_proj'])."
    )
    eviction_ttl_seconds: int | None = Field(
        default=None,
        gt=0,
        description="The time-to-live before the inference engine forcefully evicts this Hot-Swappable Tensor Overlay "
        "to prevent Out-Of-Memory (OOM) routing crashes.",
    )
