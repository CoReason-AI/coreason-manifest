# **AGENTS.md**

**Note to Agent:** This file contains the **Supreme Law** for this repository. It defines the architectural constraints of a "Shared Kernel." Read this before planning or executing *any* task.

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

### **Logging (Passive Pattern)**
* **Library Responsibility:** Expose a logger object (`loguru.logger`) but **DO NOT** configure it.
* **Consumer Responsibility:** The consuming application (Builder/Engine) will configure sinks, formats, and levels.
* **Pattern:**
    ```python
    from coreason_manifest.utils.logger import logger
    # usage is fine
    logger.debug("Validating manifest...")
    # configuration (logger.add) is FORBIDDEN in library code
    ```

## **4. File Structure Constraints**

* **`src/coreason_manifest/`**:
    * **`spec/`**: Pure Pydantic models (The "Blueprint").
    * **`policies/`**: OPA Rego files (if applicable, treated as data).
    * **`utils/`**: Pure utility functions (no side effects).
* **Root**:
    * **NO** `Dockerfile`.
    * **NO** `app.py` or `server.py`.

## **5. Testing Guidelines**

* **Mock External Interactions:** Since this is a pure library, unit tests should mock *everything* external. There should be no need for integration tests against real databases or APIs within this repo.
* **Schema Validation Tests:** Focus heavily on testing valid/invalid YAML configurations against the Pydantic models.
* **"Passive" Tests:** specific tests (like `test_logger_creation.py`) must exist to PROVE that importing the library does not modify the system state.

## **6. Human-in-the-Loop Triggers**

**STOP and ASK the user if:**
* You feel a feature requires adding a dependency that is not `pydantic` or `yaml`.
* You are tempted to add a "helper script" that runs a server.
* You encounter a requirement that seems to violate the "Shared Kernel" philosophy.

## 🛡️ Mandatory Local Verification Workflow

This package enforces a zero-tolerance policy for type errors, linting violations, and coverage drops. To ensure the Shared Kernel remains completely stable and immutable, **the following checks must be run locally before opening a Pull Request or finalizing an AI-generated refactor.** Failure to comply will result in an immediate rejection by the CI/CD pipeline.

### 1. Formatting and Linting
We use `ruff` with an aggressive, strict ruleset (including `SIM`, `C4`, `PERF`, and `FURB`). Run the auto-fixer to resolve import and syntax issues:
`uv run ruff format .`
`uv run ruff check . --fix`

### 2. Strict Type Checking
We run `mypy` in `strict = true` mode. There are no implicit optionals, and `Any` should be avoided wherever possible. Verify your types:
`uv run mypy src/ tests/`

### 3. Test Coverage
Ensure your new logic maintains the strict coverage mandates:
`uv run pytest`

*Note: Do not bypass type hints or add `# type: ignore` unless interacting with deeply dynamic external modules, and only do so with an explicit explanatory comment.*
