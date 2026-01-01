# **AGENTS.md**

**Note to Agent:** This file contains strict rules and context for this repository. Read this before planning or executing tasks.

# **PRIMARY DIRECTIVE: STRICT DEVELOPMENT PROTOCOL**

**You are an advanced coding LLM tasked with implementing changes in this repository. It is imperative that you adhere strictly to this iterative, atomic, and test-driven development protocol. Do not attempt to implement the entire specification at once.**

## **The Protocol:**

1. **Comprehensive Analysis:** Thoroughly review the user's request and the detailed specifications provided. Examine the current state of the existing codebase to understand the existing architecture and what has already been implemented.
2. **Decomposition and Planning:** Identify the delta between the current codebase and the specification. Break down all pending work into a list of small, atomic units. An atomic unit must be independently implementable and testable. **You MUST print all pending work as atomic units prior to selecting the first task.**
3. **Select ONE Atomic Unit (The "One Step" Rule):** Choose one and only one atomic unit from your list to implement in this iteration. Select the smallest possible increment that moves the project toward the goal.
4. **Implementation:** Build the functionality for this single atomic unit, ensuring it adheres strictly to the architectural patterns defined in this document.
5. **Rigorous Testing:** Write comprehensive unit tests specifically for the implemented unit. This must include positive tests, negative tests, boundary conditions, and all foreseeable edge cases.
6. **Validation and Regression Check:** Ensure all newly added tests pass. Crucially, verify that all pre-existing tests still pass. There must be zero regressions.
   * *Constraint:* If a test fails more than twice after attempted fixes, STOP and re-evaluate the implementation strategy. Do not loop endlessly.
7. **Commit:** Deliver the complete, high-quality implementation and its corresponding tests, ready for an atomic commit.

## **1. Project Overview**

* **Type:** Python Application / Library
* **Language:** Python 3.12, 3.13, 3.14 (Latest 3 versions)
* **Package Manager:** Poetry
* **License:** Prosperity Public License 3.0 (Proprietary/Dual-licensed)
* **Project Structure:** src layout (source code resides in src/coreason_manifest)

## **2. Environment & Commands**

The project is managed via Poetry. Do not use pip directly unless inside a Docker build stage.

* **Install Dependencies:** poetry install
* **Run Linter (Pre-commit):** poetry run pre-commit run --all-files
* **Run Tests:** poetry run pytest
* **Build Docs:** poetry run mkdocs build --strict
* **Build Package:** poetry build (or python -m build in CI)

## **3. Development Rules**

### **Code Style & Quality**

This project uses **Ruff** for Python linting/formatting, **Mypy** for typing, and **Hadolint** for Dockerfiles.

* **Formatting:** Do not manually format. Run poetry run ruff format .
* **Linting:** Fix violations automatically where possible: poetry run ruff check --fix .
* **Docker Linting:** Checked via pre-commit (hadolint).
* **Typing:**
  * Strict static typing is encouraged.
  * Run checks with: poetry run mypy .
  * Avoid Any wherever possible.
* **Logging:** Use the project's centralized logging configuration.
  * *Good:* from src.utils.logger import logger -> logger.info("...")
* **Licensing:** Every .py file must start with the standard license header.

### **Legal & Intellectual Property**

Strict Prohibition on External Code:
You are strictly forbidden from copying, reproducing, imitating, or drawing from any external codebases, especially GPL, AGPL, or other non-permissive licenses or copy left licenses. All generated logic must be original or derived from permissively licensed (e.g., MIT, Apache 2.0) sources and properly attributed.

### **File Structure**

* **Source Code:** src/coreason_manifest/
  * main.py: Entry point.
  * __init__.py: Package definition.
* **Tests:** tests/
  * Test files must start with test_.
  * Use pytest fixtures where appropriate.

### **Testing Guidelines**

**Mandatory Requirement: 100% Test Coverage.**

