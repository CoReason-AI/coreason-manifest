## Part VII: Applied Research & Contribution

### 7.1 The Prosperity Public License 3.0

The CoReason Manifest and its accompanying ontology are distributed under the Prosperity Public License 3.0. For university researchers, PhD candidates, and non-profit AI safety organizations, this license guarantees that the repository is completely free for academic research, open-source experimentation, and non-commercial utilization. Commercial deployment is strictly isolated to a 30-day trial period without requiring a separate enterprise license.

### 7.2 Stateless Polyglot Bindings

Because the `ontology.py` file operates as the definitive "God Context," it must safely export its mathematical constraints to downstream execution engines across language ecosystems without introducing active logic bleed.

The manifest natively generates and publishes strict, stateless polyglot bindings. For frontend interaction and UI projection, TypeScript boundary definitions are auto-generated and distributed via `npm` under `@coreason/coreason-manifest`. For core hardware orchestration and theorem proving, strict `Struct` bindings are generated via `cargo-typify` and published to Rust's package registry (`crates.io`) under `coreason-manifest`. The native Python declarative models are distributed via `PyPI`. These bindings are mathematically proven to act as Anemic Domain Models, preserving the Hollow Data Plane architecture across network boundaries.

### 7.3 Mandatory Local Verification and CI/CD Gates

To ensure the Shared Kernel remains mathematically sound, any proposed architectural mutation to the ontology must clear a highly rigid local verification sequence before reaching the CI/CD pipeline.

Researchers expanding the ontology must use the `uv` package manager and pass the following architectural gates:
1.  **Strict Linting:** The codebase is subject to severe formatting validation via `uv run ruff format .` and `uv run ruff check . --fix`.
2.  **Type Checking:** `uv run mypy src/ tests/` enforces absolute type rigidity across all class and model definitions.
3.  **Behavioral Contracts:** `uv run pytest` executes the test suite, where the repository CI/CD enforces a strict 95% behavioral test coverage floor to prevent untested theoretical models from entering the active manifest.
