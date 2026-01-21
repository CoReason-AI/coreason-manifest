# The Architecture and Utility of coreason-manifest

### 1. The Philosophy (The Why)

In the high-stakes world of GxP-regulated software and autonomous agents, "trust but verify" is not enough; we must verify before we even trust. The proliferation of autonomous agents brings a new class of risks: unpinned dependencies, unauthorized tool usage, and code tampering. Standard CI/CD pipelines often catch syntax errors but miss the subtle compliance violations that can compromise a regulated environment.

**coreason-manifest** was born from the "Blueprint" philosophy: *If it isn't in the manifest, it doesn't exist. If it violates the manifest, it doesn't run.*

Existing solutions often conflate structure with policy, embedding business rules directly into Python code. This makes them brittle and hard to audit. This package solves that by decoupling **structure** (schema), **interface** (code contract), **policy** (compliance rules), and **integrity** (tamper-proofing). It acts as the immutable gatekeeper for the Agent Development Lifecycle, ensuring that every artifact produced is not just functional, but compliant by design.

### 2. Under the Hood (The Dependencies & Logic)

The architecture leverages a "best-in-class" stack where each component does exactly one thing well:

*   **`pydantic`**: Powers the **Agent Interface**. It transforms raw data into strict, type-safe Python objects (`AgentDefinition`). It handles the immediate "contract" validity (e.g., UUIDs are valid, versions are SemVer).
*   **`jsonschema`**: Powers the **Structural Validation**. Before Python objects are even instantiated, the raw YAML is validated against a standard JSON Schema (Draft 2020-12). This ensures that the data structure itself is sound and interoperable.
*   **Open Policy Agent (OPA) / Rego**: Powers the **Compliance Engine**. Complex business logic—like "Agent X cannot use Tool Y if it processes PII"—is offloaded to OPA. This allows policy to change independently of the code.
*   **`loguru`**: Provides the **Observability** layer, ensuring every validation step is auditable with precise timing and context.
*   **SHA256 Hashing**: Powers the **Integrity Checker**. By calculating a Merkle-like hash of the source code and comparing it to the manifest's signature, the system guarantees "what you signed is what you run."

The internal logic follows a strict "fail-fast" pipeline. The `ManifestEngine` orchestrates this: it parses the YAML, validates the schema, normalizes the data into Pydantic models, consults the OPA oracle for policy compliance, and finally cryptographically verifies the source code on disk.

### 3. In Practice (The How)

The usage of `coreason-manifest` is designed to be declarative and synchronous. It is the first line of defense before an agent is ever allowed to spin up.

Here is how the system enforces compliance in a clean, Pythonic way:

```python
from coreason_manifest import ManifestEngine, ManifestConfig
from coreason_manifest.errors import PolicyViolationError

# 1. Configure the Engine with your organizational policies
# This tells the engine WHERE the rules live (e.g., GxP compliance rules)
config = ManifestConfig(
    policy_path="./policies/gx_compliant.rego",
    tbom_path="./policies/tbom.json"  # Trusted Bill of Materials
)

# 2. Initialize the Gatekeeper
engine = ManifestEngine(config)

try:
    # 3. Load & Validate the Agent
    # This single call performs Schema Validation, Policy Checks, and Integrity Verification
    agent = engine.load_and_validate(
        manifest_path="./agents/finance_bot/agent.yaml",
        source_dir="./agents/finance_bot/src"
    )

    # 4. Happy Path: The agent is compliant and ready for use
    print(f"Agent '{agent.metadata.name}' (v{agent.metadata.version}) verified.")
    print(f"Authorized Tools: {len(agent.dependencies.tools)}")

except PolicyViolationError as e:
    # The agent was structurally valid but violated a business rule
    print(f"Compliance Blocked: {e}")

```

In this snippet, the `engine` abstracts away the complexity of running OPA subprocesses and traversing directory trees for hashing. The developer simply asks, "Is this agent valid?" and receives a definitive, audit-ready answer.
