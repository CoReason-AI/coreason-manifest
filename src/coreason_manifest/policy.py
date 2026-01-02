# Prosperity-3.0
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, List

from coreason_manifest.errors import PolicyViolationError


class PolicyEnforcer:
    """
    Component C: PolicyEnforcer (The Compliance Officer).

    Responsibility:
      - Evaluate the agent against the compliance.rego policy file using OPA.
    """

    def __init__(self, policy_path: str | Path, opa_path: str = "opa") -> None:
        """
        Initialize the PolicyEnforcer.

        Args:
            policy_path: Path to the Rego policy file.
            opa_path: Path to the OPA executable. Defaults to "opa" (expected in PATH).
        """
        self.policy_path = Path(policy_path)
        self.opa_path = opa_path

        if not self.policy_path.exists():
            raise FileNotFoundError(f"Policy file not found: {self.policy_path}")

    def evaluate(self, agent_data: dict[str, Any]) -> None:
        """
        Evaluates the agent data against the policy.

        Args:
            agent_data: The dictionary representation of the AgentDefinition.

        Raises:
            PolicyViolationError: If there are any policy violations.
            RuntimeError: If OPA execution fails.
        """
        # Prepare input for OPA
        # We invoke OPA via subprocess: opa eval -d <policy> -I <input> "data.coreason.compliance.deny"
        # We pass input via stdin to avoid temp files

        try:
            # We use 'data.coreason.compliance.deny' as the query
            query = "data.coreason.compliance.deny"

            # Serialize input to JSON
            input_json = json.dumps(agent_data)

            process = subprocess.run(
                [
                    self.opa_path,
                    "eval",
                    "-d",
                    str(self.policy_path),
                    "-I",  # Read input from stdin
                    query,
                    "--format",
                    "json",
                ],
                input=input_json,
                capture_output=True,
                text=True,
                check=False,  # We handle return code manually
            )

            if process.returncode != 0:
                raise RuntimeError(f"OPA execution failed: {process.stderr}")

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
