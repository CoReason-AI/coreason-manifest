# Coreason Manifest: Study Guide

Welcome to the Coreason Manifest learning journey. This guide is designed to take you from "Zero to Hero" by structuring the documentation into a cohesive narrative.

The Coreason Manifest is not just a schema library; it is the **Shared Kernel**—the immutable contract between the Builder (UI), the Engine (Runtime), and the Analyst (Eval).

Follow this path to master the architecture.

## Phase 1: Philosophy (The "Why")

Before writing code, understand the architectural constraints and the "Code is Source of Truth" doctrine.

1.  **[Vignette](VIGNETTE.md)**: Start here for the high-level narrative. Why does this project exist? What problems does it solve in GxP-regulated environments?
2.  **[Agents Directive](AGENTS.md)**: The "Supreme Law" of the repository. Understand the "Passive Library" and "No Execution" rules that govern this Shared Kernel.
3.  **[Shared Kernel Strategy](architecture/ADR-001-shared-kernel-boundaries.md)**: A deeper dive into the architectural boundaries between Data (Spec) and Logic (Utils).

## Phase 2: Building Agents (The "What")

Learn how to define the structural blueprint of an autonomous agent.

1.  **[Graph Recipes](graph_recipes.md)**: The core of V2 orchestration. Learn how to build Directed Cyclic Graphs (DCGs) for complex workflows, loops, and conditional branching.
2.  **[Episteme & Reasoning](episteme_reasoning.md)**: Configure "System 2" thinking. Enable agents to critique their own work, detect gaps, and reason about their reasoning.
3.  **[Builder SDK](builder_sdk.md)**: While the YAML schema is the source of truth, the Python SDK provides a fluent, type-safe API for constructing manifests programmatically.

## Phase 3: Governance & Security (The "Rules")

In a regulated environment, compliance is not an afterthought—it's a constraint.

1.  **[Governance Policy](governance_policy_enforcement.md)**: Learn how to define organizational standards, allowed domains, and risk limits for tools.
2.  **[Identity & Access Management](identity_access_management.md)**: Understand how to enforce Role-Based Access Control (RBAC) and inject user context securely into the agent's execution environment.

## Phase 4: Runtime Engineering (The "How")

Understand how the passive manifest translates into active behavior in the runtime engine.

1.  **[Runtime Principles](runtime/runtime_principles.md)**: The theoretical foundation of the execution model.
2.  **[Flow Governance](flow_governance.md)**: Resilience patterns. Learn how to configure retries, fallbacks, and circuit breakers to handle failures gracefully.

## Phase 5: UX & Collaboration (The "Human")

Agents don't work in a vacuum. Learn how to design for human-AI collaboration.

1.  **[UX & Collaboration](ux_collaboration.md)**: Configure "Human-on-the-Loop" interactions, visualization hints, and co-editing protocols.

## Reference

*   **[Package Structure](package_structure.md)**: Navigate the codebase layout.
*   **[Full Index](index.md)**: The complete list of all documentation files.
