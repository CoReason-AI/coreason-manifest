# Reasoning Engines: The Discriminated Union of Thought

The `coreason-manifest` library recognizes that "reasoning" is not a monolithic concept. A simple Q&A task requires a vastly different cognitive strategy than a complex codebase refactor or a multi-step research plan.

To address this, the `ReasoningConfig` is defined as a **Strictly Typed Discriminated Union**.

```python
ReasoningConfig = Annotated[
    StandardReasoning
    | AdaptiveReasoning
    | TreeSearchReasoning
    | ...
    Field(discriminator="type")
]
```

This guarantees that an `AgentNode` can only be bound to a valid, pre-defined cognitive strategy. These are **configuration schemas**—blueprints for *how* to think—not the execution code itself.

---

## 1. Standard & Fast Paths

### `StandardReasoning` (`type: standard`)
The default schema for direct, linear LLM interactions. It configures a zero-shot or few-shot Chain-of-Thought (CoT) process.
*   **`thoughts_max`**: Maximum number of internal reasoning steps.
*   **`min_confidence`**: Threshold score required to output a final answer.

### `FastPathConfig`
This schema allows an agent to bypass heavy reasoning for deterministic or cached semantic routes.
*   **`caching`**: Whether to utilize semantic cache (e.g., Redis).
*   **`timeout_ms`**: Strict latency budget for "System 1" responses.

---

## 2. Advanced Cognitive Topologies

### `AdaptiveReasoning` (`type: adaptive`)
Schema for dynamic compute allocation. The agent expands its reasoning trace until confidence is met or the budget is exhausted.
*   **`max_compute_tokens`**: The "thinking budget."
*   **`verifier_model`**: The external judge model used to score intermediate thoughts.
*   **`scaling_mode`**: `depth_first` vs. `breadth_first`.

### `AttentionReasoning` (`type: attention`)
Defines "System 2 Attention" (S2A). The agent filters and rewrites input context to maximize signal-to-noise ratio before reasoning begins.
*   **`attention_mode`**: `rephrase` (rewrite query) or `extract` (pull key facts).
*   **`focus_model`**: A smaller, faster model used solely for context sanitization.

### `BufferReasoning` (`type: buffer`)
Schema for "Buffer of Thoughts" (BoT). Retrieves and stores thought templates to solve routine problems efficiently.
*   **`max_templates`**: Number of similar past solutions to retrieve.
*   **`learning_strategy`**: `read_only` vs. `append_new` (save successful traces back to the buffer).

### `TreeSearchReasoning` (`type: tree_search`)
Configures multi-step, branching thought processes (e.g., MCTS or LATS).
*   **`depth`**: Maximum search tree depth.
*   **`branching_factor`**: Number of potential next steps to explore per node.
*   **`simulations`**: Monte Carlo Tree Search simulation budget.

### `DecompositionReasoning` (`type: decomposition`)
Schema for breaking a complex problem into atomic sub-tasks (e.g., ReAct pattern or "Atom of Thoughts").
*   **`decomposition_breadth`**: Maximum parallel sub-tasks.
*   **`contract_every_steps`**: Frequency of re-planning/consolidation.

---

## 3. Consensus & Red Teaming

### `CouncilReasoning` (`type: council`)
Schema for intra-node multi-persona consensus. The agent simulates a "boardroom" of different personas debating a topic.
*   **`personas`**: List of distinct system prompts (e.g., "Skeptic", "Optimist").
*   **`voting_mode`**: `unanimous`, `majority`, or `weighted`.

### `EnsembleReasoning` (`type: ensemble`)
Schema for multi-model consensus. Executes parallel queries across different LLMs and uses a hybrid fast/slow path to verify agreement.
*   **`fast_comparison_mode`**: `embedding` (vector cosine) or `lexical` (token overlap).
*   **`agreement_threshold`**: Score above which results are considered identical.
*   **`judge_model`**: The "Supreme Court" model that resolves conflicts if the ensemble disagrees.

### `RedTeamingReasoning` (`type: red_teaming`)
Schema for adversarial self-correction loops. The agent proactively attacks its own draft response to find weaknesses.
*   **`attacker_model`**: The model configured to generate attack vectors.
*   **`attack_strategy`**: `crescendo` (escalation), `refusal_suppression` (jailbreak), etc.
*   **`success_criteria`**: Natural language definition of a successful break (e.g., "PII Leakage").

---

## 4. Execution Topologies

### `ComputerUseReasoning` (`type: computer_use`)
Specialized schema for "Operator Agents" that control desktop environments.
*   **`coordinate_system`**: `absolute_px` vs. `normalized_0_1` (for screen size portability).
*   **`allowed_actions`**: Strict allow-list of permitted GUI operations (`click`, `type`, `screenshot`).
*   **`interaction_mode`**: `native_os` (OS events) vs. `browser_dom` (web selectors).

### `CodeExecutionReasoning` (`type: code_execution`)
Schema for agents that write and execute Python code in a sandboxed environment.
*   **`allow_network`**: Boolean flag to enable/disable external network access.
*   **`timeout_seconds`**: Hard execution limit to prevent infinite loops.

### `GraphReasoning` (`type: graph`)
Schema allowing a node to recursively execute a sub-graph (GraphRAG) as its reasoning engine.
*   **`graph_store`**: Identifier for the Knowledge Graph.
*   **`retrieval_mode`**: `local` (neighbor search) vs. `global` (community summaries).
*   **`max_hops`**: Traversal depth for local searches.
