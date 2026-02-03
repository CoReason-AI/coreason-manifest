# Migration Guide: V1 to V2

Coreason Manifest v0.12.0 introduces a **Breaking Change** to the default import behavior. The root `coreason_manifest` package now exports **V2** objects by default, while legacy **V1** objects have been moved to the `coreason_manifest.v1` namespace.

This guide details the changes and how to migrate your existing code.

## Summary of Changes

| Feature | Legacy (V1) | Modern (V2) |
| :--- | :--- | :--- |
| **Default Export** | `RecipeManifest` | `Manifest` (V2) |
| **Serialization** | `.model_dump()` | `dump()` / `load()` |
| **File Format** | Pydantic / JSON | Canonical YAML (CAM) |
| **Topology** | GraphTopology (Pydantic) | V2 Workflow Topology |

## 1. Import Changes

### The "Quick Fix" (Legacy Mode)
If you are not ready to upgrade to V2, you can keep your existing V1 code working by updating your imports.

**Before:**
```python
from coreason_manifest import RecipeManifest, AgentDefinition, Topology
```

**After:**
```python
from coreason_manifest.v1 import RecipeManifest, AgentDefinition, Topology
# OR
from coreason_manifest.recipes import RecipeManifest
from coreason_manifest.definitions.agent import AgentDefinition
```

### Adopting V2 (Recommended)
The new default `Manifest` is the entry point for the V2 ecosystem.

```python
import coreason_manifest as cm

# Load a V2 YAML file
manifest = cm.load("path/to/manifest.yaml")

# Work with the V2 object
print(manifest.metadata.name)
```

## 2. Using the V2 API

The V2 API is designed around the **Canonical Agent Manifest (CAM)** YAML format.

### Loading
```python
from coreason_manifest import load

manifest = load("agent.yaml", recursive=True)
```

### Dumping
```python
from coreason_manifest import dump

yaml_str = dump(manifest)
print(yaml_str)
```

## 3. Backward Compatibility

While the root exports have changed, the underlying V1 definitions (`coreason_manifest.definitions.*`) remain in place. The V2 adapter layer is available to translate V2 manifests into V1 runtime objects if needed.

```python
from coreason_manifest.v2.adapter import v2_to_recipe

# Convert V2 Manifest to V1 Recipe
recipe = v2_to_recipe(manifest_v2)
```

## Troubleshooting

**Error:** `AttributeError: module 'coreason_manifest' has no attribute 'RecipeManifest'`
**Solution:** Change your import to `from coreason_manifest.v1 import RecipeManifest`.

**Error:** `ImportError: cannot import name 'AgentDefinition' from 'coreason_manifest'`
**Solution:** Change your import to `from coreason_manifest.v1 import AgentDefinition`.
