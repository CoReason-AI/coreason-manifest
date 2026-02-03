# RFC 005: Secure Recursive Composition

## 1. Executive Summary

### The Problem
Manifest V2 aims to support modularity through the `$ref` syntax, allowing developers to split large manifests into smaller, reusable files (e.g., separating Tool definitions from the main Agent workflow). However, simply loading files presents significant security risks, specifically **Path Traversal Attacks** (e.g., `"$ref": "../../../etc/passwd"`), and technical challenges like **Circular Dependencies**.

### The Solution
We introduce a **Secure Recursive Loader** architecture. This system employs a strict `ReferenceResolver` that enforces a "Jail" directory, ensuring no file access occurs outside the authorized root. It implements a Depth-First Search (DFS) loading strategy with cycle detection to safely compose complex, nested manifests.

---

## 2. Architecture

### 2.1 The Reference Resolver ("The Jail")
The `ReferenceResolver` is the security kernel of the composition system. It is initialized with a `root_dir` (usually the directory of the entry-point manifest).

*   **Input:** A base file path and a relative reference string.
*   **Resolution:** `(base_file.parent / ref_path).resolve()`
*   **Enforcement:** The resolved path is checked against `root_dir` using `path.relative_to(root_dir)`.
*   **Violation:** If the path escapes the root, a `ValueError` (Security Error) is raised immediately.

### 2.2 Recursive Loading Strategy
The loader (`io.py`) transforms the flat YAML loader into a recursive build system.

1.  **Load:** Parse the current YAML file.
2.  **Scan:** Iterate through the `definitions` block looking for objects containing a single `$ref` key.
3.  **Resolve:** Use the `ReferenceResolver` to convert the relative path to an absolute, verified path.
4.  **Recurse:** Call `_load_recursive` on the new path.
    *   **State:** A set of `visited_paths` is passed down the stack.
    *   **Cycle Detection:** If the target path is already in `visited_paths`, a `RecursionError` is raised.
5.  **Merge:** Replace the `$ref` node with the fully loaded object.

---

## 3. Usage Examples

### 3.1 Basic Composition
**`tools/weather.yaml`**
```yaml
id: "weather-tool"
name: "Weather Service"
uri: "mcp://weather.com"
risk_level: "safe"
```

**`agent.yaml`**
```yaml
apiVersion: coreason.ai/v2
kind: Agent
metadata:
  name: "Weather Bot"
definitions:
  my_tool:
    $ref: "./tools/weather.yaml"  # Securely imports the tool
workflow:
  start: "step-1"
  steps:
    step-1:
      type: "agent"
      agent: "gpt-4"
      inputs:
        tools: ["weather-tool"]
```

### 3.2 Security Violation (Blocked)
**`hacker.yaml`**
```yaml
definitions:
  secret:
    $ref: "../../../etc/passwd"  # <--- BLOCKED by ReferenceResolver
```
Attempting to load this file will raise:
`ValueError: Security Error: Reference '../../../etc/passwd' escapes the root directory...`

---

## 4. Implementation Details

### Dependencies
The implementation uses **Standard Library only** (`pathlib`, `typing`) to avoid bloating the dependency tree. It does not rely on external `jsonref` libraries, giving us fine-grained control over the security logic.

### State Management
The `visited_paths` set is critical for preventing infinite recursion. It is managed as a stack-local variable (added before recursion, removed after return) to correctly handle diamond dependency patterns (where two files A and B both import C).

### Round-Trip Dumping
The `dump_to_yaml` function currently serializes the *fully composed* manifest. In the future, we may introduce a "Splitter" to reverse the process and save definitions back to their original files.
