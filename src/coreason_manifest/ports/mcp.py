"""
Native Model Context Protocol (MCP) Integration for the CoReason Manifest.

This module defines a production-ready FastMCP server that natively exposes our
Epistemic Ledger, our strict Neuro-Symbolic Data Contracts, and dynamic prompts.
"""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal, cast  # noqa: F401
from uuid import uuid4

from mcp.server.fastmcp import Context, FastMCP
from pydantic import Field, ValidationError, model_validator

from coreason_manifest.compute.epistemic import ClinicalProposition
from coreason_manifest.core.common.base import CoreasonModel
from coreason_manifest.core.scivis.scivis_provenance import ActorIdentity
from coreason_manifest.state.events import EpistemicAnchor, EpistemicEvent, EventType
from coreason_manifest.state.ledger import EpistemicLedger
from coreason_manifest.telemetry.telemetry_schemas import AgentSignature, HardwareFingerprint


def create_mcp_server(ledger: EpistemicLedger) -> FastMCP:
    """
    Creates and configures a FastMCP server connected to the given EpistemicLedger.

    The server exposes:
      - Resources: Read-only access to ledger events via epistemic:// URIs.
      - Tools: Neuro-symbolic data appending (e.g., ClinicalProposition).
      - Prompts: Dynamic context injection.

    Args:
        ledger: The central CRDT EpistemicLedger instance.

    Returns:
        The configured FastMCP server instance.
    """
    mcp = FastMCP("CoReason Manifest MCP Server")

    @mcp.resource("epistemic://ledger/events/{event_id}")
    async def get_event(event_id: str) -> str:
        """
        Fetch a specific EpistemicEvent from the ledger and return its canonical JSON representation.
        """
        event = ledger.get_event_by_id(event_id)
        if event is not None:
            return event.model_dump_json()
        raise ValueError(f"Event {event_id} not found in ledger")

    @mcp.tool()
    async def append_clinical_proposition(proposition: ClinicalProposition, ctx: Context[Any, Any, Any]) -> str:
        """
        Intercept a call to append a ClinicalProposition, run strict Pydantic validation natively,
        wrap it in an EpistemicEvent, and append it to the Ledger.
        """
        if ctx.request_context is None or ctx.request_context.meta is None:
            raise ValueError("SecurityException: Context metadata is missing.")

        from pydantic import BaseModel, ConfigDict

        class SecurityMetadata(BaseModel):
            model_config = ConfigDict(extra="ignore")
            agent_signature: dict[str, Any] = Field(alias="x-agent-signature")
            hardware_fingerprint: dict[str, Any] = Field(alias="x-hardware-fingerprint")

        try:
            sec_meta = SecurityMetadata.model_validate(ctx.request_context.meta, from_attributes=True)
            agent_sig_raw = sec_meta.agent_signature
            hw_fingerprint_raw = sec_meta.hardware_fingerprint
        except ValidationError as e:
            raise ValueError(
                f"SecurityException: Security headers are missing or invalid in Context metadata. Details: {e}"
            ) from e

        try:
            agent_sig = AgentSignature.model_validate(agent_sig_raw)
            hardware_fingerprint = HardwareFingerprint.model_validate(hw_fingerprint_raw)
        except ValidationError as e:
            raise ValueError(f"SecurityException: Validation failed for Zero-Trust credentials: {e}") from e

        event = EpistemicEvent(
            event_id=str(uuid4()),
            timestamp=datetime.now(UTC),
            context_envelope={
                "agent_signature": agent_sig.model_dump(),
                "hardware_cluster": hardware_fingerprint.model_dump(),
                "prompt_version": "1.0",
            },
            event_type=EventType.SEMANTIC_EXTRACTED,
            payload=proposition.model_dump(mode="json"),
            epistemic_anchor=EpistemicAnchor(),
        )
        ledger.append(event)
        return f"Successfully appended event {event.event_id}"

    @mcp.prompt("auditor_recovery_prompt")
    async def auditor_recovery_prompt(suspense_reason: str, hardware_profile: str) -> str:
        """
        Return a structured system prompt directing a Heavy Reasoner on how to verify
        a blurry bounding box or failing mathematical token based on the failure context.
        """
        return (
            f"You are a Heavy Reasoner operating on {hardware_profile}.\n"
            f"The previous extraction failed due to: {suspense_reason}.\n"
            "Please verify the blurry bounding box or failing mathematical token carefully."
        )

    return mcp


class MCPToolName(StrEnum):
    """Names of the Universal Canvas API tools."""

    CANVAS_ADD_ELEMENT = "CANVAS_ADD_ELEMENT"
    CANVAS_UPDATE_ELEMENT = "CANVAS_UPDATE_ELEMENT"
    CANVAS_REMOVE_ELEMENT = "CANVAS_REMOVE_ELEMENT"
    CANVAS_GROUP_ELEMENTS = "CANVAS_GROUP_ELEMENTS"
    CANVAS_ADD_CONNECTION = "CANVAS_ADD_CONNECTION"
    CANVAS_APPLY_STYLE = "CANVAS_APPLY_STYLE"
    CANVAS_IMPORT_ARTIFACT = "CANVAS_IMPORT_ARTIFACT"
    CANVAS_ADD_MATH_NODE = "CANVAS_ADD_MATH_NODE"
    CANVAS_UPDATE_MATH_NODE = "CANVAS_UPDATE_MATH_NODE"


class MCPOperation(CoreasonModel):
    """An atomic design action executed on a headless canvas."""

    operation_id: str = Field(..., description="Unique ID for tracing and logging this specific action.")
    tool_name: MCPToolName
    target_element_id: str | None = Field(
        default=None, description="The ID of the specific canvas object being mutated. Crucial for targeted edits."
    )
    parameters: dict[str, Any] = Field(
        default_factory=dict, description="The kwargs payload for the tool (e.g., x, y, width, fill_color)."
    )
    actor: ActorIdentity | None = Field(
        default=None, description="Cryptographically tags the specific agent/human issuing this canvas command."
    )

    @model_validator(mode="after")
    def enforce_strict_provenance(self) -> "MCPOperation":
        if (
            self.tool_name in {MCPToolName.CANVAS_ADD_MATH_NODE, MCPToolName.CANVAS_UPDATE_MATH_NODE}
            and self.actor is None
        ):
            raise ValueError("Regulatory SciVis operations require a cryptographically verifiable ActorIdentity.")
        return self

    @model_validator(mode="after")
    def validate_target_element_id(self) -> "MCPOperation":
        requires_id = {
            MCPToolName.CANVAS_UPDATE_ELEMENT,
            MCPToolName.CANVAS_REMOVE_ELEMENT,
            MCPToolName.CANVAS_UPDATE_MATH_NODE,
        }
        if self.tool_name in requires_id and self.target_element_id is None:
            raise ValueError(f"target_element_id cannot be None when tool_name is {self.tool_name}")
        return self


class MCPOperationSequence(CoreasonModel):
    """An ordered, transactional sequence of atomic design actions."""

    sequence_id: str
    operations: list[MCPOperation]
    transaction_mode: Literal["atomic_commit", "sequential_best_effort"] = Field(
        default="atomic_commit",
        description="If atomic, the downstream engine must snapshot the canvas and rollback if any operation fails.",
    )
    expected_canvas_state_hash: str | None = Field(
        default=None,
        description="Ensures the sequence is applied to the correct diagram version to prevent races.",
    )
