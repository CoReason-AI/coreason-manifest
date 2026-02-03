# Agent Behavior Protocols

The `coreason_manifest` package defines the standard behavioral contracts that all Coreason Agents must implement. These protocols ensure interoperability between Agents, the Engine, and external testing tools.

They are defined in `src/coreason_manifest/definitions/interfaces.py` and are based on Python's `typing.Protocol` for structural subtyping.

## AgentInterface

The `AgentInterface` protocol defines the core responsibility of an Agent: to accept a request and use a response handler to emit events.

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
    async def assist(self, request: AgentRequest, response: ResponseHandler) -> None:
        """Process a request and use the response handler to emit events.

        Args:
            request: The strictly typed input envelope.
            response: The handler for emitting results.
        """
        ...
```

### Key Components

1.  **`manifest`**: A property that returns the agent's static configuration (`AgentDefinition`). This allows runtime inspection of the agent's capabilities, inputs, and outputs.
2.  **`assist`**: The primary entry point for execution.
    *   **Input**: Strictly typed `AgentRequest` envelope.
    *   **Output**: None (events are emitted via `response`).
    *   **Inversion of Control**: Instead of yielding events, the agent calls methods on the provided `ResponseHandler`.

## ResponseHandler

The `ResponseHandler` Protocol decouples the agent's logic from the event transport (e.g., HTTP, WebSocket, SSE).

### Definition

```python
class ResponseHandler(Protocol):
    async def emit(self, event: Union[CloudEvent[Any], GraphEvent]) -> None: ...

    async def thought(self, content: str, status: str = "IN_PROGRESS") -> None: ...

    async def markdown(self, content: str) -> None: ...

    async def data(self, data: Dict[str, Any], title: Optional[str] = None, view_hint: str = "JSON") -> None: ...

    async def error(self, message: str, details: Optional[Dict[str, Any]] = None, recoverable: bool = False) -> None: ...

    async def create_stream(self, title: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> StreamHandle:
        """Create a new stream and return its handle."""
        ...
```

## StreamHandle

The `StreamHandle` Protocol encapsulates the lifecycle of a stream (Open -> Emit -> Close). See [Stream Identity and Lifecycle](stream_lifecycle.md) for details.

```python
@runtime_checkable
class StreamHandle(Protocol):
    @property
    def stream_id(self) -> str: ...

    @property
    def is_active(self) -> bool: ...

    async def write(self, chunk: str) -> None: ...

    async def close(self) -> None: ...

    async def abort(self, reason: str) -> None: ...
```

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
from typing import Any
from coreason_manifest import AgentInterface, AgentRequest, ResponseHandler, AgentDefinition

class EchoAgent:
    """A simple agent that strictly implements AgentInterface."""

    def __init__(self, manifest: AgentDefinition):
        self._manifest = manifest

    @property
    def manifest(self) -> AgentDefinition:
        return self._manifest

    async def assist(self, request: AgentRequest, response: ResponseHandler) -> None:
        # Emit a "thinking" event
        await response.thought("Processing request...")

        # Create a stream for the output
        stream = await response.create_stream(title="Echo Response")

        try:
            # Simulate streaming chunks
            words = str(request.payload.get("query", "")).split()
            for word in words:
                await stream.write(word + " ")
                await asyncio.sleep(0.1)

            # Finalize the stream
            await stream.close()

        except Exception as e:
            await stream.abort(str(e))
            await response.error("Failed to stream response")

# Runtime Check
agent = EchoAgent(manifest=...)
assert isinstance(agent, AgentInterface)  # True
```
