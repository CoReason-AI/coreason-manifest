# Architectural Guide & Principles for Runtime Developers

This document defines how a Runtime Engine (the "Executor") must behave to correctly interpret and maximize the capabilities of the `Coreason Manifest` Shared Kernel.

---

# Coreason Runtime Principles

**Target Audience:** Developers building execution engines (in Python, Node, Go, or Rust) that consume `coreason-manifest`.

### 1. The Principle of "Passive Definition, Active Execution"

**The Rule:** The Manifest is a static, passive declaration of intent. The Runtime is responsible for **all** side effects and operational limits.

*   **Manifest Responsibility:** Defines *what* an agent is and *what* it can do.
*   **Runtime Responsibility:**
    *   **Execution Loop:** Instantiates the LLM client, manages the context window, and executes tool calls.
    *   **Policy Enforcement:** The runtime must respect `PolicyConfig` definitions found in `recipe.py`. This includes enforcing `max_retries` for failed steps, `timeout_seconds` for global execution, and adhering to `execution_mode` (sequential vs. parallel).
    *   **Safety Interceptors:** Adhere to strict governance rules. If a tool is marked `risk_level: critical` or if the `PolicyConfig` forbids custom logic, the runtime must halt or reject execution accordingly.

### 2. The "Pre-Flight" Feasibility Check

**The Rule:** The runtime must validate the environment state against defined `Constraints` *before* attempting execution.

*   **The Component:** `Constraint` objects in `recipe.py` (e.g., `requirements` list in `RecipeDefinition`).
*   **Runtime Requirement:**
    1.  Before starting the graph or a specific node, the runtime must evaluate the `requirements` list using `RecipeDefinition.check_feasibility`.
    2.  It must resolve variables from the Blackboard (e.g., `data.row_count`) and apply the defined operator (`eq`, `gt`, `contains`).
    3.  If a `required: True` constraint fails, the runtime must abort execution immediately with the provided `error_message`.

### 3. The "Multiplexed Stream" Mandate (New in v0.21.0)

**The Rule:** The runtime must treat outputs as **named, concurrent streams**, not a single text pipe.

*   **The Component:** `StreamReference` and Lifecycle Events (`STREAM_START`, `NODE_STREAM`, `STREAM_END`) defined in `stream_lifecycle.md`.
*   **Runtime Requirement:**
    1.  **Identity:** Support `stream_id` to distinguish content (e.g., `stream_id="thinking"` vs `stream_id="default"`).
    2.  **Concurrency:** Allow agents to emit multiple streams simultaneously (e.g., streaming a Python script to a sandbox while streaming an explanation to the user).
    3.  **Lifecycle Emission:** The runtime must explicitly emit `STREAM_START` events (with `content_type`) before sending data chunks, and `STREAM_END` events when a stream closes.
    4.  **Backward Compatibility:** If no stream is specified by the agent, the runtime must default to `stream_id="default"` and `content_type="text/plain"`.

### 4. The Interception Layer (Middleware) (New in v0.21.0)

**The Rule:** The runtime must support standardized injection points for cross-cutting logic (PII, Toxicity, Audit).

*   **The Component:** `IRequestInterceptor` and `IResponseInterceptor` protocols defined in `middleware_extension_interfaces.md`.
*   **Runtime Requirement:**
    1.  **Context Creation:** For every execution, instantiate an immutable `InterceptorContext` containing the `request_id` and `start_time`.
    2.  **Request Pipeline:** Before the agent sees the input, pass the `AgentRequest` through all registered `IRequestInterceptor` implementations.
    3.  **Response Pipeline:** As the agent streams output, pass every `StreamPacket` through registered `IResponseInterceptor` implementations (e.g., to block toxic tokens in real-time).

### 5. Generative Provenance & Awareness (New in v0.21.0)

**The Rule:** The runtime must preserve and expose the metadata indicating *why* a workflow exists, especially if AI-generated.

*   **The Component:** `ManifestMetadata` fields in `definitions.py` (`generation_rationale`, `confidence_score`, `generated_by`, `original_user_intent`).
*   **Runtime Requirement:**
    *   If executing a dynamic/ephemeral manifest, the runtime logs must include the `generated_by` model ID and the `confidence_score`.
    *   This data must be persisted in the `SimulationTrace` to allow debugging why a specific workflow structure was hallucinated/generated.

