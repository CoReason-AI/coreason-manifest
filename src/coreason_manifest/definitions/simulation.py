# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class StepType(str, Enum):
    """Type of the simulation step."""

    INTERACTION = "interaction"  # Normal User/Agent turn
    SYSTEM_EVENT = "system_event"  # Chaos injection, error, or info


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
    type: StepType = Field(default=StepType.INTERACTION, description="Type of the step.")
    node_id: str = Field(..., description="The graph node executed.")
    inputs: Dict[str, Any] = Field(..., description="Snapshot of entry state.")
    thought: Optional[str] = Field(None, description="The Chain-of-Thought reasoning.")
    action: Optional[Dict[str, Any]] = Field(None, description="Tool calls or API requests.")
    observation: Optional[Dict[str, Any]] = Field(None, description="Tool outputs.")
    snapshot: Dict[str, Any] = Field(
        default_factory=dict, description="Full copy of the graph state at the completion of this step."
    )


class SimulationMetrics(BaseModel):
    """Metrics gathered during simulation."""

    turn_count: int
    total_tokens: Optional[int] = None
    cost_usd: Optional[float] = None
    duration_ms: Optional[float] = None


class SimulationTrace(BaseModel):
    """Trace of a simulation execution."""

    trace_id: UUID = Field(..., description="Unique trace identifier.")
    agent_version: str = Field(..., description="Agent SemVer version.")
    steps: List[SimulationStep] = Field(..., description="List of execution steps.")
    outcome: Dict[str, Any] = Field(..., description="Final result.")
    metrics: SimulationMetrics = Field(..., description="Execution metrics (e.g., token usage, cost).")
