from datetime import datetime
from enum import Enum
from typing import Any, Dict, List
from uuid import UUID

from pydantic import BaseModel, Field


class ValidationLogic(str, Enum):
    """Logic used to validate the scenario outcome."""

    EXACT_MATCH = "exact_match"
    FUZZY = "fuzzy"
    CODE_EVAL = "code_eval"


class SimulationScenario(BaseModel):
    """Definition of a simulation scenario."""

    id: str = Field(..., description="Unique identifier for the scenario.")
    name: str = Field(..., description="Name of the scenario.")
    objective: str = Field(..., description="The prompt/task instructions.")
    difficulty: int = Field(..., description="Difficulty level (1-3, aligning with GAIA levels).", ge=1, le=3)
    expected_outcome: Any = Field(..., description="The ground truth for validation.")
    validation_logic: ValidationLogic = Field(..., description="Logic used to validate the outcome.")


class SimulationStep(BaseModel):
    """The atomic unit of execution in a simulation."""

    step_id: UUID = Field(..., description="Atomic unit of execution ID.")
    timestamp: datetime = Field(..., description="Execution timestamp.")
    node_id: str = Field(..., description="The graph node executed.")
    inputs: Dict[str, Any] = Field(..., description="Snapshot of entry state.")
    thought: str = Field(..., description="The Chain-of-Thought reasoning.")
    action: Dict[str, Any] = Field(..., description="Tool calls or API requests.")
    observation: Dict[str, Any] = Field(..., description="Tool outputs.")


class SimulationTrace(BaseModel):
    """Trace of a simulation execution."""

    trace_id: UUID = Field(..., description="Unique trace identifier.")
    agent_version: str = Field(..., description="Agent SemVer version.")
    steps: List[SimulationStep] = Field(..., description="List of execution steps.")
    outcome: Dict[str, Any] = Field(..., description="Final result.")
    metrics: Dict[str, Any] = Field(..., description="Execution metrics (e.g., token usage, cost).")
