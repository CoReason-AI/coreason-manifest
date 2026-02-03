# Response Handler Protocol & Inversion of Control

To decouple the Agent's core logic from the infrastructure that serves it (HTTP, WebSocket, CLI), Coreason adopts an **Inversion of Control (IoC)** pattern for event emission.

Instead of an agent *returning* a generator of events, the agent is *passed* a `ResponseHandler` sink. The agent invokes methods on this sink to emit thoughts, data, artifacts, and system telemetry.

## The Architecture

### 1. The `EventSink` Primitive

At the base is the `EventSink` protocol, designed for **internal side-effects** that are not necessarily meant for the user (e.g., telemetry, audit logs).

```python
class EventSink(Protocol):
    """Protocol for emitting internal side-effects."""

    async def emit(self, event: Union[CloudEvent[Any], GraphEvent]) -> None:
        """Ingest any strictly typed event."""
        ...

    async def log(self, level: str, message: str, metadata: Optional[Dict] = None) -> None:
        """Emit a standard log event (System/Debug)."""
        ...

    async def audit(self, actor: str, action: str, resource: str, success: bool) -> None:
        """Emit an immutable Audit Log entry."""
        ...
```

### 2. The `ResponseHandler` Interface

The `ResponseHandler` inherits from `EventSink` and adds methods specific to **user-facing communication**.

```python
class ResponseHandler(EventSink, Protocol):
    """Protocol for handling user-facing communication and system events."""

    async def emit_text_block(self, text: str) -> None:
        """Emit a text block to the user UI.

        This is distinct from `log`, which goes to Datadog/Splunk.
        """
        ...
```

### 3. The New `AgentInterface`

The `assist` method now accepts a `ResponseHandler` and returns `None` (awaited).

```python
@runtime_checkable
class AgentInterface(Protocol):
    @abstractmethod
    async def assist(self, request: AgentRequest, response: ResponseHandler) -> None:
        """Process a request and use the response handler to emit events."""
        ...
```

## Benefits of Inversion of Control

1.  **Unified Side-Effects**: The agent can emit debug logs (`response.log(...)`) and user text (`response.emit_text_block(...)`) using the same injected dependency.
2.  **Infrastructure Decoupling**: The agent doesn't know if it's connected to a FastAPI endpoint, a CLI, or a test harness. The `ResponseHandler` implementation handles the transport (e.g., SSE, printing to stdout).
3.  **Simplified Async Flow**: Removing `AsyncIterator` return types simplifies exception handling and middleware wrapping.

## Usage Example

```python
class MyAgent:
    @property
    def manifest(self) -> AgentDefinition:
        return self._manifest

    async def assist(self, request: AgentRequest, response: ResponseHandler) -> None:
        # 1. System Log (Not visible to user)
        await response.log("INFO", "Starting analysis", {"user": request.user_id})

        # 2. Audit Log (Legal record)
        await response.audit(actor="agent", action="read_file", resource="doc.txt", success=True)

        # 3. User Response (Visible in Chat)
        await response.emit_text_block("I have analyzed your document.")
```
