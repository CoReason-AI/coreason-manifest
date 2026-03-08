# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

from pydantic import Field

from coreason_manifest.core.base import CoreasonBaseModel


class PeftAdapterContract(CoreasonBaseModel):
    """Declarative contract for dynamically mounting a Parameter-Efficient Fine-Tuning (PEFT) adapter."""

    adapter_id: str = Field(description="Unique identifier for the requested LoRA adapter.")
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
        description="The low-rank intrinsic dimension (r) of the update matrices, "
        "used by the orchestrator to calculate VRAM cost.",
    )
    target_modules: list[str] = Field(
        min_length=1, description="The explicit list of attention head modules to inject (e.g., ['q_proj', 'v_proj'])."
    )
    eviction_ttl_seconds: int | None = Field(
        default=None,
        gt=0,
        description="The time-to-live before the inference engine forcefully evicts this adapter from the LRU cache.",
    )
