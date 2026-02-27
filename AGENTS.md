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
4.  **Test Coverage (The 95% Rule):** Maintain a strict `>= 95%` test coverage floor. **Do not write "filler tests" just to hit 100%.** If a branch of code is already proven impossible by strict Pydantic/mypy typing, remove the branch (Dead Code Elimination) rather than mocking Python internals to test it. Tests must verify *behavior* and *contracts*, not just line execution.

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

* **Behavioral over Unit:** Favor integration and BDD-style tests that verify business capabilities (e.g., routing, orchestration) over micro-tests that check class initialization.
* **Property-Based Edge Cases:** Use `hypothesis` for generating randomized data payloads to test schema edge cases and Pydantic validators. Avoid hardcoding synthetic edge cases.
* **Security Fuzzing:** Any changes to the `loader` or `sandbox` modules must be verified against our `atheris` fuzzing targets to prevent path-traversal and parsing vulnerabilities.
* **Schema Contracts:** Changes to Pydantic models must not break the generated `model_json_schema()`. Contract tests must pass before merging.
* **Performance Benchmarks:** Complex graph validations and Merkle hashing must pass `pytest-benchmark` thresholds to prevent silent regressions.
* **Mock External Interactions:** Since this is a pure library, mock everything external (like LLM APIs) unless explicitly writing an 'Evals' test.

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
Ensure your new logic maintains the strict 95% coverage mandate and passes all behavioral checks:
`uv run pytest --cov --cov-fail-under=95`

*Note: Do not bypass type hints or add `# type: ignore` unless interacting with deeply dynamic external modules, and only do so with an explicit explanatory comment.*
