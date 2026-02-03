# Migration Guide: V2 Breaking Switch

This guide outlines the changes introduced in Coreason Manifest **v0.12.0**, which makes the **V2 Agent Manifest (CAM)** the default experience.

## Executive Summary

*   **V2 is Default:** `coreason_manifest` now exports V2 components (`Manifest`, `Recipe`, `load`, `dump`) by default.
*   **V1 is Deprecated:** Legacy V1 components (`RecipeManifest`, `AgentDefinition`) have been moved to the `coreason_manifest.v1` namespace.
*   **Action Required:** Existing code that imports directly from the root package will break and must be updated.

## 1. Import Changes

### Breaking Change
The following imports will now raise an `AttributeError` or import the wrong class (V2 instead of V1):

**❌ Old Code (V1):**
```python
from coreason_manifest import RecipeManifest, AgentDefinition
from coreason_manifest import Topology
```

### Required Update (Option A: Explicit V1)
To continue using V1 components without changing logic, update your imports to point to the `v1` namespace.

**✅ New Code (V1 Legacy):**
```python
from coreason_manifest.v1 import RecipeManifest, AgentDefinition
from coreason_manifest.v1 import Topology
```

### Required Update (Option B: Switch to V2)
To adopt the new standard, use the root imports for V2.

**✅ New Code (V2 Standard):**
```python
from coreason_manifest import Manifest, load
```

## 2. Loading Files

### V1 Loader (Deprecated)
The `load_from_json` function has been removed from the root.

**❌ Old Code:**
```python
from coreason_manifest import load_from_json
manifest = load_from_json("recipe.json")
```

**✅ New Code (V1 Legacy):**
```python
# You must construct from Pydantic directly or implement your own JSON loader
# as load_from_json was a simple helper.
import json
from coreason_manifest.v1 import RecipeManifest

with open("recipe.json") as f:
    data = json.load(f)
    manifest = RecipeManifest.model_validate(data)
```

### V2 Loader (Recommended)
Use the unified `load` function for V2 YAML manifests.

**✅ New Code (V2):**
```python
from coreason_manifest import load
manifest = load("agent.yaml")
```

## 3. Namespace Reference

| Component | V1 Location (Legacy) | V2 Location (Default) |
| :--- | :--- | :--- |
| **Manifest** | `coreason_manifest.v1.RecipeManifest` | `coreason_manifest.Manifest` |
| **Agent** | `coreason_manifest.v1.AgentDefinition` | `coreason_manifest.Manifest` (kind='Agent') |
| **Topology** | `coreason_manifest.v1.GraphTopology` | `coreason_manifest.v2.spec.definitions.Workflow` |
| **Node Types** | `coreason_manifest.v1.AgentNode` | `coreason_manifest.v2.spec.definitions.AgentStep` |
