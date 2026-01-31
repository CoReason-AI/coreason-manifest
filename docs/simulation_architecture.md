# Simulation Architecture

This document details the simulation architecture for the `coreason-manifest` library, designed to ensure compatibility with standard evaluation tools and the Agent Trajectory Interchange Format (ATIF).

## Agent Trajectory Interchange Format (ATIF)

To enable standardized evaluation and interoperability with tools like Harbor and LangSmith, we adopt the ATIF structure.

### SimulationStep

The atomic unit of execution in a simulation is the `SimulationStep`. It captures the full causal chain of an agent's reasoning for a single step.

- **step_id** (`UUID`): Unique identifier for the step.
- **timestamp** (`datetime`): Execution timestamp.
- **node_id** (`str`): The graph node executed.
- **inputs** (`Dict[str, Any]`): Snapshot of entry state.
- **thought** (`str`): The Chain-of-Thought reasoning.
- **action** (`Dict[str, Any]`): Tool calls or API requests.
- **observation** (`Dict[str, Any]`): Tool outputs.

### SimulationTrace

A trace represents a full execution session of an agent.

- **trace_id** (`UUID`): Unique trace identifier.
- **agent_version** (`str`): Agent SemVer version.
- **steps** (`List[SimulationStep]`): List of execution steps.
- **outcome** (`Dict[str, Any]`): Final result.
- **metrics** (`Dict[str, Any]`): Execution metrics (e.g., token usage, cost).

## GAIA-Compliant Scenarios

We define scenarios that allow for rigorous, standardized benchmarking, aligned with the GAIA benchmark structure.

### SimulationScenario

- **id** (`str`): Unique identifier for the scenario.
- **name** (`str`): Name of the scenario.
- **objective** (`str`): The prompt/task instructions.
- **difficulty** (`int`): Difficulty level (1-3).
- **expected_outcome** (`Any`): The ground truth for validation.
- **validation_logic** (`ValidationLogic`): Logic used to validate the outcome (`exact_match`, `fuzzy`, `code_eval`).
