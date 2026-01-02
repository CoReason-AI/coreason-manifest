# Prosperity-3.0
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from coreason_manifest.errors import PolicyViolationError
from coreason_manifest.models import AgentDefinition


class PolicyEnforcer:
    """
    Component C: PolicyEnforcer (The Compliance Officer).

    Responsibility:
      - Embed a Rego (OPA) interpreter.
      - Evaluate the agent against the compliance.rego policy file.
    """

    def __init__(self, policy_path: str | Path, opa_path: str | Path = "opa") -> None:
        """
        Initialize the PolicyEnforcer.

        Args:
            policy_path: Path to the Rego policy file.
            opa_path: Path to the OPA binary. Defaults to "opa" (expected in PATH).
        """
        self.policy_path = Path(policy_path)
        self.opa_path = str(opa_path)

        if not self.policy_path.exists():
            raise FileNotFoundError(f"Policy file not found: {self.policy_path}")

    def evaluate(self, agent_def: AgentDefinition) -> None:
        """
        Evaluates the agent definition against the policy.

        Args:
            agent_def: The AgentDefinition model to check.

        Raises:
            PolicyViolationError: If the agent violates the policy.
            RuntimeError: If OPA execution fails.
        """
        # Convert AgentDefinition to dict for OPA input
        input_data = agent_def.model_dump(mode="json", by_alias=True)

        # We use 'opa eval' command.
        # We pass the policy file and the input data.
        # We query for 'data.compliance.deny'.
        # Assuming the policy package is 'compliance' and it defines a set 'deny'.

        # Construct the OPA command
        # opa eval -d policy.rego -I "data.compliance.deny"
        # We pass input via stdin

        cmd = [
            self.opa_path,
            "eval",
            "-d",
            str(self.policy_path),
            "-I",  # Read input from stdin
            "data.compliance.deny",  # Query
            "--format",
            "json",
        ]

        try:
            process = subprocess.run(
                cmd,
                input=json.dumps(input_data).encode("utf-8"),
                capture_output=True,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"OPA execution failed: {e.stderr.decode('utf-8')}") from e
        except FileNotFoundError as e:
            raise RuntimeError(f"OPA binary not found at {self.opa_path}. Please install OPA.") from e

        # Parse output
        # Output format: {"result": [{"expressions": [{"value": ["violation1", "violation2"]}]}]}
        try:
            result_json = json.loads(process.stdout)
        except json.JSONDecodeError as e:
            # Decode bytes safely for error message
            decoded_stdout = (
                process.stdout.decode("utf-8", errors="replace")
                if isinstance(process.stdout, bytes)
                else str(process.stdout)
            )
            raise RuntimeError(f"Failed to parse OPA output: {decoded_stdout}") from e

        violations = []
        if "result" in result_json:
            for res in result_json["result"]:
                if "expressions" in res:
                    for expr in res["expressions"]:
                        if "value" in expr and isinstance(expr["value"], list):
                            violations.extend(expr["value"])

        if violations:
            raise PolicyViolationError("Policy compliance check failed.", violations=violations)
