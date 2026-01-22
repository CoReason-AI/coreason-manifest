# Prosperity-3.0
"""Policy enforcement functionality using Open Policy Agent (OPA).

This module provides the `PolicyEnforcer` class, which interacts with OPA to
evaluate agent definitions against compliance policies defined in Rego.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any, List, Optional

from coreason_manifest.errors import PolicyViolationError


class PolicyEnforcer:
    """Component C: PolicyEnforcer (The Compliance Officer).

    Responsibility:
      - Evaluate the agent against the compliance.rego policy file using OPA.
    """

    def __init__(
        self,
        policy_path: str | Path,
        opa_path: str = "opa",
        data_paths: Optional[List[str | Path]] = None,
    ) -> None:
        """Initialize the PolicyEnforcer.

        Args:
            policy_path: Path to the Rego policy file.
            opa_path: Path to the OPA executable. Defaults to "opa" (expected in PATH).
            data_paths: List of paths to data files (e.g. JSON/YAML) to be loaded by OPA.

        Raises:
            FileNotFoundError: If OPA, policy file, or data files are not found.
        """
        self.policy_path = Path(policy_path)
        self.data_paths = [Path(p) for p in data_paths] if data_paths else []

        # Validate OPA executable
        # If opa_path is a simple name (like "opa"), use shutil.which to find it
        if "/" not in str(opa_path) and "\\" not in str(opa_path):
            resolved_opa: Optional[str] = shutil.which(opa_path)
            if not resolved_opa:
                raise FileNotFoundError(f"OPA executable not found in PATH: {opa_path}")
            self.opa_path: str = resolved_opa
        else:
            # If it's a path, check existence
            if not Path(opa_path).exists():
                raise FileNotFoundError(f"OPA executable not found at: {opa_path}")
            self.opa_path = str(opa_path)

        if not self.policy_path.exists():
            raise FileNotFoundError(f"Policy file not found: {self.policy_path}")

        for path in self.data_paths:
            if not path.exists():
                raise FileNotFoundError(f"Data file not found: {path}")

    def evaluate(self, agent_data: dict[str, Any]) -> None:
        """Evaluates the agent data against the policy.

        Args:
            agent_data: The dictionary representation of the AgentDefinition.

        Raises:
            PolicyViolationError: If there are any policy violations.
            RuntimeError: If OPA execution fails.
        """
        # Prepare input for OPA
        # We invoke OPA via subprocess: opa eval -d <policy> -d <data> ... -I <input> "data.coreason.compliance.deny"
        # We pass input via stdin to avoid temp files

        try:
            # We use 'data.coreason.compliance.deny' as the query
            query = "data.coreason.compliance.deny"

            # Serialize input to JSON
            input_json = json.dumps(agent_data)

            cmd = [
                self.opa_path,
                "eval",
                "-d",
                str(self.policy_path),
            ]

            # Add data paths
            for data_path in self.data_paths:
                cmd.extend(["-d", str(data_path)])

            cmd.extend(
                [
                    "-I",  # Read input from stdin
                    query,
                    "--format",
                    "json",
                ]
            )

            process = subprocess.run(
                cmd,
                input=input_json,
                capture_output=True,
                text=True,
                check=False,  # We handle return code manually
            )

            if process.returncode != 0:
                # Include stdout in error message if stderr is empty or insufficient
                error_msg = process.stderr.strip()
                if not error_msg:
                    error_msg = process.stdout.strip() or "Unknown error (empty stdout/stderr)"
                raise RuntimeError(f"OPA execution failed: {error_msg}")

            # Parse OPA output
            # Format: {"result": [{"expressions": [{"value": ["violation1", "violation2"]}]}]}
            result = json.loads(process.stdout)

            violations: List[str] = []
            if "result" in result and len(result["result"]) > 0:
                # Assuming the query returns a set/list of strings
                expressions = result["result"][0].get("expressions", [])
                if expressions:
                    violations = expressions[0].get("value", [])

            if violations:
                raise PolicyViolationError("Policy violations found.", violations=violations)

        except FileNotFoundError as e:
            raise RuntimeError(f"OPA executable not found at: {self.opa_path}") from e
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse OPA output: {e}") from e
