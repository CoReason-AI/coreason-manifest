# Requirements

## System Requirements

*   **Python:** 3.12 or higher.
*   **Operating System:** Linux, macOS, or Windows (WSL recommended).
*   **Open Policy Agent (OPA):** The `opa` executable must be installed and available in the system `PATH` for policy enforcement.
    *   [Download OPA](https://www.openpolicyagent.org/docs/latest/#running-opa)

## Python Dependencies

The core library depends on the following packages:

*   **pydantic (>=2.12.5):** Data validation and settings management using Python type hints.
*   **jsonschema (>=4.25.1):** An implementation of the JSON Schema specification for Python.
*   **pyyaml (>=6.0.3):** YAML parser and emitter for Python.
*   **loguru (>=0.7.2):** Python logging made (stupidly) simple.
*   **anyio (>=4.3.0):** High level asynchronous concurrency and networking framework.
*   **aiofiles (>=23.2.1):** File support for asyncio.
*   **httpx (>=0.27.0):** A next-generation HTTP client for Python.

### Server Mode Dependencies

To run `coreason-manifest` as a Compliance Microservice (Service C), the following additional dependencies are required:

*   **fastapi (>=0.111.0):** Modern, fast (high-performance), web framework for building APIs with Python.
*   **uvicorn (>=0.30.1):** An ASGI web server implementation for Python.

## Development Dependencies

For contributing to the project, you will also need:

*   **poetry:** Dependency management and packaging made easy.
*   **pytest:** A mature full-featured Python testing tool.
*   **ruff:** An extremely fast Python linter and code formatter.
*   **mypy:** Optional static typing for Python.
*   **mkdocs-material:** Documentation site generator.