### 6. Lazy Loading

**The Rule:** The runtime must support lazy loading of Skills, using vector-based semantic routing for discovery.

*   **The Component:** `SkillDefinition` in `skills.py`.
*   **Runtime Requirement:**
    *   Skills marked with `load_strategy: "lazy"` must not be loaded into the context window immediately.
    *   The runtime must index the `trigger_intent` field of these skills.
    *   During execution, the runtime should semantically query these intents and load the skill only when relevant to the current task.
    *   `trigger_intent` is mandatory for lazy skills to enable this routing.

### 7. The Graph State Blackboard & Routing Logic

**The Rule:** Execution is a Directed Cyclic Graph (DCG) where flow is determined by data, not just linear sequence.

*   **Data Structure:** The `RecipeDefinition` defines a `StateDefinition` schema for shared memory.
*   **Runtime Requirement:**
    *   **Router Execution:** When encountering a `RouterNode`, the runtime must evaluate the `input_key` against the Blackboard. It must strictly match the value to the `routes` map to determine the next node ID, falling back to `default_route` only if no match is found.
    *   **I/O Mapping:** Map global state variables to `AgentNode` inputs using `inputs_map`.
    *   **Persistence:** If `state.persistence` is set to `redis` or `postgres`, the runtime must serialize the Blackboard to external storage to support long-running or resumed sessions.

### 8. Standardized Simulation & Tracing

**The Rule:** The runtime must produce a standardized trace object, not just raw logs.

*   **The Component:** `SimulationTrace` and `SimulationStep` in `simulation_executor.py`.
*   **Runtime Requirement:**
    *   Every state transition must be recorded as a `SimulationStep`.
    *   The step must explicitly capture `thought` (reasoning), `action` (tool/router decision), `observation` (result), and a `snapshot` of the Blackboard context at that moment.
    *   This trace must be retrievable to replay or visualize the execution flow.

### 9. The Evaluator-Optimizer Loop (LLM-as-a-Judge)

**The Rule:** The runtime must natively support self-correction loops using the `EvaluatorNode`.

*   **The Component:** `EvaluatorNode` in `recipe.py`.
*   **Runtime Logic:**
    1.  **Execute Judge:** Call the `evaluator_agent_ref` with the content of `target_variable`.
    2.  **Parse Score:** Extract a normalized score (0.0 - 1.0) based on the `EvaluationProfile`.
    3.  **Route & Feedback:**
        *   If `score >= pass_threshold`: Transition to `pass_route`.
        *   If `score < pass_threshold`: Increment retry counter. Write the critique to `feedback_variable` and transition to `fail_route`.
    4.  **Feedback Injection:** When routing back to the generator, the runtime **must** append the content of `feedback_variable` to the prompt.

---

### Implementation Checklist for Runtime Developers

| Feature | Manifest Source | Runtime Action |
| :--- | :--- | :--- |
| **Multiplexed Streams** | `stream_lifecycle.md` | **NEW:** Emit `STREAM_START/END` events; support `stream_id` in chunks. |
| **Middleware** | `middleware_extension_interfaces.md` | **NEW:** Apply `IRequestInterceptor` and `IResponseInterceptor` chains. |
| **Generative Provenance** | `definitions.py` | **NEW:** Log `generation_rationale` and `confidence_score` from metadata. |
| **Pre-Flight Checks** | `recipe.py` -> `Constraint` | Evaluate `requirements` against context before execution using `check_feasibility`. |
| **Operational Policy** | `recipe.py` -> `PolicyConfig` | Enforce `timeout_seconds` and `max_retries`. |
| **Dynamic Routing** | `recipe.py` -> `RouterNode` | Switch execution path based on Blackboard variable values. |
| **Lazy Loading** | `skills.py` -> `SkillDefinition` | Index `trigger_intent` for vector search; load only when needed. |
| **Observability** | `simulation_executor.py` | Generate structured `SimulationStep` objects with state snapshots. |
| **Self-Correction** | `recipe.py` -> `EvaluatorNode` | Implement logic to parse "Score" and route based on threshold. |
