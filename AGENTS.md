# **AGENTS.md: The coreason-manifest Constitution**

**Note to Agent:** This file contains the **Supreme Law** for this repository. It defines the architectural constraints of a "Shared Kernel." Read this before planning or executing *any* task.

## **PRIMARY DIRECTIVE: THE SHARED KERNEL PROTOCOL**

**Current Status:** Pure Data Library
**Role:** Definitive Source of Truth for Schemas and Contracts.

### **The "No Execution" Directives**

You are strictly forbidden from introducing "Active" or "Runtime" logic into this repository. Adhere to the following architectural laws without exception:

1. **Passive by Design (The "Import" Rule):** Importing `coreason_manifest` (or any submodule) MUST NOT trigger side effects.
* *Forbidden:* Creating directories, configuring global logging sinks (`logger.add(...)`), opening sockets, or database connections on import.
* *Allowed:* Defining Pydantic classes, variables, and constants.


2. **No Runtime Artifacts (The "Library" Rule):** This project is a Library (distributed as a Wheel), NOT a Service.
* *Forbidden:* `Dockerfile`, `docker-compose.yml`, server entry points (e.g., `uvicorn`, `flask`), or CI workflows that build containers.


3. **Decoupled Contracts (The "Middleware" Rule):** The Manifest defines the *shape* of data, not the *method* of execution.
* *Forbidden:* Dependencies on execution-layer libraries (e.g., `fastapi`, auth middleware, database drivers).
* *Allowed:* Pure data dependencies (`pydantic`, `pyyaml`).



---

## **1. Philosophy: Agents as Software, Not Magic**

In `coreason-manifest`, an agent is not a simple "prompt." It is modeled as a **recursive system configuration** composed of three verifiable data layers. While external runtimes handle the execution, this library defines their strict blueprints:

1. **The Brain (Reasoning):** Schemas defining how an agent breaks down problems.
2. **The Tools (Skills):** Schemas representing atomic units of capability.
3. **The Law (Contracts):** Rigid rules and constraints that the runtime agent cannot violate.

---

## **2. The Reasoning Engine (The CPU Blueprints)**

The external reasoning engine drives the agent's behavior. This repository defines the schemas to configure that engine. We support two primary modes, modeled strictly as data:

### **A. Recursive Decomposition (SOTA)**

* **Class:** `DecompositionReasoning` (A pure Pydantic model)
* **Schema Behavior:** It outlines the configuration for an agent that plans before it acts. The schema strictly types the data required for the runtime to:
1. Receive and structure a **Goal**.
2. Check if the Goal matches an **Atomic Skill** schema.
3. If not, break the Goal into sub-goals (Recursion).
4. Build a **PlanTree**—a hierarchical, validatable data map of the problem.


* **Best For:** Complex, multi-step tasks (e.g., "Analyze a raw clinical dataset, normalize it to the OMOP Common Data Model, and generate a summary report").

---

## **3. Development & Technical Standards**

**Iterative Protocol:**

1. **Architectural Audit:** Ask: *"Does this change introduce a runtime side effect?"* If yes, STOP.
2. **Atomic Implementation:** Break tasks into the smallest testable units.
3. **Test Coverage:** Maintain 100% coverage verifying logic and schema validation, including "Passive Tests" to prove imports do not modify system state.

**Technical Constraints:**

* **Manager:** `uv`.
* **Language:** Python 3.12+.
* **Typing:** Strict `mypy`. Use `Pydantic` models for all data structures. Avoid `dict` or `Any`.
* **Logging:** Expose a logger (`loguru.logger`) but **DO NOT** configure it. Configuration is the consumer's responsibility.

---

## **4. Human-in-the-Loop Triggers**

**STOP and ASK the user if:**

* You feel a feature requires adding a dependency that is not `pydantic` or `yaml`.
* You are tempted to add a "helper script" that runs a server or engine.
* You encounter a requirement that blurs the line between schema definition and runtime execution.

---
