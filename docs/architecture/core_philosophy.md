# Core Philosophy

The `coreason-manifest` architecture is built upon a State-of-the-Art (SOTA) doctrine that prioritizes safety, determinism, and verifiability above all else. This philosophy is encoded into every class and module within the package.

## 1. Passive by Design

The most critical architectural decision is the strict separation of concerns between **definition** (the manifest) and **execution** (the runtime).

*   **`spec/` Directory**: Contains *only* pure data structures (Pydantic models). These define the "blueprint" of a cognitive system.
*   **`utils/` Directory**: Contains helper tools for builders, diffing, validation, and introspection.

**Crucially:** No network calls, no active LLM inferences, and no side effects occur within this package. This "Passive by Design" approach ensures:
1.  **Safety**: A manifest file cannot execute arbitrary code or trigger unauthorized actions simply by being loaded.
2.  **Stability**: Changes to the runtime environment or LLM providers do not require changes to the manifest definition.
3.  **Portability**: The same manifest can be executed by different runtimes (e.g., a local debugger vs. a scaled cloud cluster).

## 2. Strong Typing & Validation

We rely heavily on Pydantic V2 to enforce strict structural integrity. This is not just type hinting; it is runtime contract enforcement.

### Discriminated Unions
We use discriminated unions (e.g., `AnyNode` type field) to enable polymorphic behavior while maintaining strict type safety. This allows tools to parse a generic list of nodes and automatically instantiate the correct concrete class (e.g., `AgentNode` vs. `SwitchNode`) based on the data payload.

### Strict Field Validation
Every field is strictly validated. For example:
*   **`NodeID`**: Must be URL-safe alphanumeric strings.
*   **`RiskLevel`**: Enforced enum values (`safe`, `standard`, `critical`).
*   **`Edge.condition`**: Python AST validation to ensure conditions are safe expressions and not arbitrary code injection vectors.

This validation happens *at load time*, preventing invalid or dangerous configurations from ever reaching the execution stage.

## 3. Immutability and Auditability

In the era of autonomous agents, auditability is non-negotiable.

### Immutable Data Structures
Flows are designed to be treated as immutable data. Once a `GraphFlow` is published, it should not be modified in place. Instead, a new version is created. This immutability is enforced by the Pydantic `frozen=True` configuration on `CoreasonModel`.

### Hashing & Merkle Proofs
Because flows are pure data, they can be hashed. This allows for:
*   **Cryptographic Verification**: Ensuring a deployed agent is running the exact approved version of a flow.
*   **Semantic Diffing**: Comparing two versions of a flow to understand exactly what changed (e.g., "The prompt for Agent A was modified").
*   **Lineage Tracking**: Tracing the provenance of a decision back to the specific version of the manifest that produced it.
