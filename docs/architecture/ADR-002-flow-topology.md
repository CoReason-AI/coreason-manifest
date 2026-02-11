# Adoption of Linear vs. Graph Flow Topology and SOTA Component Naming

**Status:** Accepted
**Date:** 2025-05-15 (Estimated)
**Context:** Moving from "Static Manifest" paradigm to "Executable Flow" paradigm.

## Context

The previous architecture relied on a "Static Manifest" (YAML configuration) that was ambiguous regarding execution flow. It used generic names like "Manager" or "Handler" and custom terms like "Maco", "Episteme", "Foundry".
We are refactoring the core kernel to enforce **Topological Determinism** and align with **SOTA Systems Engineering**.

## Decision

We are adopting a strict "Linear vs. Graph" topology distinction and renaming components to match industry-standard patterns (Erlang, DSPy, Kubeflow).

### 1. Topology Mapping

| Old Concept | New Concept | Justification |
| :--- | :--- | :--- |
| `Manifest` (Ambiguous) | `LinearFlow` | Explicitly defines a deterministic, sequential list of steps (Script). |
| `Topology` | `GraphFlow` | Explicitly defines a cyclic, branching network of nodes (System). |
| `StateDefinition` | `Blackboard` | Reclaims the classic Blackboard Pattern (Hayes-Roth) for shared memory. |

### 2. Component Mapping (Engines)

| Old Name | New Name | Justification (SOTA Alignment) |
| :--- | :--- | :--- |
| `Episteme` | `ReasoningEngine` | "Reasoning" is the standard term for System 2 slow thinking in LLM agents. |
| `Cortex` | `Reflex` | "Reflex" describes System 1 fast response more accurately than the generic "Cortex". |
| `Maco` / `RecoveryConfig` | `Supervision` | Aligns with **Erlang/OTP Supervisor** pattern. Agents don't just "recover"; they are "supervised" for lifecycle. |
| `Foundry` / `OptimizationIntent` | `Optimizer` | Aligns with **DSPy** and **TextGrad**. Agents are compiled programs to be optimized against metrics. |

### 3. Node Mapping

| Old Name | New Name | Justification |
| :--- | :--- | :--- |
| `CognitiveProfile` | `AgentBrain` | "Brain" encapsulates the cognitive configuration (Role + Reasoning + Reflex). |
| `RouterNode` | `SwitchNode` | "Switch" describes the mechanical action of routing based on a variable (like a network switch). |
| `GenerativeNode` | `PlannerNode` | "Planner" implies dynamic goal solving using an Optimizer. |
| `SemanticRef` | `Placeholder` | "Placeholder" clearly indicates a slot to be filled later. |

## Consequences

* **Clarity:** The shape of the execution is immediately visible from the class name.
* **Standardization:** New engineers familiar with distributed systems (Erlang) or modern AI (DSPy) will recognize the terms immediately.
* **Strictness:** Generic names are now forbidden, enforcing architectural intent.
