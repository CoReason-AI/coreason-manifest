from datetime import datetime
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

    id: str = Field(..., description="Unique identifier for the operation/span.")
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
    """The full audit trail of an Agent's execution session."""

    model_config = ConfigDict(extra="ignore")

    trace_id: UUID
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


# --- Backward Compatibility ---
# Adapters or Aliases
AuditLog = ReasoningTrace
CognitiveStep = GenAIOperation
TokenUsage = GenAITokenUsage
