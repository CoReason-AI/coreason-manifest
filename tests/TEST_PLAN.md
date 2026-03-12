# Testing Strategy

## Goal
Increase code coverage for `src/coreason_manifest/spec/ontology.py` focusing on property methods and validators which currently sit untested (lines 133-137, 221-227, 258-262, 751, 780, 850-857, etc.).

## Methodology
1. Implement a new test suite specifically targeting specific blocks of code currently untouched.
2. The file will be named `tests/contracts/test_ontology_validators.py`.
3. The tests will encompass the following areas:
    - `RiskLevelPolicy.weight` (lines 133-137)
    - The `_cached_hash` caching mechanism on `CoreasonBaseState` (lines 221-227).
    - `SpatialCoordinateState` limits testing x and y boundaries (lines 258-262).
    - Byzantine Fault Tolerance validators enforcing mathematically rigorous size bounds.
    - Quorum rules validator.
    - Violation action "smooth_decay" constraints.

## Constraints
All code produced must conform completely to the constraints described in `AGENTS.md`. Tests must utilize valid Pydantic models obeying strictly bounded, deterministic rules with mathematically exact logic.
