"""
AGENT INSTRUCTION: This module must remain strictly passive. Do not add execution loops.
It purely calculates filesystem geometry and projects a deterministic JSON payload to stdout.
"""

import json
import sys
from pathlib import Path


def main() -> None:
    """
    Calculates the absolute repository root and emits the exact MCP configuration
    payload required to bridge an external agentic sandbox into this environment.
    """
    # Mathematical anchor: __file__ -> cli/ -> coreason_manifest/ -> src/ -> REPO_ROOT
    repo_root = Path(__file__).resolve().parent.parent.parent.parent

    payload = {
        "mcpServers": {
            "coreason-manifest": {
                "command": "uv",
                "args": ["--directory", str(repo_root), "run", "coreason-mcp"],
                "env": {"COREASON_GRANTED_LICENSES": ""},
            }
        }
    }

    # Strict compliance: Zero pollution output to stdout.
    sys.stdout.write(json.dumps(payload, indent=2) + "\n")
    sys.stdout.flush()


if __name__ == "__main__":
    main()
