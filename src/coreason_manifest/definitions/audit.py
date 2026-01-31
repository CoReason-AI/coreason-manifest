from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from .message import Message, ToolCall

class TokenUsage(BaseModel):
    """Token consumption stats."""
    model_config = ConfigDict(extra="ignore")

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    details: Dict[str, Any] = Field(default_factory=dict)

class CognitiveStep(BaseModel):
    """An atomic step in the reasoning process (e.g., one LLM call)."""
    model_config = ConfigDict(extra="ignore")

    step_id: str
    timestamp: datetime = Field(default_factory=datetime.now)

    # Input context (The prompt sent to the LLM)
    input_messages: List[Message]

    # The decision made (The LLM's response)
    output_message: Message

    # Execution details
    tool_calls: List[ToolCall] = Field(default_factory=list)
    token_usage: Optional[TokenUsage] = None
    latency_ms: float = 0.0

    # Metadata (e.g., model used, temperature, provider)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ReasoningTrace(BaseModel):
    """The full audit trail of an Agent's execution session."""
    model_config = ConfigDict(extra="ignore")

    trace_id: UUID
    agent_id: str
    session_id: Optional[str] = None

    start_time: datetime
    end_time: Optional[datetime] = None

    # The chain of thought (Ordered list of steps)
    steps: List[CognitiveStep] = Field(default_factory=list)

    # Final outcome
    status: str = "pending"  # options: success, failure, pending
    final_result: Optional[str] = None
    error: Optional[str] = None

    # Aggregated stats
    total_tokens: TokenUsage = Field(default_factory=TokenUsage)
    total_cost: float = 0.0

# --- Backward Compatibility ---
# This ensures that existing code importing AuditLog still works,
# but it now possesses the full structure of ReasoningTrace.
AuditLog = ReasoningTrace
