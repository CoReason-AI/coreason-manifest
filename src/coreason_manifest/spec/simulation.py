# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import Field

from .common_base import CoReasonBaseModel


class StepType(str, Enum):
    """Enumeration of step types in a simulation trace."""

    INTERACTION = "interaction"
    SYSTEM_EVENT = "system_event"
    TOOL_EXECUTION = "tool_execution"
    REASONING = "reasoning"
    ERROR = "error"


class ValidationLogic(str, Enum):
    """Enumeration of validation logic types for simulation scenarios."""

    EXACT_MATCH = "exact_match"
    FUZZY = "fuzzy"
    CODE_EVAL = "code_eval"
    LLM_JUDGE = "llm_judge"


class SimulationStep(CoReasonBaseModel):
    """The atomic unit of execution history."""

    step_id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    type: StepType
    node_id: str
    inputs: Dict[str, Any] = Field(default_factory=dict)
    thought: Optional[str] = None
    action: Optional[Dict[str, Any]] = None
    observation: Optional[Dict[str, Any]] = None
    snapshot: Dict[str, Any] = Field(default_factory=dict)


class SimulationTrace(CoReasonBaseModel):
    """The full recording of a session."""

    trace_id: UUID = Field(default_factory=uuid4)
    agent_id: str
    agent_version: str
    steps: List[SimulationStep] = Field(default_factory=list)
    outcome: Optional[Dict[str, Any]] = None
    score: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AdversaryProfile(CoReasonBaseModel):
    """Configuration for the Red Team agent."""

    name: str
    goal: str
    strategy_model: str
    attack_model: str
    persona: Optional[Dict[str, Any]] = None


class ChaosConfig(CoReasonBaseModel):
    """Configuration for infrastructure faults."""

    latency_ms: int = 0
    error_rate: float = 0.0
    token_throttle: bool = False


class SimulationScenario(CoReasonBaseModel):
    """The test case definition."""

    id: str
    description: str
    inputs: Dict[str, Any]
    expected_output: Optional[Dict[str, Any]] = None
    validation_logic: ValidationLogic


class SimulationRequest(CoReasonBaseModel):
    """The trigger payload sent to the runner."""

    scenario: SimulationScenario
    profile: Optional[AdversaryProfile] = None
    chaos_config: Optional[ChaosConfig] = None
