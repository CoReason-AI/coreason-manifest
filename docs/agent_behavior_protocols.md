# Agent Behavior Protocols

The `coreason_manifest` package defines the standard behavioral contracts that all Coreason Agents must implement. These protocols ensure interoperability between Agents, the Engine, and external testing tools.

They are defined in `src/coreason_manifest/definitions/interfaces.py` and are based on Python's `typing.Protocol` for structural subtyping.

**Note:** The detailed Runtime Contract is now documented in [Runtime Contract](runtime_contract.md).

## IAgentRuntime

The `IAgentRuntime` protocol defines the core responsibility of an Agent: to accept a request and use a response handler to emit events.

### Definition

```python
@runtime_checkable
class IAgentRuntime(Protocol):
    """Protocol defining the strict signature an agent developer must implement."""

    @property
    @abstractmethod
    def manifest(self) -> AgentDefinition:
        """Accessor for the static configuration/metadata of the agent."""
        ...

    @abstractmethod
    def assist(self, session: ISession, request: AgentRequest, handler: IResponseHandler) -> Awaitable[None]:
        """Process a request and use the response handler to emit events.

        Args:
            session: The active memory interface.
            request: The strictly typed input envelope.
            handler: The callback interface for emitting thoughts, data, and streams.
        """
        ...
```

### Key Components

1.  **`manifest`**: A property that returns the agent's static configuration (`AgentDefinition`). This allows runtime inspection of the agent's capabilities, inputs, and outputs.
2.  **`assist`**: The primary entry point for execution.
    *   **Inversion of Control**: Instead of yielding events, the agent calls methods on the provided `IResponseHandler`.

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
