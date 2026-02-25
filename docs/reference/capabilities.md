# Tool Packs

## Overview
This module defines `ToolPack` bundles for organizing and distributing tools.

## Example

```python
from coreason_manifest.spec.core.tools import ToolPack, Dependency

pandas_dep = Dependency(
    name="pandas",
    version="2.0.0",
    manager="pip"
)

finance_pack = ToolPack(
    kind="ToolPack",
    namespace="coreason.tools.finance",
    tools=["calculate_roi", "fetch_ticker"],
    dependencies=[pandas_dep],
    env_vars=["ALPHA_VANTAGE_KEY"]
)
```

## API Reference

::: coreason_manifest.spec.core.tools.ToolPack

::: coreason_manifest.spec.core.tools.Dependency
