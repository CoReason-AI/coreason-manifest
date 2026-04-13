# Substrate Projections in Neurosymbolic Architecture: Standardizing Execution Envelopes via the Model Context Protocol

## Abstract
As multi-agent neurosymbolic systems scale, the dichotomy between immutable schema definition (the data plane) and dynamic computational execution (the runtime plane) introduces significant orchestration friction. Large Language Models (LLMs) require standardized interfaces to invoke external deterministic solvers (e.g., Lean 4, ASP, SWI-Prolog). This paper details the architectural integration of the Model Context Protocol (MCP) as the universal execution substrate within a decentralized directed acyclic graph (DAG). We formalize the concept of "Substrate Projections"—the mechanical translation of rigid, highly constrained Pydantic geometries into dynamic, executable MCP tool definitions. By explicitly binding the schema boundaries established in prior epics to the MCP transport layer, we demonstrate how an orchestrator can natively discover, bound, and execute specialized mathematical kernels without compromising the cryptographic integrity of the zero-trust ledger.

---

## 1. Introduction: The Disconnect Between Schema and Execution
In advanced neurosymbolic architectures (circa 2026), the "Hollow Data Plane" acts as the immutable rules of physics. Through rigid schemas (e.g., Pydantic), it defines the exact structure a hypothesis or mathematical proof must take to be appended to the Merkle-DAG. However, schemas are passive; they define the *shape* of truth but do not *compute* it.

A connectionist model (LLM) cannot evaluate a Dependent Type Theory proof internally. It must rely on an external, C-backed kernel. Historically, connecting LLMs to external tools relied on fragmented, bespoke REST APIs or brittle prompt-based function calling, leading to high failure rates when managing complex mathematical environments.

The **Model Context Protocol (MCP)** has emerged as the universal standard for exposing remote and local tools to LLMs. MCP allows an orchestrator to dynamically mount external computational environments (like a Lean REPL or a Clingo solver) into the LLM's context window. This paper addresses the theoretical and structural mechanisms required to "project" our rigid Pydantic schema boundaries onto the dynamic MCP transport layer.

---

## 2. The Model Context Protocol (MCP) Substrate
MCP standardizes the lifecycle of tool discovery, parameter validation, and execution between a client (the LLM/Orchestrator) and a server (the environment hosting the tools).

In our architecture, the `coreason-manifest` must act as the bridge. It must not only define the schema for an `EpistemicLogicPremise` but also generate the exact MCP `Tool` specification required to evaluate that premise.

### 2.1 The Anatomy of an MCP Tool
An MCP tool consists of three primary components:
1.  **Name:** A rigid identifier (e.g., `execute_clingo_falsification`).
2.  **Description:** The natural language instruction injected into the LLM's context window dictating *when* to invoke the tool (the routing heuristic).
3.  **Input Schema:** A JSON Schema definition dictating the required parameters.

The architectural imperative is that the MCP `Input Schema` must be a flawless mechanical derivative of the underlying Pydantic schemas defined in the data plane. If the data plane enforces a 65,536-byte limit on ASP syntax, the MCP tool definition must inherently enforce that exact same geometric bound prior to tool invocation.

---

## 3. Substrate Projections: Bridging State and Action
To integrate the neurosymbolic triad (Lean 4, ASP, SWI-Prolog), the system must implement **Substrate Projections**. These are adapter algorithms that translate the static Pydantic premise definitions into dynamic MCP tool objects.

### 3.1 Projecting Dependent Type Theory (Lean 4)
The Lean 4 schema (`EpistemicLean4Premise`) requires a `formal_statement` and a `tactic_proof`.
The projection algorithm must compile an MCP Tool named `verify_lean4_theorem`. The tool's description must encompass the routing heuristics established in Epic 4 (e.g., "Use this tool to evaluate constructive mathematical proofs..."). The resulting JSON Schema payload sent to the MCP server must strictly mirror the field constraints of the `EpistemicLean4Premise`.

Crucially, the execution of this MCP tool is ephemeral. The tool executes the tactic script against the Lean kernel. The manifest's responsibility is to define how the *response* from this ephemeral execution (the verified status or the `failing_tactic_state`) is captured and permanently crystallized into the immutable `Lean4VerificationReceipt`.

### 3.2 Projecting Combinatorial Falsification (ASP)
When projecting `EpistemicLogicPremise` into an MCP tool (`execute_clingo_falsification`), the architecture must manage the computational boundaries of NP-hard search problems.

The projection must define an `input_schema` that accepts the raw `asp_program` string. More importantly, it must expose the `max_models` parameter defined in the Pydantic schema. By exposing this parameter through MCP, the LLM is constrained to request a strictly bounded execution space, preventing the remote constraint oracle from exhausting memory while searching for millions of satisfying assignments.

### 3.3 Projecting Deductive Traversal (SWI-Prolog)
The projection of `EpistemicPrologPremise` into an MCP tool (`execute_prolog_deduction`) requires handling both static knowledge bases and dynamic context.

The MCP tool must accept the `prolog_query` and the optional `ephemeral_facts`. The underlying system must merge these ephemeral clauses generated by the LLM with the static Knowledge Base (identified by `knowledge_base_cid`) before executing the backward-chaining resolution. The projection ensures that the LLM understands it is passing a query to a relational database rather than a generative model.

---

## 4. Executing the Orchestration Handoff
With the Substrate Projections defined, the macro-orchestration contracts must be updated to acknowledge the transport mechanism.

### 4.1 The Execution Substrate Directive
The `NeuroSymbolicHandoffContract` must be expanded to include an `execution_substrate` parameter. While `solver_protocol` dictates the mathematical logic (e.g., `lean4`), the `execution_substrate` dictates the physical transport path.

The orchestrator must know whether the Triad solver is hosted locally (e.g., via standard input/output `mcp_local`), on a remote cluster (e.g., via Server-Sent Events `mcp_remote`), or tightly bound via a Foreign Function Interface (`direct_ffi`). This explicitly separates the logical evaluation strategy from the infrastructural deployment topology.

---

## 5. Conclusion
The integration of the Model Context Protocol (MCP) completes the execution lifecycle of the neurosymbolic framework. By implementing Substrate Projections, the architecture mechanically translates the cryptographic, static boundaries of the Hollow Data Plane into dynamic, executable tool definitions for large language models. This alignment ensures that connectionist agents can natively invoke specialized deterministic kernels (Lean 4, ASP, Prolog) while the orchestrator retains absolute control over input geometries, memory bounds, and computational timeouts, thereby securing the execution envelope of the distributed swarm.