# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import Field

from .common_base import CoReasonBaseModel


class StepType(StrEnum):
    """Enumeration of step types in a simulation trace."""

    INTERACTION = "interaction"
    SYSTEM_EVENT = "system_event"
    TOOL_EXECUTION = "tool_execution"
    REASONING = "reasoning"
    ERROR = "error"


class ValidationLogic(StrEnum):
    """Enumeration of validation logic types for simulation scenarios."""

    EXACT_MATCH = "exact_match"
    FUZZY = "fuzzy"
    CODE_EVAL = "code_eval"
    LLM_JUDGE = "llm_judge"


class SimulationStep(CoReasonBaseModel):
    """The atomic unit of execution history."""

    step_id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    type: StepType
    node_id: str
    inputs: dict[str, Any] = Field(default_factory=dict)
    thought: str | None = None
    action: dict[str, Any] | None = None
    observation: dict[str, Any] | None = None
    snapshot: dict[str, Any] = Field(default_factory=dict)


class SimulationTrace(CoReasonBaseModel):
    """The full recording of a session."""

    trace_id: UUID = Field(default_factory=uuid4)
    agent_id: str
    agent_version: str
    steps: list[SimulationStep] = Field(default_factory=list)
    outcome: dict[str, Any] | None = None
    score: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AdversaryProfile(CoReasonBaseModel):
    """Configuration for the Red Team agent."""

    name: str
    goal: str
    strategy_model: str
    attack_model: str
    persona: dict[str, Any] | None = None


class ChaosConfig(CoReasonBaseModel):
    """Configuration for infrastructure faults."""

    latency_ms: int = 0
    error_rate: float = 0.0
    token_throttle: bool = False


class SimulationScenario(CoReasonBaseModel):
    """The test case definition."""

    id: str
    description: str
    inputs: dict[str, Any]
    expected_output: dict[str, Any] | None = None
    validation_logic: ValidationLogic


class SimulationRequest(CoReasonBaseModel):
    """The trigger payload sent to the runner."""

    scenario: SimulationScenario
    profile: AdversaryProfile | None = None
    chaos_config: ChaosConfig | None = None
