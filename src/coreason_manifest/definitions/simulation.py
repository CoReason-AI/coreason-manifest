from pydantic import BaseModel

class SimulationScenario(BaseModel):
    """Definition of a simulation scenario."""
    pass

class SimulationTrace(BaseModel):
    """Trace of a simulation execution."""
    pass

class SimulationTurn(BaseModel):
    """A single turn in a simulation."""
    pass
