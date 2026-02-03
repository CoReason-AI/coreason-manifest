from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class InterfaceDefinition(BaseModel):
    """Defines the input/output contract."""

    model_config = ConfigDict(extra="forbid")

    inputs: Dict[str, Any] = Field(default_factory=dict, description="JSON Schema definitions for arguments.")
    outputs: Dict[str, Any] = Field(default_factory=dict, description="JSON Schema definitions for return values.")


class StateDefinition(BaseModel):
    """Defines the conversation memory/context structure."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    schema_: Dict[str, Any] = Field(
        default_factory=dict, alias="schema", description="The structure of the conversation memory/context."
    )
    backend: Optional[str] = Field(None, description="Backend storage type (e.g., 'redis', 'memory').")


class PolicyDefinition(BaseModel):
    """Defines execution policy and governance rules."""

    model_config = ConfigDict(extra="forbid")

    max_steps: Optional[int] = Field(None, description="Execution limit on number of steps.")
    max_retries: int = Field(3, description="Maximum number of retries.")
    timeout: Optional[int] = Field(None, description="Timeout in seconds.")
    human_in_the_loop: bool = Field(False, description="Whether to require human approval.")
