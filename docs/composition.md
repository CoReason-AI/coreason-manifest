# Secure Composition

The CoReason Manifest supports modular composition of Agents and Recipes using a **Secure Recursive Loader**. This architecture allows you to split large manifests into smaller, reusable files while enforcing strict security boundaries.

## The `$ref` Syntax

You can import definitions from external YAML files using the standard `$ref` syntax within the `definitions` block.

```yaml
definitions:
  my_tool:
    $ref: "./tools/search_tool.yaml"

  research_agent:
    $ref: "./agents/researcher.yaml"
```

The loader will:
1.  Resolve the path relative to the current file.
2.  Recursively load the target file.
3.  Replace the `$ref` block with the content of the loaded file.
4.  Validate the final composed structure.

## Security Model: The "Jail" Rule

To prevent **Path Traversal Attacks** (e.g., accessing `/etc/passwd` or secrets outside the project), the loader enforces a strict **Jail Rule**.

*   **Root Directory:** When you call `load(path)`, the directory containing that file (or a specified `root_dir`) becomes the "Jail".
*   **Confinement:** All references must resolve to a path *inside* this root directory.
*   **Enforcement:** Any attempt to reference a file outside the root (e.g., via `../../secret.yaml`) will raise a `ValueError` with a "Security Error" message.

### Example

Given this structure:
```
project/
  main.yaml
  tools/
    tool.yaml
secrets/
  api_keys.yaml
```

*   `main.yaml` **CAN** reference `tools/tool.yaml`.
*   `main.yaml` **CANNOT** reference `../secrets/api_keys.yaml`.

## Cycle Detection

The loader automatically detects circular dependencies to prevent infinite recursion crashes.

*   **Scenario:** File A refs File B, and File B refs File A.
*   **Outcome:** The loader raises a `RecursionError` explicitly identifying the cycle path.

## Diamond Dependencies

Diamond dependencies (where A imports B and C, and both B and C import D) are **supported**. The loader tracks the call stack correctly to ensure shared dependencies are loaded multiple times if needed (in different contexts) without triggering false positive cycle detection.

## Python API

```python
from coreason_manifest import load

# Standard secure load
# root_dir defaults to the parent of main.yaml
manifest = load("path/to/main.yaml")

# Custom Jail
# Only allow files within /opt/safe_zone
manifest = load("path/to/main.yaml", root_dir="/opt/safe_zone")

# Disable Recursion (Load raw $ref)
manifest = load("path/to/main.yaml", recursive=False)
```
