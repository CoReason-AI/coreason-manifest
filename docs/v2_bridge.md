# V2 Loader Bridge

The **V2 Loader Bridge** is the mechanism that connects the human-friendly **V2 Canonical YAML** format with the strict, machine-optimized **V1 Runtime Engine**.

It allows developers to write manifests in the concise V2 YAML format and immediately execute them on the existing V1 engine without waiting for a full runtime rewrite.

## Components

The bridge consists of three main modules located in `src/coreason_manifest/v2/`:

1.  **Compiler** (`compiler.py`): Transforms the implicit "Linked List" topology of V2 into the explicit "Graph" topology of V1.
2.  **I/O** (`io.py`): Handles loading and dumping of V2 YAML files. It supports **recursive multi-file composition** (via `$ref`) and enforces secure path resolution.
*   **Adapter** (`adapter.py`): Converts a loaded V2 `ManifestV2` object into a V1 `RecipeManifest` ready for execution, mapping Interface, State, and Policy configurations.
4.  **Resolver** (`resolver.py`): A helper module used by the loader to securely resolve file paths against a root "Jail" directory.

## State Mapping Logic

The Adapter performs intelligent mapping between V2 and V1 state configurations:

*   **Schema**: The JSON Schema defined in V2 (`state.schema`) is copied directly to the V1 recipe.
*   **Persistence**: V2 uses a `backend` field (e.g., "memory", "redis"), while V1 uses a binary `persistence` mode ("ephemeral", "persistent").
    *   `backend: "memory"` or `"ephemeral"` (or `None`) -> `persistence: "ephemeral"`
    *   Any other value (e.g., `"redis"`, `"sql"`, `"persistent"`) -> `persistence: "persistent"`

## Usage

### Loading and Executing a V2 Manifest

To run a V2 YAML file, you use the `load_from_yaml` function. This function automatically handles recursive imports and security checks.

```python
from pathlib import Path
from coreason_manifest.v2.io import load_from_yaml
from coreason_manifest.v2.adapter import v2_to_recipe

# 1. Load V2 Manifest (Human Friendly)
# By default, this resolves imports relative to the file's directory.
v2_manifest = load_from_yaml("my_workflow.v2.yaml")

# 2. Convert to V1 Recipe (Machine Optimized)
recipe = v2_to_recipe(v2_manifest)

# 3. The 'recipe' object is now a standard RecipeManifest
# compatible with the coreason-maco engine.
print(f"Loaded Recipe: {recipe.name} (ID: {recipe.id})")
print(f"Policy: {recipe.policy.max_retries} retries")
print(f"Topology has {len(recipe.topology.nodes)} nodes.")
```

## Multi-File Composition

The V2 Loader supports composing complex manifests from multiple files using the standard `$ref` syntax within the `definitions` section.

### Example

**`tools.yaml`** (A fragment defining a tool):
```yaml
id: weather-tool
name: Weather Tool
uri: mcp://weather.com
risk_level: safe
description: Get weather info
```

**`main.yaml`** (The root manifest):
```yaml
apiVersion: coreason.ai/v2
kind: Agent
metadata:
  name: Weather Agent
definitions:
  # Import the tool definition from an external file
  my_tool:
    $ref: "./tools.yaml"
workflow:
  start: step1
  steps:
    step1:
      type: agent
      id: step1
      agent: some-agent
      # ...
```

When `load_from_yaml("main.yaml")` is called, the loader recursively resolves `./tools.yaml` and injects its content into `definitions.my_tool`.

## Security & Safety

To prevent security vulnerabilities and infinite loops, the loader enforces strict constraints:

### 1. The Jail (Root Directory)
To prevent **Path Traversal Attacks**, the loader enforces a "Jail" constraint. By default, the root of the jail is the parent directory of the initial file being loaded.

*   All references (`$ref`) must resolve to a path **inside** this root directory.
*   Attempts to reference files outside the root (e.g., `../sensitive_file.txt`) will raise a `ValueError`.

You can explicitly set the root directory:

```python
# Enforce that all imports must be within /safe/base/dir
manifest = load_from_yaml(
    "project/main.yaml",
    root_dir="/safe/base/dir"
)
```

### 2. Cycle Detection
The loader tracks visited paths during recursion. If a circular dependency is detected (e.g., A imports B, and B imports A), a `RecursionError` is raised immediately.

## Compiler Logic

The compiler performs several transformations:

*   **Node Conversion**:
    *   `AgentStep` -> `AgentNode`
    *   `LogicStep` -> `LogicNode`
    *   `CouncilStep` -> `LogicNode` (with `council_config`)
    *   `SwitchStep` -> `LogicNode` (generates routing logic)
*   **Edge Generation**:
    *   `step.next` -> `Edge`
    *   `SwitchStep.cases` -> `ConditionalEdge` (with generated keys)
*   **Validation**: Ensures all referenced steps exist, preventing "dangling pointers".

### Round-Trip Serialization

You can also programmatically create V2 manifests and dump them to YAML. The dumper ensures that `apiVersion`, `kind`, and `metadata` appear at the top of the file.

```python
from coreason_manifest.v2.io import dump_to_yaml

yaml_str = dump_to_yaml(v2_manifest)
print(yaml_str)
```
