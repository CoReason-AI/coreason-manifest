# Generative Solvers & Strategies

Coreason V2 introduces advanced autonomous planning capabilities via the `GenerativeNode`. By decoupling the "What" (Goal) from the "How" (Solver), we enable the runtime to switch between different cognitive architectures without changing the manifest.

## Solver Configuration (`SolverConfig`)

The behavior of a `GenerativeNode` is governed by its `solver` configuration.

```python
class SolverConfig(CoReasonBaseModel):
    strategy: SolverStrategy = Field(SolverStrategy.STANDARD, ...)
    depth_limit: int = Field(3, ...)
    n_samples: int = Field(1, ...)        # Council Size
    diversity_threshold: float | None = Field(0.3, ...)  # Ensemble Diversity
    enable_dissenter: bool = Field(False, ...)           # Devil's Advocate
    consensus_threshold: float | None = Field(0.6, ...)  # Voting Quorum
    beam_width: int = Field(1, ...)       # LATS
    max_iterations: int = Field(10, ...)  # LATS
    aggregation_method: Literal[...] | None = Field(None, ...) # SPIO-E
```

## Strategies

### 1. Standard (ROMA)
*   **Enum**: `standard`
*   **Description**: Simple Recursive Decomposition. The agent breaks down the goal into sub-tasks depth-first.
*   **Best For**: Well-defined tasks with clear steps.
*   **Key Params**: `depth_limit`.

### 2. Tree Search (LATS)
*   **Enum**: `tree_search`
*   **Description**: Language Agent Tree Search. Combines reasoning with Monte Carlo Tree Search (MCTS). It explores branching paths, simulates outcomes, and back-propagates feedback to select the best path.
*   **Best For**: Complex reasoning, coding tasks, or logic puzzles where backtracking is necessary.
*   **Key Params**:
    *   `beam_width`: How many children to expand per node.
    *   `max_iterations`: The "Search Budget" (total simulations).
    *   `depth_limit`: Maximum tree depth.

### 3. Ensemble Meta-Strategy (SPIO / Council)
*   **Enum**: `ensemble`
*   **Description**: Sequential Plan Integration and Optimization.
    *   **SPIO-S (Single)**: If `n_samples=1`. Generates a single high-quality plan.
    *   **SPIO-E (Ensemble)**: If `n_samples > 1`. Generates multiple candidate strategies in parallel and selects the best one (or merges them) to maximize robustness.
    *   **Council Mode**: Enables advanced consensus features:
        *   **Diversity**: Forces candidates to be distinct (Jaccard distance > `diversity_threshold`).
        *   **Dissenter**: Adds a "Devil's Advocate" critique step (`enable_dissenter=True`).
        *   **Consensus**: Requires a super-majority to ratify a plan (`consensus_threshold`).
*   **Best For**: High-stakes planning where reliability is paramount.
*   **Key Params**:
    *   `n_samples`: Council size (number of plans).
    *   `diversity_threshold`: Minimum uniqueness per plan.
    *   `enable_dissenter`: Activate adversarial review.
    *   `consensus_threshold`: Vote percentage required to pass.
    *   `aggregation_method`: How to combine results (`best_of_n`, `majority_vote`, `weighted_merge`).

## Examples

### LATS Configuration
```python
node = GenerativeNode(
    id="coding-task",
    goal="Implement a thread-safe LRU cache",
    output_schema={...},
    solver=SolverConfig(
        strategy="tree_search",
        beam_width=3,      # Explore 3 options at each step
        max_iterations=50, # Allow 50 total simulations
        depth_limit=5
    )
)
```

### SPIO-E Configuration
```python
node = GenerativeNode(
    id="critical-planning",
    goal="Develop a migration strategy for prod DB",
    output_schema={...},
    solver=SolverConfig(
        strategy="ensemble",
        n_samples=5,                     # Generate 5 distinct plans
        aggregation_method="best_of_n"   # Pick the highest scored one
    )
)
```
