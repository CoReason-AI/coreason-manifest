# **AGENTS.md**

**Note to Agent:** This file contains the **Supreme Law** for this repository. It defines the architectural constraints of a "Shared Kernel." Read this before planning or executing *any* task.

# **Core Guidelines: Coreason Architectural Standard**

**Status:** Immutable Constitution
**Scope:** All Naming, Design, and Structural Decisions.

## **1. Philosophy of Topological Determinism**

* **The Philosophy:** We abandon generic names like "Manifest" or "Recipe" because they obscure the runtime behavior. We adopt names that describe the control flow topology.
* **The Rule:** "If it is a list, name it a Sequence/Flow. If it loops, name it a Graph."
    * A deterministic script must be a `Sequence` or `LinearFlow`.
    * A cyclic, non-deterministic structure must be a `Graph` or `GraphFlow`.

## **2. Functional Over Abstract Naming**

* **The Philosophy:** Components must be named after their mechanical function, not an abstract concept or biological metaphor.
* **The Rule:** "Use functional component names (`Switch`, `FastPath`) over abstract/biological names (`Router`, `Reflex`)."
    * *Switch:* Routes traffic based on conditions (visual metaphor).
    * *FastPath:* A heuristic bypass for high-latency reasoning (engineering term).

## **3. SOTA Engineering Standards**

* **The Philosophy:** We reject internal project code names in favor of industry-standard terms from Erlang, DSPy, and Multi-Agent Systems.
* **The Rule:** "Use SOTA engineering terms (`Supervision`, `Blackboard`) over internal project names."
    * *Supervision:* Active lifecycle management (Actor Model).
    * *Blackboard:* Shared, observable memory (Multi-Agent Systems).
    * *Optimizer:* Self-improvement/compilation (DSPy).

## **4. Strict Ontological Suffixing (The "Greenfield" Rule)**

* **The Philosophy:** A developer must know the architectural role of a class solely by its name.
* **The Rules:**
    * **Graph Vertices:** MUST end in `Node`. (e.g., `EmergenceInspectorNode`, `PlaceholderNode`).
    * **Cognitive Engines:** MUST end in `Reasoning`. (e.g., `DecompositionReasoning`, `GraphReasoning`).
    * **Base Classes:** MUST use `Base` prefix or `Base` suffix. (e.g., `InspectorNodeBase`).

## **5. Anti-Anthropomorphism Directive**

* **The Philosophy:** We build software, not synthetic life. Avoid nomenclature that implies biology.
* **The Rule:** "Replace biological metaphors with cognitive engineering terms."
    * `Brain` -> **`CognitiveProfile`** (A configuration of reasoning and persona).
    * `Reflex` -> **`FastPath`** (A low-latency execution route).
    * `Atom` -> **`Decomposition`** (Breaking tasks into DAGs).

# **PRIMARY DIRECTIVE: THE SHARED KERNEL PROTOCOL**

**Current Status:** Pure Data Library
**Role:** Definitive Source of Truth for Schemas and Contracts.

## **1. The "No Execution" Directives**

You are strictly forbidden from introducing "Active" or "Runtime" logic into this repository. Adhere to the following architectural laws without exception:

### **Law 1: Passive by Design (The "Import" Rule)**
* **Constraint:** Importing `coreason_manifest` (or any submodule) MUST NOT trigger side effects.
* **Forbidden:**
    * Creating directories (e.g., `os.mkdir("logs")`) on module level.
    * Configuring global logging sinks (e.g., `logger.add(...)`) on import.
    * Opening sockets, database connections, or reading files immediately upon import.
* **Allowed:** Defining classes, variables, and constants.

### **Law 2: No Runtime Artifacts (The "Library" Rule)**
* **Constraint:** This project is a **Library** (distributed as a Wheel), NOT a Service.
* **Forbidden:**
    * `Dockerfile` or `Containerfile` (Libraries are not deployed as containers).
    * `docker-compose.yml`.
    * Server Entry Points (e.g., `uvicorn`, `flask`, `main.py` that starts a loop).
    * CI workflows that build/push containers (`docker.yml`).

### **Law 3: Decoupled Contracts (The "Middleware" Rule)**
* **Constraint:** The Manifest defines the *shape* of data, not the *method* of execution.
* **Forbidden:** Dependencies on execution-layer libraries (e.g., `fastapi`, `starlette`, auth middleware, database drivers like `psycopg2`).
* **Allowed:** Pure data dependencies (`pydantic`, `pyyaml`).

---

## **2. Development Protocol**

**You MUST follow this iterative process for every task:**

1.  **Architectural Audit:** Before writing code, ask: *"Does this change introduce a runtime side effect?"* If yes, STOP.
2.  **Atomic Implementation:** Break tasks into the smallest testable units.
3.  **Regression Check:** Ensure no re-introduction of "Ghosts" (e.g., do not accidentally re-add a Dockerfile because a generic template suggested it).
4.  **Test Coverage:** Maintain 100% coverage. Tests must verify *logic*, not just existence.

---

## **3. Technical Standards**

### **Environment & Package Management**
* **Manager:** `uv`.
* **Language:** Python 3.12+.
* **License:** Prosperity Public License 3.0. Every file must include the license header.

### **Code Style & Typing**
* **Linting:** `ruff check --fix` (Strict).
* **Formatting:** `ruff format`.
* **Typing:** Strict `mypy`. Use `Pydantic` models for all data structures. Avoid `dict` or `Any` where a schema can be defined.
