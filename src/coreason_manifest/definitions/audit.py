# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import hashlib
import json
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import ConfigDict, Field, model_validator

from coreason_manifest.definitions.base import CoReasonBaseModel

from .message import ChatMessage


class GenAITokenUsage(CoReasonBaseModel):
    """Token consumption stats aligned with OTel conventions."""

    model_config = ConfigDict(extra="ignore")

    input: int = Field(0, description="Number of input tokens (prompt).")
    output: int = Field(0, description="Number of output tokens (completion).")
    total: int = Field(0, description="Total number of tokens used.")

    # Backward compatibility fields (mapped to new fields in logic if needed, but kept for schema)
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    details: Dict[str, Any] = Field(default_factory=dict)

    def __add__(self, other: "GenAITokenUsage") -> "GenAITokenUsage":
        """Add two TokenUsage objects."""
        new_details = self.details.copy()
        new_details.update(other.details)
        return GenAITokenUsage(
            input=self.input + other.input,
            output=self.output + other.output,
            total=self.total + other.total,
            prompt_tokens=self.prompt_tokens + other.prompt_tokens,
            completion_tokens=self.completion_tokens + other.completion_tokens,
            total_tokens=self.total_tokens + other.total_tokens,
            details=new_details,
        )

    def __iadd__(self, other: "GenAITokenUsage") -> "GenAITokenUsage":
        """In-place add two TokenUsage objects."""
        self.input += other.input
        self.output += other.output
        self.total += other.total
        self.prompt_tokens += other.prompt_tokens
        self.completion_tokens += other.completion_tokens
        self.total_tokens += other.total_tokens
        self.details.update(other.details)
        return self


class GenAIOperation(CoReasonBaseModel):
    """An atomic operation in the reasoning process (e.g., one LLM call), aligning with OTel Spans."""

    model_config = ConfigDict(extra="ignore")

    span_id: str = Field(..., description="Unique identifier for the operation/span.")
    trace_id: str = Field(..., description="Trace ID this operation belongs to.")
    parent_id: Optional[str] = Field(None, description="Parent span ID.")

    operation_name: str = Field(..., description="Name of the operation (e.g., chat, embedding).")
    provider: str = Field(..., description="GenAI provider (e.g., openai, anthropic).")
    model: str = Field(..., description="Model name used.")

    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    duration_ms: float = 0.0

    # Context
    input_messages: List[ChatMessage] = Field(default_factory=list)
    output_messages: List[ChatMessage] = Field(default_factory=list)

    # Metrics
    token_usage: Optional[GenAITokenUsage] = None

    # Metadata
    status: str = "pending"  # success, error
    error_type: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def thought(cls, content: str, **kwargs: Any) -> "GenAIOperation":
        """Factory method to create a simplified thought/reasoning step."""
        defaults = {
            "span_id": str(uuid.uuid4()),
            "trace_id": str(uuid.uuid4()),
            "operation_name": "thought",
            "provider": "internal",
            "model": "internal",
        }
        defaults.update(kwargs)
        # Ensure output_messages is not duplicated if passed in kwargs
        defaults.pop("output_messages", None)
        return cls(
            **defaults,
            output_messages=[ChatMessage.assistant(content)],
        )


class ReasoningTrace(CoReasonBaseModel):
    """The full audit trail of an Agent's execution session.

    Aligned with OpenTelemetry for trace identification.
    """

    model_config = ConfigDict(extra="ignore")

    trace_id: str = Field(..., description="Trace ID (OTel format).")
    agent_id: str
    session_id: Optional[str] = None

    # Request Lineage
    request_id: UUID = Field(..., description="The specific request ID that generated this trace.")
    root_request_id: Optional[UUID] = Field(default=None, description="The root ID of the conversation tree.")
    parent_request_id: Optional[UUID] = Field(default=None, description="The parent ID that triggered this trace.")

    start_time: datetime
    end_time: Optional[datetime] = None

    # The chain of thought (Ordered list of operations)
    steps: List[GenAIOperation] = Field(default_factory=list)

    # Final outcome
    status: str = "pending"  # options: success, failure, pending
    final_result: Optional[str] = None
    error: Optional[str] = None

    # Aggregated stats
    total_tokens: GenAITokenUsage = Field(default_factory=GenAITokenUsage)
    total_cost: float = 0.0

    # Flexible metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_lineage(self) -> "ReasoningTrace":
        """Enforce strict lineage: if Root is None, handle based on Parent."""
        if self.root_request_id is None:
            if self.parent_request_id is None:
                self.root_request_id = self.request_id
            else:
                raise ValueError("Root ID missing while Parent ID is present.")
        return self


class AuditEventType(str, Enum):
    SYSTEM_CHANGE = "system_change"
    PREDICTION = "prediction"
    GUARDRAIL_TRIGGER = "guardrail_trigger"


class AuditLog(CoReasonBaseModel):
    """Tamper-evident legal record.

    IDs aligned with OpenTelemetry:
    - audit_id: Unique record ID.
    - trace_id: OTel Trace ID.
    """

    audit_id: UUID = Field(..., description="Unique identifier.")
    trace_id: str = Field(..., description="Trace ID for OTel correlation.")

    # Request Lineage
    request_id: UUID = Field(..., description="The request ID associated with this audit entry.")
    root_request_id: UUID = Field(..., description="The root request ID of the workflow.")

    timestamp: datetime = Field(..., description="ISO8601 timestamp.")
    actor: str = Field(..., description="User ID or Agent Component ID.")
    event_type: AuditEventType = Field(..., description="Type of event.")
    safety_metadata: Dict[str, Any] = Field(..., description="Safety metadata (e.g., PII detected).")
    previous_hash: str = Field(..., description="Hash of the previous log entry.")
    integrity_hash: str = Field(..., description="SHA256 hash of this record + previous_hash.")

    def compute_hash(self) -> str:
        """Computes the integrity hash of the record."""
        # Use model_dump to get a dict, but exclude integrity_hash as it is the target
        data = self.model_dump(exclude={"integrity_hash"}, mode="json")
        # Ensure deterministic serialization
        json_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(json_str.encode("utf-8")).hexdigest()


# --- Backward Compatibility ---
# Adapters or Aliases
CognitiveStep = GenAIOperation
TokenUsage = GenAITokenUsage
