# CoReason Manifest

> **"This package is the definitive source of truth. If it isn't in the manifest, it doesn't exist. If it violates the manifest, it doesn't run."**

## Overview

**CoReason Manifest** (`coreason_manifest`) is a 2026+ State-of-the-Art Neurosymbolic architecture component acting as the Universal Unified Ontology for the CoReason AI swarm ecosystem.

This is **NOT** a standard human-centric software package. It is a strictly bounded, AI-native, pure structural data library. It maintains the foundational mathematical, causal, and spatial definitions required to orchestrate a decentralized, zero-trust swarm of Large Language Models and mechanistic solvers.

## Core Architectural Directives

Contributors (both human and AI) are strictly bound to the **Shared Kernel Protocol**. Violating these directives will result in immediate rejection by the CI/CD architectural gates.

### 1. Passive by Design (No Execution)

This repository is a completely **Hollow Data Plane**.

* It is distributed exclusively as an inert data library (Wheel).
* Importing any module **MUST NOT** trigger runtime side effects (no network sockets, no file writing, no global loggers, no runtime loops).
* Dependencies are strictly limited to pure data parsers (`pydantic` and `pyyaml`).

### 2. The "God Context" Monolith Directive

We intentionally ignore legacy "Separation of Concerns" (SoC) anti-patterns.

* **NEVER federate or split `src/coreason_manifest/spec/ontology.py`.** * The entire universe of the ecosystem's state, orchestration, memory, and compute lives within this single artifact. This is a mathematical requirement to guarantee deterministic, zero-shot latent alignment across the swarm.

### 3. The Anti-CRUD Mandate & Strict Lexical Architecture

Legacy CRUD terminology flattens softmax distributions and introduces semantic drift.

* **Banned Terms:** `Create`, `Read`, `Update`, `Delete`, `User`, `Data`, `List`.
* **Required Paradigm:** State transitions are mapped using Judea Pearl’s Structural Causal Models (e.g., `Transmutation`, `DefeasibleCascade`, `StateMutationIntent`).
* **Categorical Suffixing:** Every schema ends in a strict topological contract:
* `...Event` / `...Receipt`: Cryptographically frozen historical facts (Append-only).
* `...Intent` / `...Task`: Authorized kinetic execution triggers.
* `...Policy` / `...Contract`: Rigid mathematical boundaries.
* `...State` / `...Manifest`: Ephemeral or declarative N-dimensional coordinates.



### 4. Cryptographic Determinism

All models subclass `CoreasonBaseState`, enforcing `frozen=True` immutability. Arrays and sets are mathematically sorted during instantiation to guarantee deterministic canonical hashing (RFC 8785) across varying distributed environments.

## Repository Structure

```text
coreason_manifest/
├── src/coreason_manifest/
│   ├── spec/
│   │   └── ontology.py       # THE GOD CONTEXT: All Pydantic models, TypeAliases, and Enums.
│   └── utils/
│       └── algebra.py        # Pure algebraic functors, matrix projections, and validation.
├── scripts/
│   ├── evaluate_architecture.py  # CI gate blocking runtime side-effects.
│   ├── semantic_diff.py          # CI gate enforcing backward schema compatibility.
│   └── swarm_watchdog.py         # Semantic scanner for intellectual property bounds.
├── coreason_ontology.schema.json # The compiled JSON Schema used for MCP Discovery.
└── pyproject.toml            # Project definitions and uv dependencies.

```

## Installation

This project requires **Python 3.14+** and uses [`uv`](https://www.google.com/search?q=%5Bhttps://github.com/astral-sh/uv%5D(https://github.com/astral-sh/uv)) as the standard package manager.

```bash
# Clone the repository
git clone https://github.com/CoReason-AI/coreason_manifest.git
cd coreason_manifest

# Install dependencies using uv
uv sync --all-extras --dev

```

## Mandatory Local Verification Workflow

To ensure the Shared Kernel remains mathematically sound, all commits must pass a stringent local evaluation before a Pull Request is opened. The CI/CD pipeline enforces a strict 95% test coverage floor.

**1. Formatting and Linting (Strict Ruff ruleset)**

```bash
uv run ruff format .
uv run ruff check . --fix

```

**2. Strict Type Checking**

```bash
uv run mypy src/ tests/

```

**3. Behavioral and Contract Testing**

```bash
uv run pytest

```

**4. Dependency Auditing**

```bash
uv run deptry src/

```

## License and Copyright

This repository and its entire ontology are the intellectual property of **CoReason, Inc.**

Licensed under the **Prosperity Public License 3.0**.

* **Non-Commercial:** Free for research, experiments, and open-source non-commercial use.
* **Commercial:** Permitted for a strict 30-day trial period.

For full license details, see the `LICENSE` file. For commercial licensing exceptions or inquiries, please explicitly contact `license@coreason.ai` or `gowtham.rao@coreason.ai`.

*(Genesis Commit: Initialized per CoReason Clean Room Protocol PIP-001 on 2026-01-01).*