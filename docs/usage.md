# Usage Guide

This guide describes how to use the `coreason-manifest` package to work with CoReason schemas.

## Using Schemas

The package provides strict Pydantic models for Agents, Recipes, and Simulations.

### Importing Definitions

```python
from coreason_manifest.definitions import (
    AgentManifest,
    SimulationTrace,
    SimulationScenario,
    TopologyGraph
)
from coreason_manifest.recipes import RecipeManifest
```

### Validating Data

You can use the models to validate data structures directly.

```python
try:
    trace = SimulationTrace(
        scenario_id="12345678-1234-5678-1234-567812345678",
        agent_id="agent-007",
        agent_version="1.0.0",
        history=[]
    )
    print("Trace is valid!")
except ValidationError as e:
    print(f"Validation failed: {e}")
```

### Extending Schemas

All shared definitions inherit from `CoReasonBaseModel`, which provides utility methods like canonical hashing.

```python
from coreason_manifest.definitions.base import CoReasonBaseModel

class MyCustomEvent(CoReasonBaseModel):
    event_type: str
    payload: dict

event = MyCustomEvent(event_type="test", payload={"foo": "bar"})
print(event.canonical_hash())
```
