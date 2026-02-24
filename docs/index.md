# Coreason Manifest

**The Universal Shared Kernel for Cognitive Architectures**

`coreason-manifest` is the foundational schema library that defines the *structure* and *intent* of cognitive workflows. It serves as the **Shared Kernel**—a ubiquitous language that binds together the various components of an AI system, from the builder SDKs to the runtime execution engines.

## The Blueprint Philosophy

The core doctrine of this package is strict separation of **definition** from **execution**.

*   **What it is**: A collection of strictly typed, immutable Pydantic V2 models that define *what* a cognitive system should do.
*   **What it is NOT**: It contains **zero runtime execution logic**, no active LLM calls, and no side effects.

This "Blueprint Philosophy" ensures that a flow defined in `coreason-manifest` is:
1.  **Portable**: Can be serialized, stored, and transported across different environments (cloud, edge, local).
2.  **Verifiable**: Can be statically analyzed for structural integrity, security risks, and policy compliance before a single line of code is executed.
3.  **Auditable**: Every change to a flow is a data change, allowing for perfect version control, diffing, and cryptographic signing.

## Core Capabilities

The manifest provides the following architectural primitives:

### 1. Flow Topologies
*   **`LinearFlow`**: For sequential, deterministic pipelines where A leads to B leads to C.
*   **`GraphFlow`**: For complex, non-linear cognitive architectures involving loops, conditional branching, and dynamic routing (DAGs).

### 2. Cognitive Nodes
The vertices of your cognitive graph, including:
*   **`AgentNode`**: The primary worker unit, driven by a `CognitiveProfile` (persona + reasoning engine).
*   **`SwitchNode`**: Deterministic routing based on variable state.
*   **`InspectorNode` & `EmergenceInspectorNode`**: Semantic evaluation and guardrails.
*   **`SwarmNode`**: Dynamic map-reduce operations with fractional failure tolerance (allowing swarms to succeed even if a percentage of ephemeral workers fail).
*   **`HumanNode`**: Advanced human-in-the-loop interactions supporting synchronous blocking, asynchronous steering, and non-blocking "shadow mode" monitoring.
*   **`PlannerNode`**: High-level goal decomposition.

### 3. Data & State
*   **`Blackboard`**: An abstract shared memory space where nodes read and write variables.
*   **`DataSchema`**: Strict JSON Schemas defining the shape of inputs, outputs, and intermediate state.

### 4. Governance & Resilience
*   **`Governance`**: Global policies for risk management, including a **global recursive kill-switch** that statically scans the entire object graph to prevent high-risk tools from executing in low-risk flows.
*   **`ResilienceConfig`**: Error handling strategies like retries, fallbacks, and circuit breakers defined at the node level.

### 5. Tools & Skills
*   **`ToolPack`**: Collections of capabilities (functions, APIs) available to agents.

## Usage

This package is intended to be consumed by:
*   **Builders**: SDKs and UIs that generate valid manifest files.
*   **Runtimes**: Execution engines that interpret the manifest and orchestrate the actual LLM calls.
*   **Auditors**: Compliance tools that verify the safety and integrity of a flow.
