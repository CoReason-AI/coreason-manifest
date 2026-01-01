# coreason-manifest

This package is the definitive source of truth. If it isn't in the manifest, it doesn't exist. If it violates the manifest, it doesn't run.

[![CI](https://github.com/CoReason-AI/coreason_manifest/actions/workflows/ci.yml/badge.svg)](https://github.com/CoReason-AI/coreason_manifest/actions/workflows/ci.yml)

## Getting Started

### Prerequisites

- Python 3.12+
- Poetry

### Installation

1.  Clone the repository:
    ```sh
    git clone https://github.com/example/example.git
    cd my_python_project
    ```
2.  Install dependencies:
    ```sh
    poetry install
    ```

### Usage

-   Run the linter:
    ```sh
    poetry run pre-commit run --all-files
    ```
-   Run the tests:
    ```sh
    poetry run pytest
    ```
