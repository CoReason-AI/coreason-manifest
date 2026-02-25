# CLI Reference

The `coreason` CLI provides tools for creating, running, inspecting, and visualizing agents.

## Installation

The CLI is installed automatically with the package:

```bash
pip install coreason-manifest
```

## Commands

### `init`

Scaffolds a new agent project with a production-ready directory structure.

```bash
coreason init <project_name>
```

**What it does:**
1. Creates a directory named `<project_name>`.
2. Generates `agent.py` with a "Hello World" agent using `AgentBuilder` best practices.
3. Configures VS Code settings (`.vscode/launch.json`) for immediate "F5" debugging.
4. Adds `README.md` and `.gitignore`.

**Example:**
```bash
coreason init my_agent
cd my_agent
# Open in VS Code and press F5 to run!
```

---

### `run`

Simulates an agent execution locally.

```bash
coreason run <reference> [--inputs <json>] [--mock]
```

**Arguments:**
* `<reference>`: Path to the agent object (e.g., `agent.py:agent`).
* `--inputs`: JSON string of input data (default: `{}`).
* `--mock`: Enable mock output generation (simulated execution without LLM calls).

**Example:**
```bash
coreason run agent.py:agent --mock --inputs '{"name": "Alice"}'
```

---

### `viz`

Generates a Mermaid graph of the agent's workflow topology.

```bash
coreason viz <reference> [--json]
```

**Arguments:**
* `<reference>`: Path to the agent object.
* `--json`: Output as a JSON object wrapping the Mermaid string (useful for tools).

**Example:**
```bash
coreason viz agent.py:agent
```

---

### `inspect`

Outputs the full JSON representation of the agent manifest.

```bash
coreason inspect <reference>
```

**Example:**
```bash
coreason inspect agent.py:agent
```

---

### `validate`

Validates a static agent definition file (YAML or JSON) against the strict CoReason schema.

This command is crucial for CI/CD pipelines to ensure that manifest files committed to the repository are structurally correct and adhere to the policy before they are deployed or run.

```bash
coreason validate <path_to_file> [--json]
```

**Arguments:**
* `<path_to_file>`: Path to the `.yaml`, `.yml`, or `.json` file to validate.
* `--json`: If the file is valid, output the full validated JSON model to stdout. This is useful for canonicalizing input (e.g., converting YAML to JSON) or piping to other tools.

**Supported Schemas:**
*   **ManifestV2:** Detected automatically if the file contains `apiVersion: coreason.ai/v2`. This validates the entire recipe, including metadata, definitions, and workflows.
*   **AgentDefinition:** Fallback if no `apiVersion` is present. Validates a single Agent object.

**Output:**
*   **Success:** Prints `✅ Valid Agent: <Name> (v<Version>)` and exits with code 0.
*   **Failure:** Prints `❌ Validation Failed:` followed by a detailed list of errors (Field Path -> Error Message) and exits with code 1.

**Examples:**

*Validate a YAML file:*
```bash
coreason validate agent.yaml
# Output: ✅ Valid Agent: ResearchBot (v1.0.0)
```

*Validate and export as canonical JSON:*
```bash
coreason validate agent.yaml --json > agent.json
```

*Validation Failure:*
```bash
coreason validate invalid.json
# Output:
# ❌ Validation Failed:
#   • metadata -> name: Field required
#   • workflow -> start: Input should be a valid string
```

---

### `hash`

Computes the canonical hash of an agent for audit and integrity purposes.

```bash
coreason hash <reference>
```
