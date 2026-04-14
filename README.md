# CoReason Manifest

[![PyPI](https://img.shields.io/pypi/v/coreason-manifest?style=flat-square&logo=pypi&logoColor=white&label=PyPI)](https://pypi.org/project/coreason-manifest/)
[![PyPI Downloads](https://img.shields.io/pypi/dm/coreason-manifest?style=flat-square)](https://pypi.org/project/coreason-manifest/)
[![Crates.io](https://img.shields.io/crates/v/coreason-manifest?style=flat-square&logo=rust&label=Crates.io)](https://crates.io/crates/coreason-manifest)
[![Crates Downloads](https://img.shields.io/crates/dv/coreason-manifest?style=flat-square&logo=rust)](https://crates.io/crates/coreason-manifest)
[![npm](https://img.shields.io/npm/v/@coreason/coreason-manifest?style=flat-square&logo=npm&label=npm)](https://www.npmjs.com/package/@coreason/coreason-manifest)
[![npm Downloads](https://img.shields.io/npm/dw/@coreason/coreason-manifest?style=flat-square&logo=npm)](https://www.npmjs.com/package/@coreason/coreason-manifest)
[![npm Types](https://img.shields.io/npm/types/@coreason/coreason-manifest?style=flat-square&logo=typescript)](https://www.npmjs.com/package/@coreason/coreason-manifest)
[![Node Version](https://img.shields.io/node/v/@coreason/coreason-manifest?style=flat-square&logo=nodedotjs)](https://www.npmjs.com/package/@coreason/coreason-manifest)

[![CI](https://img.shields.io/github/actions/workflow/status/CoReason-AI/coreason-manifest/ci.yml?branch=main&style=flat-square&logo=github&label=CI)](https://github.com/CoReason-AI/coreason-manifest/actions/workflows/ci.yml)
![Platforms](https://img.shields.io/badge/platforms-Linux%20%7C%20macOS%20%7C%20Windows-lightgrey?style=flat-square)
[![Coverage](https://img.shields.io/codecov/c/github/CoReason-AI/coreason-manifest?style=flat-square&logo=codecov&logoColor=white&label=Coverage)](https://app.codecov.io/gh/CoReason-AI/coreason-manifest)
[![Security Audit](https://img.shields.io/github/actions/workflow/status/CoReason-AI/coreason-manifest/security.yml?branch=main&style=flat-square&logo=github&label=Security%20Audit)](https://github.com/CoReason-AI/coreason-manifest/actions/workflows/security.yml)
[![CodeQL](https://img.shields.io/github/actions/workflow/status/CoReason-AI/coreason-manifest/codeql.yml?branch=main&style=flat-square&logo=github&label=CodeQL)](https://github.com/CoReason-AI/coreason-manifest/actions/workflows/codeql.yml)
[![Security: Bandit](https://img.shields.io/badge/security-bandit-yellow.svg?style=flat-square)](https://github.com/PyCQA/bandit)
[![SLSA Level 3](https://img.shields.io/badge/SLSA-Level%203-blue?style=flat-square&logo=slsa)](https://slsa.dev/spec/v1.0/levels)
[![Signed by Sigstore](https://img.shields.io/badge/Signed_by-Sigstore-blueviolet?style=flat-square&logo=sigstore)](https://sigstore.dev/)
[![SBOM](https://img.shields.io/badge/SBOM-SPDX_Included-brightgreen?style=flat-square&logo=databricks)](https://spdx.dev/)
[![OpenSSF Scorecard](https://img.shields.io/ossf-scorecard/github.com/CoReason-AI/coreason-manifest?style=flat-square&label=OpenSSF)](https://scorecard.dev/viewer/?uri=github.com/CoReason-AI/coreason-manifest)
![Egress Filtered](https://img.shields.io/badge/Egress_Filtered-Step--Security-blue?style=flat-square)
[![Advanced Security](https://img.shields.io/github/actions/workflow/status/CoReason-AI/coreason-manifest/advanced-security.yml?branch=main&style=flat-square&logo=github&label=Advanced%20Security)](https://github.com/CoReason-AI/coreason-manifest/actions/workflows/advanced-security.yml)
![OSS-Fuzz](https://img.shields.io/badge/OSS--Fuzz-Pending-lightgray?style=flat-square)
![CII Best Practices](https://img.shields.io/badge/CII_Best_Practices-Pending-lightgray?style=flat-square)

![Python Versions](https://img.shields.io/pypi/pyversions/coreason-manifest?style=flat-square&logo=python&logoColor=white)
![Status](https://img.shields.io/pypi/status/coreason-manifest?style=flat-square)
![Format](https://img.shields.io/pypi/format/coreason-manifest?style=flat-square)
[![License](https://img.shields.io/badge/License-Prosperity%203.0-blue?style=flat-square)](./LICENSE)
[![Security Policy](https://img.shields.io/badge/Security-Policy-green?style=flat-square)](./SECURITY.md)


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
* Dependencies are strictly limited to pure data parsers and structural utilities (`pydantic`, `networkx`, `jsonpatch`, `numpy`, `canonicaljson`, `nh3`).

### 2. The "God Context" Monolith Directive

We intentionally ignore legacy "Separation of Concerns" (SoC) anti-patterns.

* **NEVER federate or split `src/coreason_manifest/spec/ontology.py`.** * The entire universe of the ecosystem's state, orchestration, memory, and compute lives within this single artifact. This is a mathematical requirement to guarantee deterministic, zero-shot latent alignment across the swarm.

### 3. The Anti-CRUD Mandate & Strict Lexical Architecture

Legacy CRUD terminology flattens softmax distributions and introduces semantic drift.

* **Banned Terms:** `Create`, `Read`, `Update`, `Delete`, `Remove`, `Group`, `List`, `User`, `Data`, `Memory`, `Link`.
* **Required Paradigm:** State transitions are mapped using Judea Pearl’s Structural Causal Models (e.g., `Transmutation`, `DefeasibleCascade`, `StateMutationIntent`).
* **Categorical Suffixing:** Every schema ends in a strict topological contract:
  * `...Event` / `...Receipt`: Cryptographically frozen historical facts (Append-only).
  * `...Intent` / `...Task`: Authorized kinetic execution triggers.
  * `...Policy` / `...Contract` / `...SLA`: Rigid mathematical boundaries.
  * `...State` / `...Snapshot` / `...Manifest` / `...Profile`: Ephemeral or declarative N-dimensional coordinates.


### 4. Cryptographic Determinism

All models subclass `CoreasonBaseState`, enforcing `frozen=True` immutability. Arrays and sets are mathematically sorted during instantiation to guarantee deterministic canonical hashing (RFC 8785) across varying distributed environments.

## Cross-Language Ecosystem Integration (Polyglot Bindings)

Because `coreason-manifest` is the definitive "God Context" for the swarm, it strictly publishes pure, stateless data schema bindings to downstream language ecosystems:
* **TypeScript (`npm`)**: Auto-generated TS bounds published to `@coreason/coreason-manifest`.
* **Rust (`crates.io`)**: Strict Struct bindings generated via `cargo-typify` and published to `coreason-manifest`.
* **Python (`PyPI`)**: The core declarative `pydantic` models distributed natively as `coreason_manifest`.

These downstream bindings are mathematically proven to be stateless Anemic Domain Models, guaranteeing zero active logic bleed across network boundaries.

## Military-Grade Supply Chain Security

To ensure absolute institutional trust, the repository is aggressively hardened against supply-chain attacks:
* **Passive Execution Quarantine**: The code functions strictly as a pure data architecture (Hollow Data Plane), possessing zero active execution bounds.
* **OS-Level Egress Filtering**: Continuous Integration pipelines are guarded dynamically by `step-security/harden-runner`, instantly blocking unauthorized network socket allocations initiated by transient dependencies.
* **Continuous Threat Verification**: Every branch is aggressively audited by `Bandit`, `TruffleHog` (for hardcoded secrets), and `ClamAV` (for filesystem virus scanning).
* **Zero-Trust Release Pipelines**: All artifacts are OIDC strictly authenticated, cryptographic signed via Sigstore, and mapped with SLSA Level 3 guarantees + SPDX SBOMs.

## Repository Structure

```text
coreason_manifest/
├── .github/workflows/
│   ├── advanced-security.yml # Deep SAST, GitGuardian secrets, and ClamAV sweeps
│   ├── publish.yml           # Zero-Trust OIDC artifact publishing & Sigstore
│   └── security.yml          # OSV & Pip dependencies auditing
├── bindings/
│   ├── rust/                 # Cargo-typify stateless structs
│   └── typescript/           # json-schema-to-typescript ecosystem bounds
├── src/coreason_manifest/
│   ├── spec/
│   │   └── ontology.py       # THE GOD CONTEXT: All Pydantic models, TypeAliases, and Enums.
│   └── utils/
│       └── algebra.py        # Pure algebraic functors, matrix projections, and validation.
├── scripts/
│   └── universal_ontology_compiler.py  # Monolithic CI gate: architecture, AST bounds, reachability.
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

## Security

Please report vulnerabilities **privately** — do not open a public GitHub Issue.

See [`SECURITY.md`](./SECURITY.md) for our full security policy, response SLAs, and responsible disclosure process. For urgent matters, email [security@coreason.ai](mailto:security@coreason.ai).

## Contributing

This project follows [Conventional Commits](https://www.conventionalcommits.org/) to power automated release notes and changelogs via [Release Please](https://github.com/googleapis/release-please). All commit messages should follow the format:

```
<type>(<scope>): <description>
```

Examples: `feat(ontology): add SpatialKinematicState`, `fix(algebra): correct canonical hash ordering`.

## License and Copyright

This repository and its entire ontology are the intellectual property of **CoReason, Inc.**

Licensed under the **Prosperity Public License 3.0**.

* **Non-Commercial:** Free for research, experiments, and open-source non-commercial use.
* **Commercial:** Permitted for a strict 30-day trial period.

For full license details, see the `LICENSE` file. For commercial licensing exceptions or inquiries, please explicitly contact `license@coreason.ai` or `gowtham.rao@coreason.ai`.

*(Genesis Commit: Initialized per CoReason Clean Room Protocol PIP-001 on 2026-01-01).*
