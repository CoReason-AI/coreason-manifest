# Agent Behavior Protocols

The `coreason_manifest` package defines the standard behavioral contracts that all Coreason Agents must implement. These protocols ensure interoperability between Agents, the Engine, and external testing tools.

They are defined in `src/coreason_manifest/definitions/interfaces.py` and are based on Python's `typing.Protocol` for structural subtyping.

## AgentInterface

The `AgentInterface` protocol defines the core responsibility of an Agent: to accept a request and yield a stream of events.

### Definition

```python
@runtime_checkable
class AgentInterface(Protocol):
    """Protocol defining the standard interface for a Coreason Agent."""

    @property
    @abstractmethod
    def manifest(self) -> AgentDefinition:
        """Accessor for the static configuration/metadata of the agent."""
        ...

    @abstractmethod
    def assist(
        self, request: AgentRequest
    ) -> AsyncIterator[Union[CloudEvent[Any], GraphEvent]]:
        """Process a request and yield a stream of events.

        Returns:
            An async iterator yielding thoughts, data, artifacts, or final answers.
        """
        ...
```

### Key Components

1.  **`manifest`**: A property that returns the agent's static configuration (`AgentDefinition`). This allows runtime inspection of the agent's capabilities, inputs, and outputs.
2.  **`assist`**: The primary entry point for execution.
    *   **Input**: Strictly typed `AgentRequest` envelope.
    *   **Output**: An asynchronous stream (`AsyncIterator`) of events.
    *   **Event Types**: Supports both `CloudEvent[Any]` (modern) and `GraphEvent` (legacy/internal).

### Why `def` instead of `async def`?

In the Protocol definition, `assist` is defined as a synchronous function (`def`) that returns an `AsyncIterator`. This is a technical requirement to satisfy static type checkers (like Mypy) when using `AsyncGenerator` implementations.

**Implementers should use `async def`:**

```python
class MyAgent:
    @property
    def manifest(self) -> AgentDefinition:
        return self._manifest

    async def assist(self, request: AgentRequest) -> AsyncIterator[Union[CloudEvent[Any], GraphEvent]]:
        yield CloudEvent(...)
```

An `async def` function that yields is an `AsyncGenerator`, which is a subtype of `AsyncIterator`. This implementation correctly satisfies the protocol.

## LifecycleInterface

The `LifecycleInterface` protocol defines optional setup and teardown methods for agents that manage resources (e.g., database connections, model loaders).

### Definition

```python
@runtime_checkable
class LifecycleInterface(Protocol):
    def startup(self) -> None:
        """Initialize resources before serving traffic."""
        ...

    def shutdown(self) -> None:
        """Cleanup resources."""
        ...
```

## Usage Example

```python
import asyncio
from typing import AsyncIterator, Union, Any
from coreason_manifest import AgentInterface, AgentRequest, CloudEvent, GraphEvent, AgentDefinition

class EchoAgent:
    """A simple agent that strictly implements AgentInterface."""

    def __init__(self, manifest: AgentDefinition):
        self._manifest = manifest

    @property
    def manifest(self) -> AgentDefinition:
        return self._manifest

    async def assist(self, request: AgentRequest) -> AsyncIterator[Union[CloudEvent[Any], GraphEvent]]:
        # Emit a "thinking" event
        yield CloudEvent(
            type="ai.coreason.thought",
            source="agent:echo",
            data={"content": "Processing request..."}
        )

        # Emit the result
        yield CloudEvent(
            type="ai.coreason.output",
            source="agent:echo",
            data={"echo": request.payload}
        )

# Runtime Check
agent = EchoAgent(manifest=...)
assert isinstance(agent, AgentInterface)  # True
```
