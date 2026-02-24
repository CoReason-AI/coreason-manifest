# Capabilities: Defining Actionable Interfaces

An agent's power comes from its ability to interact with the world. In `coreason-manifest`, these capabilities are strictly defined as **Tools**.

The `ToolCapability` schema (`src/coreason_manifest/spec/core/tools.py`) defines the *contract* of a tool—its name, its inputs, its outputs, and its risk profile—not the Python code that executes it. This separation ensures that the manifest can be statically analyzed for safety before any code runs.

---

## `ToolCapability` Schema

Every actionable capability (whether a web search, a database query, or a calculator) is represented by a `ToolCapability` object.

```python
class ToolCapability(CoreasonModel):
    name: ToolID
    risk_level: RiskLevel = RiskLevel.STANDARD
    description: str | None
    requires_approval: bool = False
    url: HttpUrl | None
```

*   **`name`**: The unique identifier used by the LLM to call the tool.
*   **`risk_level`**: The critical classification (see below).
*   **`requires_approval`**: A mandatory Human-in-the-Loop flag. If `True`, the runtime halts execution and awaits authorization before calling the tool.

### Input/Output Schema
Although not shown in the base class, strict implementations of `ToolCapability` require an OpenAPI-compliant or JSON Schema definition for inputs and outputs. This ensures the LLM knows exactly how to format arguments.

---

## `ToolPack` Schema

A `ToolPack` is a bundle of logically related tools, designed for reusability. For example, a "Research Pack" might contain `web_search`, `pdf_reader`, and `citation_checker`.

*   **`namespace`**: A prefix applied to all tools in the pack (e.g., `research.web_search`) to prevent naming collisions.
*   **`tools`**: A list of `ToolCapability` objects provided by this pack.
*   **`env_vars`**: A strict list of environment variables required for the pack to function (e.g., `GOOGLE_API_KEY`).

---

## `RiskLevel` Classification

The system enforces a strict taxonomy of risk. This allows Governance Policies to filter which tools are safe to execute in a given context.

| Level | Description | Examples |
| :--- | :--- | :--- |
| **`SAFE`** | Read-only, local, deterministic. Cannot cause side effects or leak data. | `calculator`, `regex_search`, `format_date`. |
| **`STANDARD`** | Read-only network calls or low-impact state changes. | `web_search`, `send_email_draft`, `read_database`. |
| **`CRITICAL`** | Irreversible state changes or high-security actions. | `execute_python_code`, `drop_table`, `transfer_funds`. |

**Governance Tie-In:**
If a `Governance` policy sets `max_risk_level=STANDARD`, any tool marked as `CRITICAL` is automatically disabled. The runtime will reject the call before execution begins.

---

## `Dependency` Schema

Tools often require external libraries or services. The `Dependency` schema allows a tool to declare its requirements explicitly.

```python
class Dependency(CoreasonModel):
    name: str
    version: str | None
    manager: Literal["pip", "npm", "apt", "mcp"]
```

*   **`manager`**: Specifies how the dependency is sourced.
    *   `pip`: Python package.
    *   `npm`: Node.js package.
    *   `apt`: System package (e.g., `ffmpeg`).
    *   `mcp`: External Model Context Protocol resource.

This allows the runtime environment (or a container builder) to provision the correct dependencies before the agent starts.
