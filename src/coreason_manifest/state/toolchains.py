"""
Toolchain definitions for dynamic Tool-RAG and JIT Synthesis architectures.

This module provides the schema contracts required to support the 2026
Dynamic Tool-RAG architecture, ensuring precise management of the orchestrator's
dynamic discovery, semantic compression, and on-the-fly synthesis capabilities.
"""

from typing import Literal

from pydantic import BaseModel, Field


class CognitiveLoadTrimmer(BaseModel):
    """
    Defines the orchestrator's strategy for managing the LLM context window.

    In a dynamic Tool-RAG architecture, too many tool descriptions can overwhelm
    the model's effective context. This trimmer prevents context collapse.
    """

    max_tool_tokens: int = Field(
        ..., description="The absolute maximum number of tokens allowed for tool descriptions in the prompt."
    )

    auto_provision_subagent: bool = Field(
        ...,
        description="If True, orchestrator spawns a sub-agent when max_tool_tokens is exceeded rather than truncating.",
    )

    context_compression_ratio: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Threshold (0.0 to 1.0) indicating when semantic compression of tool descriptions triggers.",
    )


class JITToolSynthesisConfig(BaseModel):
    """
    Declares the algorithmic process for generating a net-new tool on the fly.

    If the semantic search catalog returns no matches, this configuration defines
    how a fallback generation and verification process occurs.
    """

    generation_model_uri: str = Field(..., description="The identifier of the model tasked with writing the tool code.")

    wasm_sandbox_profile: Literal["strict", "network-enabled", "fs-read-only"] = Field(
        ..., description="The required security boundary to safely test the generated tool."
    )

    verification_assertion: str = Field(
        ...,
        description="Natural language or code-based assertion the generated tool must pass before being registered.",
    )

    max_synthesis_time_ms: int = Field(
        ..., description="Timeout (in milliseconds) for the generation and testing loop."
    )


class SemanticToolchain(BaseModel):
    """
    Represents a DAG of micro-tools linked by vector similarity rather than hardcoded edges.

    Allows tools to be dynamically assembled and chained during an orchestrator run.
    """

    macro_intent_hash: str = Field(..., description="The hash of the high-level goal this toolchain serves.")

    discovered_tool_uris: list[str] = Field(
        ..., description="URIs pointing to tools pulled from an MCP registry or local vector database."
    )

    similarity_threshold: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Minimum cosine similarity score (0.0 to 1.0) required for a tool to be included in this chain.",
    )

    load_strategy: Literal["lazy_eval", "eager_mount", "ephemeral"] = Field(
        ..., description="How the runtime should provision these tools."
    )

    jit_synthesis_fallback: JITToolSynthesisConfig | None = Field(
        default=None,
        description="Fallback mechanism for JIT synthesis if semantic search fails to yield sufficient tools.",
    )
