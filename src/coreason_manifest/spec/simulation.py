# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from datetime import datetime, UTC
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import Field

from .common_base import CoReasonBaseModel


class StepType(StrEnum):
    INTERACTION = "INTERACTION"
    SYSTEM_EVENT = "SYSTEM_EVENT"
    TOOL_EXECUTION = "TOOL_EXECUTION"
    REASONING = "REASONING"
    ERROR = "ERROR"


class ValidationLogic(StrEnum):
    EXACT_MATCH = "EXACT_MATCH"
    FUZZY = "FUZZY"
    CODE_EVAL = "CODE_EVAL"
    LLM_JUDGE = "LLM_JUDGE"


class SimulationStep(CoReasonBaseModel):
    """The atomic unit of execution history."""

    step_id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    type: StepType
    node_id: str
    inputs: dict[str, Any]
    thought: str | None = None
    action: dict[str, Any] | None = None
    observation: dict[str, Any] | None = None
    snapshot: dict[str, Any]


class SimulationTrace(CoReasonBaseModel):
    """The full recording of a session."""

    trace_id: UUID = Field(default_factory=uuid4)
    agent_id: str
    agent_version: str
    steps: list[SimulationStep] = Field(default_factory=list)
    outcome: dict[str, Any] | None = None
    score: float | None = Field(None, ge=0.0, le=1.0)
    metadata: dict[str, Any]


class AdversaryProfile(CoReasonBaseModel):
    """Configuration for the Red Team agent."""

    name: str
    goal: str
    strategy_model: str
    attack_model: str
    persona: dict[str, Any]


class ChaosConfig(CoReasonBaseModel):
    """Configuration for infrastructure faults."""

    latency_ms: int = 0
    error_rate: float = Field(0.0, ge=0.0, le=1.0)
    token_throttle: bool = False


class SimulationScenario(CoReasonBaseModel):
    """The test case definition."""

    id: str
    description: str
    inputs: dict[str, Any]
    expected_output: dict[str, Any] | None = None
    validation_logic: ValidationLogic


class SimulationRequest(CoReasonBaseModel):
    """The trigger payload."""

    scenario: SimulationScenario
    profile: AdversaryProfile | None = None
    chaos_config: ChaosConfig | None = None
