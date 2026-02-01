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
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from .message import ChatMessage


class GenAITokenUsage(BaseModel):
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


class GenAIOperation(BaseModel):
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


class ReasoningTrace(BaseModel):
    """The full audit trail of an Agent's execution session.

    Aligned with OpenTelemetry for trace identification.
    """

    model_config = ConfigDict(extra="ignore")

    trace_id: str = Field(..., description="Trace ID (OTel format).")
    agent_id: str
    session_id: Optional[str] = None

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


class AuditEventType(str, Enum):
    SYSTEM_CHANGE = "system_change"
    PREDICTION = "prediction"
    GUARDRAIL_TRIGGER = "guardrail_trigger"


class AuditLog(BaseModel):
    """Tamper-evident legal record.

    IDs aligned with OpenTelemetry:
    - audit_id: Unique record ID.
    - trace_id: OTel Trace ID.
    """

    audit_id: UUID = Field(..., description="Unique identifier.")
    trace_id: str = Field(..., description="Trace ID for OTel correlation.")
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