* **Test Strategy (Redundancy & Depth):**
  * **Redundant Coverage:** Verify critical logic via multiple vectors (e.g., unit tests for isolation AND integration tests for workflow). Overlap is desired.
  * **Simple Tests:** Verify happy paths and basic functionality.
  * **Complex Tests:** Verify multi-step workflows, state mutations, and heavy computation.
  * **Edge Cases:** Explicitly test boundary values, empty inputs, null states, and error handling.
  * **Exclusions:** Use # pragma: no cover sparingly and **only** for defensive code that is unreachable in standard execution.
  * **No Throwaway Scripts:** Never create temporary test files (e.g., temp.py). Always add proper tests to the tests/ directory.
* **External Services & APIs:**
  * **Scenario A (Default):** Use mocks (unittest.mock, pytest-mock, or respx) for ALL external calls.
  * **Scenario B (Credentials Provided):** If the user provides API keys or connection strings:
    * **DO NOT** remove the mocks.
    * **ADD** a separate suite of live integration tests marked with @pytest.mark.live.
    * **Standard Env Vars:** Expect Postgres credentials in PGHOST, PGPORT, PGUSER, PGPASSWORD, PGDATABASE.
* **Safety:** Never hardcode credentials in tests. Use environment variables.

## **4. Architecture & Security**

### **Logging & Observability**

This project enforces a centralized logging architecture using the `loguru` library.

*   **Standard:** `loguru` is the exclusive logging library. Do not use the built-in `logging` module or `print` statements.
*   **Outputs (Sinks):**
    *   **Console:** `stderr` (Human-readable text).
    *   **File:** `logs/app.log` (JSON-formatted, rotated every 500 MB or 1 day, retained for 10 days).
*   **Usage Example:**

    ```python
    from src.utils.logger import logger

    # Inside an Agent or Module
    logger.info("Agent started task", task_id="123")
    try:
        ...
    except Exception:
        logger.exception("Agent failed to execute task")
    ```

### **Configuration Standards (Environment Variables)**

Adhere to 12-Factor App principles. Use these standard variable names:

* **Core:**
  * APP_ENV: development, testing, production.
  * DEBUG: true or false.
  * SECRET_KEY: For cryptographic signing/sessions.
* **Logging:**
  * LOG_LEVEL: DEBUG, INFO, WARNING, ERROR (Configure loguru with this).
* **Infrastructure (if applicable):**
  * DOCKER_HOST: If interacting with the Docker engine.
  * SSH_PRIVATE_KEY / SSH_USER: If managing remote connections.
  * AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY: For AWS services.

### **CI/CD Context**

* **CI Environment:** GitHub Actions (Matrix testing on Ubuntu, Windows, MacOS).
* **Python Versions:** Tests run against Python 3.12, 3.13, and 3.14.

### **Docker Strategy**

* **Multi-stage Build:** The Dockerfile has a builder stage and a runtime stage.
* **User:** The app runs as a non-root user (appuser). **DO NOT** change this to root.
* **Base Image:** Uses python:3.12-slim.

### **Dependencies**

* **Management:** Always add dependencies via poetry add <package>.
* **Lock File:** poetry.lock must be committed.
* **Vulnerability Scanning:** CI uses Trivy. Ensure no Critical/High vulnerabilities are introduced.

## **5. Documentation**

* Documentation is built with **MkDocs Material**.
* Update docs/index.md or add new markdown files in docs/ when adding features.
* Ensure all public functions have docstrings (Google or NumPy style).

## **6. Workflow & Debugging Protocol**

If you encounter an error (e.g., test failure, linting error), follow this STRICT sequence:

1. **Read the Logs:** Do not guess. Read the complete error message.
2. **Isolate:** If multiple tests fail, focus on the simplest failure first.
3. **Reproduction:** If the error is obscure, create a minimal reproduction case within the test suite (not a temp file).
4. **Fix:** Apply the fix.
5. **Verify:** Run the specific test case again.

## **7. Human-in-the-Loop Triggers**

STOP and ASK the user before:

* Modifying database migrations or schema files.
* Deleting any file outside of src/ or tests/.
* Adding a dependency that requires OS-level libraries (e.g., libpq-dev).
* Committing any secrets or API keys (even for testing).
