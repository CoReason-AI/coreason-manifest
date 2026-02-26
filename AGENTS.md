# Coreason Agents: The Cognitive Operating System

> **Evolution Note:** This document describes the **2026 Neuro-Symbolic Architecture**. Agents are no longer just scripts; they are autonomous entities running on a governable, self-correcting runtime.

## 1. Philosophy: Agents as Software, Not Magic
In `coreason-manifest`, an agent is not a "prompt". It is a **recursive system** composed of three verifiable layers:
1.  **The Brain (Reasoning):** How it breaks down problems.
2.  **The Tools (Skills):** Atomic units of capability.
3.  **The Law (Contracts):** Rigid rules that the agent cannot violate.

---

## 2. The Reasoning Engine (The CPU)
The engine drives the agent's behavior. We support two primary modes:

### A. Recursive Decomposition (SOTA)
* **Class:** `DecompositionReasoning`
* **Behavior:** It does not just "act"; it plans.
    1.  Receives a Goal.
    2.  Checks if the Goal matches an **Atomic Skill**.
    3.  If not, it breaks the Goal into sub-goals (Recursion).
    4.  It builds a **PlanTree**—a hierarchical map of the problem.
* **Best For:** Complex, multi-step tasks (e.g., "
