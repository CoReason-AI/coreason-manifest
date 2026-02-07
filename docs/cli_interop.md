# CLI & Interop Layer

Coreason Manifest provides a dependency-free Command Line Interface (CLI) designed for introspection, visualization, and simulation of AI Agents defined in Python. This tool is intended for VS Code extensions, CI pipelines, and developers who need to interact with agent definitions without running the full application runtime.

## Overview

The `coreason` CLI operates on Python files that define an `AgentDefinition`, `ManifestV2`, or `AgentBuilder`. It dynamically loads the target file, extracts the agent object, and performs the requested action.

**Key Features:**
- **Zero Runtime Dependencies:** Built using standard library `argparse` to keep the kernel lightweight.
- **Standard Output Protocol:** All commands support structured output (JSON or NDJSON) to `stdout`. Logs and debug information are sent to `stderr`.
- **Dynamic Loading:** Supports loading agents from relative file paths and automatically handles `AgentBuilder.build()`.

## Installation

The CLI is included with the `coreason_manifest` package.

```bash
# If installed via pip/poetry
coreason --help
```

## Usage

The general syntax is:

```bash
coreason <command> <reference> [options]
```

### The Reference Format

The `<reference>` argument tells the CLI where to find the agent definition. It follows the format:

```
path/to/file.py:variable_name
```

- **`path/to/file.py`**: The relative or absolute path to the Python file.
- **`variable_name`**: The name of the variable holding the `ManifestV2` or `AgentBuilder` instance.
  - If omitted (e.g., `path/to/file.py`), the CLI defaults to looking for a variable named `agent`.

### Commands

#### 1. Inspect (`inspect`)

Dumps the full JSON representation of the agent manifest. This is useful for debugging serialization or feeding the definition into other tools.

```bash
coreason inspect examples/my_agent.py:agent
```

**Output:**
- Pretty-printed JSON to `stdout`.

#### 2. Visualization (`viz`)

Generates a Mermaid.js diagram of the agent's workflow.

```bash
# Output raw Mermaid syntax
coreason viz examples/my_agent.py:agent

# Output JSON wrapper (useful for machine parsing)
coreason viz examples/my_agent.py:agent --json
```

**Output:**
- Mermaid graph syntax (e.g., `graph TD ...`).

#### 3. Run Simulation (`run`)

Simulates the execution of the agent's workflow locally. This command iterates through the defined steps and emits events.

**Options:**
- `--inputs <json_string>`: JSON string representing the input arguments for the workflow.
- `--mock`: If set, the CLI will use the `generate_mock_output` utility to synthesize realistic outputs for `AgentStep`s based on their output schema.

```bash
coreason run examples/my_agent.py:agent --inputs '{"query": "Hello"}' --mock
```

**Output Protocol (NDJSON):**
The `run` command emits Newline Delimited JSON (NDJSON) events to `stdout`.

1. **Step Start:**
   ```json
   {"type": "step_start", "step_id": "step_1", "capability": "MyAgent"}
   ```

2. **Step Output:**
   ```json
   {"type": "step_output", "step_id": "step_1", "output": {...}}
   ```

Consumers should read `stdout` line-by-line.

#### 4. Canonical Hashing (`hash`)

Calculates the canonical hash of an agent definition. This ensures that the agent's identity can be verified across different systems and environments.

**Options:**
- `--json`: Output a JSON object containing the hash and algorithm metadata.

**Example:**

```bash
# Default (text output)
coreason hash examples/my_agent.py:agent
# Output: sha256:8f434346648f6b96df89dda901c5176b10a6d83961dd3c1ac88b59b2dc327aa4

# JSON output
coreason hash examples/my_agent.py:agent --json
# Output: {"hash": "sha256:...", "algorithm": "sha256"}
```

**Behavior:**
- **Strict Canonicalization:** The command loads the agent definition and computes the hash using the kernel's native `compute_hash()` method, ensuring consistency with internal validation logic.
- **Verification:** Useful for CI/CD pipelines to verify that an agent has not been tampered with before deployment.

## Edge Cases & Limitations

- **File Paths:** The loader adds the file's directory to `sys.path` to support relative imports within the module.
- **Builder Pattern:** If the target variable is an instance of `AgentBuilder`, the CLI automatically calls `.build()` to get the `ManifestV2`.
- **Errors:** All errors (file not found, syntax error, invalid type) are printed to `stderr`, and the process exits with code `1`.
