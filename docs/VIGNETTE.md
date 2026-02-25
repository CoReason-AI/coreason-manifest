# The Architecture and Utility of coreason-manifest

### 1. The Philosophy (The Why)

In the high-stakes world of GxP-regulated software and autonomous agents, "trust but verify" is not enough; we must verify before we even trust. The proliferation of autonomous agents brings a new class of risks: unpinned dependencies, unauthorized tool usage, and code tampering. Standard CI/CD pipelines often catch syntax errors but miss the subtle compliance violations that can compromise a regulated environment.

**coreason-manifest** was born from the "Blueprint" philosophy: *If it isn't in the manifest, it doesn't exist. If it violates the manifest, it doesn't run.*

Existing solutions often conflate structure with policy, embedding business rules directly into Python code. This makes them brittle and hard to audit. This package solves that by decoupling **structure** (schema) and **interface** (code contract) from **policy** and **execution**. It acts as the immutable gatekeeper for the Agent Development Lifecycle, ensuring that every artifact produced is not just functional, but compliant by design.

### 2. Under the Hood (The Dependencies & Logic)

The architecture leverages a "best-in-class" stack where each component does exactly one thing well:

*   **`pydantic`**: Powers the **Agent Interface**. It transforms raw data into strict, type-safe Python objects (`AgentDefinition`). It handles the immediate "contract" validity (e.g., fields are strictly typed, values are validated).
*   **Shared Kernel**: This library is a **passive** Shared Kernel. It contains no active execution logic, server capabilities, or policy engines. It strictly provides the data structures that downstream services (Builder, Engine, Simulator) rely on.
*   **Serialization**: Core definitions (like `AgentDefinition`) use standard Pydantic models for maximum compatibility, while shared configuration models (like `GovernanceConfig`) use `CoReasonBaseModel` for enhanced JSON serialization.

### 3. In Practice (The How)

The usage of `coreason-manifest` is designed to be declarative and synchronous. It serves as the foundation for validating agent definitions programmatically.

Here is how the system validates compliance in a clean, Pythonic way:

```python
from coreason_manifest import AgentDefinition

# 1. Load Raw Data
# In a real scenario, this would come from an agent.yaml file or API payload
raw_data = {
    "type": "agent",
    "id": "research-agent-001",
    "name": "Deep Researcher",
    "role": "Senior Researcher",
    "goal": "Conduct deep internet research on specified topics.",
    "backstory": "You are a meticulous researcher who verifies all sources.",
    "model": "gpt-4-turbo",
    "tools": ["google-search", "web-scraper"],
    "knowledge": []
}

try:
    # 2. Validate Structure
    # This single call performs strict Schema Validation and Type Checking
    agent = AgentDefinition(**raw_data)

    # 3. Happy Path: The agent is structurally valid and ready for use
    print(f"Agent '{agent.name}' verified.")
    print(f"Authorized Tools: {len(agent.tools)}")

    # Note: Further policy checks (OPA) and integrity verification are performed
    # by the consuming services (Builder, Engine) using this validated object.

except Exception as e:
    # The agent was invalid
    print(f"Validation Failure: {e}")
```

In this snippet, the library ensures that the data structure is sound and strictly typed. If a field is missing or an ID is invalid, it fails fast before the data enters the system.

### 4. Builder Pattern for Complex Manifests (New in v0.17)

As agent systems grow into complex "God Objects" (ManifestV2) involving Workflows, Policy, and State, hand-writing YAML becomes error-prone and tedious.

The `ManifestBuilder` solves this developer experience friction:

```python
from coreason_manifest.builder import ManifestBuilder, AgentBuilder

# Fluent interface for creating complex objects
manifest = (
    ManifestBuilder("ComplexSystem")
    .add_agent(AgentBuilder("Analyst").with_model("gpt-4").build_definition())
    .set_policy(PolicyDefinition(max_steps=50))
    .build()
)
```

This approach ensures type safety at compile time rather than validation errors at runtime.

### Further Reading

For detailed technical specifications and usage instructions, please refer to the [Documentation Index](index.md).
