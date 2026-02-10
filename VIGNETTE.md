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

### 3. In Practice: The Lipitor Launch Protocol

To understand the power of a declarative manifest, let's consider a historical example of strategic decision-making: **The Launch of Lipitor**.

**The Strategic Context:**
In the late 1990s, the statin market was dominated by Zocor and Pravachol. Pfizer and Warner-Lambert had a more potent drug (Atorvastatin) but were late to market. They made a critical strategic decision: instead of relying solely on traditional sales representatives to push samples, they would deploy **Medical Science Liaisons (MSLs)**—PhD-level scientists—to engage in deep, peer-to-peer scientific dialogue with cardiologists.

This was not just a "tactic"; it was a fundamental shift in the *protocol* of engagement.

**Encoding Strategy into the Manifest:**
With `coreason-manifest`, this strategic logic is not buried in `if/else` statements deep in application code. It is elevated to the **Manifest Level**.

The workflow explicitly defines:
1.  **Analysis**: Identify the "Knowledge Gap" in a region.
2.  **Decision**: If a gap exists, the protocol *mandates* a science-first approach.
3.  **Routing**: The system dynamically routes execution to an expensive but high-impact `MedicalScienceLiaison` agent instead of a standard `SalesRepresentative`.

#### The Code (Strategic Intent as Schema)

Using the `ManifestBuilder`, we construct this protocol programmatically. Notice how the **Policy** (High Knowledge Gap -> Deploy MSL) becomes part of the graph topology via the `SwitchStep`.

```python
# from examples/02_pharma_launch/lipitor_strategy.py

# ... (Agent Definitions for Analyst, Director, MSL, Rep) ...

# Step 3: Router (SwitchStep)
# This encodes the conditional logic into the graph structure.
manifest_builder.add_step(
    SwitchStep(
        id="step_route",
        cases={
            "action == 'DEPLOY_MSL'": "step_msl", # The Strategic Path
            "action == 'DEPLOY_REP'": "step_rep"  # The Standard Path
        },
        default="step_rep"
    )
)
```

#### Simulation: Validating the Strategy

By running this manifest through the simulator, we can verify that the strategy holds under different market conditions.

*Scenario A: High Skepticism (New York)*
> **Analyst:** "Knowledge Gap Detected."
> **Director:** "Deploy MSL. Science-first approach required."
> **Outcome:** Prescription Lift +12.5% (Driven by Education)

*Scenario B: Friendly Territory (Texas)*
> **Analyst:** "No Gap."
> **Director:** "Deploy Rep. Maintain relationship."
> **Outcome:** Prescription Lift +3.2% (Driven by Presence)

This vignette demonstrates that `coreason-manifest` is not just about validating JSON schemas; it is about **validating strategic intent**. By defining the "Rules of Engagement" in the manifest, we ensure that every autonomous agent acts as a compliant extension of the organization's strategy.

### 4. Builder Pattern for Complex Manifests (New in v0.17)

As shown above, as agent systems grow into complex "God Objects" (ManifestV2) involving Workflows, Policy, and State, hand-writing YAML becomes error-prone and tedious.

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

For detailed technical specifications and usage instructions, please refer to the [Documentation Index](docs/index.md).
