# V2 Loader Bridge

The **V2 Loader Bridge** is the mechanism that connects the human-friendly **V2 Canonical YAML** format with the strict, machine-optimized **V1 Runtime Engine**.

It allows developers to write manifests in the concise V2 YAML format and immediately execute them on the existing V1 engine without waiting for a full runtime rewrite.

## Components

The bridge consists of three main modules located in `src/coreason_manifest/v2/`:

1.  **Compiler** (`compiler.py`): Transforms the implicit "Linked List" topology of V2 into the explicit "Graph" topology of V1.
2.  **I/O** (`io.py`): Handles loading and dumping of V2 YAML files, ensuring correct key ordering for human readability.
3.  **Adapter** (`adapter.py`): Converts a loaded V2 `ManifestV2` object into a V1 `RecipeManifest` ready for execution.

## Usage

### Loading and Executing a V2 Manifest

To run a V2 YAML file, you use the `load_from_yaml` function to parse the file and `v2_to_recipe` to convert it.

```python
from coreason_manifest.v2.io import load_from_yaml
from coreason_manifest.v2.adapter import v2_to_recipe

# 1. Load V2 Manifest (Human Friendly)
v2_manifest = load_from_yaml("my_workflow.v2.yaml")

# 2. Convert to V1 Recipe (Machine Optimized)
recipe = v2_to_recipe(v2_manifest)

# 3. The 'recipe' object is now a standard RecipeManifest
# compatible with the coreason-maco engine.
print(f"Loaded Recipe: {recipe.name} (ID: {recipe.id})")
print(f"Topology has {len(recipe.topology.nodes)} nodes.")
```

### Compiler Logic

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
