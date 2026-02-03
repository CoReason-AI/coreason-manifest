# Agent Behavior Protocols

The `coreason_manifest` package defines the standard behavioral contracts that all Coreason Agents must implement. These protocols ensure interoperability between Agents, the Engine, and external testing tools.

They are defined in `src/coreason_manifest/definitions/interfaces.py` and are based on Python's `typing.Protocol` for structural subtyping.

## AgentInterface

The `AgentInterface` protocol defines the core responsibility of an Agent: to accept a request and use a provided handler to emit events.

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
    def assist(self, request: AgentRequest, response: ResponseHandler) -> Awaitable[None]:
        """Process a request and use the response handler to emit events.

        Args:
            request: The strictly typed input envelope.
            response: The handler for emitting thoughts, data, artifacts, or final answers.

        Returns:
            None (awaited).
        """
        ...
```

### Key Components

1.  **`manifest`**: A property that returns the agent's static configuration (`AgentDefinition`). This allows runtime inspection of the agent's capabilities, inputs, and outputs.
2.  **`assist`**: The primary entry point for execution.
    *   **Input**: Strictly typed `AgentRequest` envelope.
    *   **Output Mechanism**: Inversion of Control via the `ResponseHandler` argument.
    *   **Event Types**: Supports both `CloudEvent[Any]` (modern) and `GraphEvent` (legacy/internal).

For a detailed explanation of the `ResponseHandler` pattern, see [Response Handler Protocol](response_handler_protocol.md).

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
from typing import Awaitable
from coreason_manifest import AgentInterface, AgentRequest, ResponseHandler, AgentDefinition

class EchoAgent:
    """A simple agent that strictly implements AgentInterface."""

    def __init__(self, manifest: AgentDefinition):
        self._manifest = manifest

    @property
    def manifest(self) -> AgentDefinition:
        return self._manifest

    async def assist(self, request: AgentRequest, response: ResponseHandler) -> None:
        # Emit a "thinking" log (System)
        await response.log("INFO", "Processing request...")

        # Emit the result (User)
        await response.emit_text_block(f"Echo: {request.payload}")

# Runtime Check
agent = EchoAgent(manifest=...)
assert isinstance(agent, AgentInterface)  # True
```
