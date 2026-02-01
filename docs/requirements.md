# Requirements

## System Requirements

*   **Python:** 3.12 or higher.
*   **Operating System:** Linux, macOS, or Windows (WSL recommended).

## Python Dependencies

The core library depends on the following packages (as defined in `requirements.txt`):

*   **pydantic (>=2.12.5):** Data validation and settings management using Python type hints.
*   **pydantic-settings (>=2.12.0):** Settings management for Pydantic.
*   **loguru (>=0.7.3):** Python logging made simple.
*   **pyyaml (>=6.0.3):** YAML parser and emitter for Python.
*   **opentelemetry-api (>=1.39.1):** OpenTelemetry API for observability.
*   **coreason-identity (>=0.4.1):** Identity management for Coreason.
*   **python-dotenv (>=1.2.1):** Read key-value pairs from a .env file.
*   **annotated-types (>=0.7.0):** Reusable constraint types for Pydantic.
*   **cryptography (>=46.0.4):** Cryptographic primitives.
*   **authlib (>=1.6.6):** Authentication library.

## Development Dependencies

For contributing to the project, you will also need:

*   **poetry:** Dependency management and packaging made easy.
*   **pytest:** A mature full-featured Python testing tool.
*   **ruff:** An extremely fast Python linter and code formatter.
*   **mypy:** Optional static typing for Python.
