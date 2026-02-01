# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest


from typing import Optional

from pydantic import BaseModel, Field

from coreason_manifest.definitions.agent import Persona
from coreason_manifest.definitions.simulation import SimulationScenario


class AdversaryProfile(BaseModel):
    name: str
    goal: str
    strategy_model: str  # e.g., "claude-3-opus"
    attack_model: str  # e.g., "llama-3-uncensored"
    persona: Optional[Persona] = Field(None, description="The full persona definition (name, description, directives).")
    # Potential future field: 'system_prompt_override'


class ChaosConfig(BaseModel):
    latency_ms: int = Field(default=0, ge=0)
    error_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    noise_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    token_throttle: bool = False
    exception_type: str = "RuntimeError"


class SimulationRequest(BaseModel):
    """
    Standard payload for triggering a simulation.
    This would replace the local 'SimulationRequest' in the Simulator.
    """

    scenario: SimulationScenario
    profile: AdversaryProfile
    chaos_config: ChaosConfig = Field(default_factory=ChaosConfig)
