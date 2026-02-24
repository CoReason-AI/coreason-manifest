# Developer Tools: The CLI

The `coreason` CLI (`src/coreason_manifest/cli.py`) provides essential utilities for introspection and validation. It allows developers to work with manifest files without needing to write Python scripts.

---

## `coreason validate`

This command reads a manifest file (JSON or YAML) and performs strict static analysis.

```bash
coreason validate my_agent.json
```

**What it checks:**
1.  **Schema Validity:** Does it conform to the Pydantic models (`GraphFlow`, `AgentNode`)?
2.  **Topology Integrity:** Are there orphaned nodes? Do edges reference non-existent IDs?
3.  **AST Safety:** Are the edge conditions safe Python expressions?
4.  **Governance Compliance:** (If configured) Does it violate risk policies?

If the manifest is valid, it exits with `0`. If not, it prints a detailed list of errors to `stderr` and exits with `1`.

---

## `coreason visualize`

This command takes a static manifest file and outputs a diagram representation.

```bash
coreason visualize my_agent.json > graph.mermaid
```

**Output Formats:**
*   **Mermaid (Default):** Outputs Mermaid.js markdown syntax, compatible with GitHub and most documentation tools.
*   **React Flow (Future):** Outputs a JSON payload for the React frontend (see Visualizer docs).

This allows you to "see" the structure of your agent before you run it.
