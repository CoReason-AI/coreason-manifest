# Prosperity-3.0
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from coreason_manifest.core.primitives.types import WasiCapability

from .base import Node


class WasmPayloadBase(BaseModel):
    """
    Base strict schema for Wasm execution payloads.
    Inherit from this instead of using opaque dictionaries.
    """
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)


type WasmExecutionPayload = WasmPayloadBase

class WasmExecutionNode(Node):
    """
    Zero-Trust WebAssembly execution node.
    Provides strict code isolation by executing tasks in a WASI-bound sandboxed Wasm environment.
    """

    type: Literal["wasm_execution"] = Field("wasm_execution", description="The type of the node.")
    wasm_module_hash: str | None = Field(
        None, description="Optional strict SHA-256 hash requirement for the Wasm binary."
    )
    payload_schema: WasmExecutionPayload | None = Field(
        None, description="The strictly typed payload defining inputs to the Wasm environment."
    )
    capabilities: list[WasiCapability] = Field(
        default_factory=list, description="Explicit WASI capabilities granted to this node."
    )
