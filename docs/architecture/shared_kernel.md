# The Shared Kernel Architecture

## The Principle of "Passive Definition, Active Execution"

The core architectural tenet of `coreason-manifest` is the strict separation between definition and execution. This package serves as a **passive definition** layer—it describes the *What* without ever touching the *How*.

When defining a cognitive workflow, the manifest specifies the blueprint:
*   The Directed Acyclic Graph (DAG) of nodes.
*   The configuration of each cognitive engine.
*   The error recovery policies and governance rules.

However, the manifest itself contains no logic to execute these definitions. It does not know how to call an LLM API, connect to a vector database, or handle network retries. This "dumb" nature is intentional. By remaining passive, the manifest guarantees that the definition of a system is stable, verifiable, and completely independent of the volatile runtime environment.

## Decoupling from Runtimes

This architectural separation is critical for the stability and portability of the CoReason ecosystem. By decoupling the manifest from the execution runtime, we achieve several key benefits:

*   **Runtime Independence:** The exact same manifest object can be consumed by entirely different execution engines. A heavy-duty production orchestrator can execute the graph with full parallelism, while a lightweight local runner can execute it sequentially for debugging.
*   **Tooling Interoperability:** Visualization tools, linters, and governance dashboards can import and analyze the manifest structure without needing to install heavy runtime dependencies like LangChain, OpenAI SDKs, or MCP libraries.
*   **Testing & Validation:** Because the manifest is purely data, it can be validated statically. CI/CD pipelines can verify the integrity of a workflow definition without spinning up a complex execution environment.

## Language Agnosticism via JSON Schema

Although `coreason-manifest` is implemented in Python using Pydantic, its design philosophy is language-agnostic. The strict adherence to `CoreasonModel` ensures that every definition can be flawlessly exported to standard JSON Schema.

This capability allows for seamless cross-language interoperability:
*   **Frontend Integration:** A React or Vue frontend can consume the JSON Schema to generate dynamic forms or visual editors for cognitive workflows, ensuring that the UI always matches the backend definition.
*   **Backend Flexibility:** A high-performance backend written in Go, Rust, or Java can ingest and validate manifest files using the same schema, guaranteeing that the system definition is consistent across the entire stack.

By prioritizing this level of rigor and separation, `coreason-manifest` ensures that the cognitive architecture remains robust, adaptable, and future-proof.
