from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import Field

from .base import CoReasonBaseModel


class SimulationScenario(CoReasonBaseModel):
    id: UUID
    objective: str
    persona: str
    max_turns: int = 10


class SimulationTurn(CoReasonBaseModel):
    user_input: str
    agent_response: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SimulationTrace(CoReasonBaseModel):
    scenario_id: UUID
    agent_id: str
    agent_version: str
    history: List[SimulationTurn]
    passed: Optional[bool] = None
    score: Optional[float] = None
