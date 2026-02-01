# Simulation Architecture

This document details the simulation architecture for the `coreason-manifest` library, designed to ensure compatibility with standard evaluation tools and the Agent Trajectory Interchange Format (ATIF).

## Agent Trajectory Interchange Format (ATIF)

To enable standardized evaluation and interoperability with tools like Harbor and LangSmith, we adopt the ATIF structure.

### SimulationStep

The atomic unit of execution in a simulation is the `SimulationStep`. It captures the full causal chain of an agent's reasoning for a single step.

- **step_id** (`UUID`): Unique identifier for the step.
- **timestamp** (`datetime`): Execution timestamp.
- **type** (`StepType`): Type of the step (`interaction` or `system_event`).
- **node_id** (`str`): The graph node executed.
- **inputs** (`Dict[str, Any]`): Snapshot of entry state.
- **thought** (`Optional[str]`): The Chain-of-Thought reasoning.
- **action** (`Optional[Dict[str, Any]]`): Tool calls or API requests.
- **observation** (`Optional[Dict[str, Any]]`): Tool outputs.
- **snapshot** (`Dict[str, Any]`): Full copy of the graph state at the completion of this step.

### SimulationTrace

A trace represents a full execution session of an agent.

- **trace_id** (`UUID`): Unique trace identifier.
- **agent_version** (`str`): Agent SemVer version.
- **steps** (`List[SimulationStep]`): List of execution steps.
- **outcome** (`Dict[str, Any]`): Final result.
- **metrics** (`SimulationMetrics`): Execution metrics (e.g., token usage, cost).

### SimulationMetrics

Metrics gathered during simulation.

- **turn_count** (`int`): Number of turns.
- **total_tokens** (`Optional[int]`): Total tokens used.
- **cost_usd** (`Optional[float]`): Total cost in USD.
- **duration_ms** (`Optional[float]`): Total duration in milliseconds.

## GAIA-Compliant Scenarios

We define scenarios that allow for rigorous, standardized benchmarking, aligned with the GAIA benchmark structure.

### SimulationScenario

- **id** (`str`): Unique identifier for the scenario.
- **name** (`str`): Name of the scenario.
- **objective** (`str`): The prompt/task instructions.
- **difficulty** (`int`): Difficulty level (1-3).
- **expected_outcome** (`Any`): The ground truth for validation.
- **validation_logic** (`ValidationLogic`): Logic used to validate the outcome (`exact_match`, `fuzzy`, `code_eval`).

## Simulation Configuration

To enable reproducible and configurable simulations, we define standard configuration objects for the Simulator service.

### SimulationRequest

The standard payload for triggering a simulation.

- **scenario** (`SimulationScenario`): The scenario to run.
- **profile** (`AdversaryProfile`): Configuration for the adversary (Red Team).
- **chaos_config** (`ChaosConfig`): Configuration for infrastructure chaos injection.

### AdversaryProfile

Defines the strategy and identity of the adversary agent.

- **name** (`str`): Name of the profile.
- **goal** (`str`): The objective of the adversary.
- **strategy_model** (`str`): The model used for strategic planning (e.g., "claude-3-opus").
- **attack_model** (`str`): The model used for generating attacks (e.g., "llama-3-uncensored").
- **persona** (`Optional[Persona]`): The full persona definition (name, description, directives) for the adversary.

### ChaosConfig

Defines parameters for injecting simulated infrastructure faults.

- **latency_ms** (`int`): Artificial latency in milliseconds.
- **error_rate** (`float`): Probability of random errors (0.0 to 1.0).
- **noise_rate** (`float`): Probability of noise injection (0.0 to 1.0).
- **token_throttle** (`bool`): Whether to simulate token rate limiting.
- **exception_type** (`str`): The type of exception to raise (default: "RuntimeError").
