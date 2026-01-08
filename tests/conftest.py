import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union
from unittest.mock import MagicMock

import pytest


@pytest.fixture(autouse=True)
def mock_shutil_which(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Mock shutil.which to always return a fake path for 'opa',
    unless the test specifically needs strict behavior.
    """
    original_which = shutil.which

    import os

    def side_effect(cmd: str, mode: int = os.F_OK | os.X_OK, path: Optional[str] = None) -> Optional[str]:
        if cmd == "opa":
            return "/usr/bin/mock_opa"
        return original_which(cmd, mode, path)

    monkeypatch.setattr(shutil, "which", side_effect)


class MockOPARunner:
    """Simulates OPA evaluation logic in Python for testing without binary."""

    def __init__(self, monkeypatch: pytest.MonkeyPatch):
        self.original_run = subprocess.run
        self.monkeypatch = monkeypatch
        self.monkeypatch.setattr(subprocess, "run", self._mock_subprocess_run)

    def _mock_subprocess_run(
        self, cmd: List[str], input: Optional[str] = None, **kwargs: Any
    ) -> Union[MagicMock, subprocess.CompletedProcess[str]]:
        # Only intercept OPA commands
        # Check if "opa" is in the command string (either as 'opa' or '/path/to/opa')
        if not cmd or "opa" not in str(cmd[0]):
            return self.original_run(cmd, input=input, **kwargs)

        # Parse arguments
        # cmd format: [opa_path, 'eval', '-d', policy, '-d', data, ..., '-I', query, '--format', 'json']
        data_paths: List[Path] = []
        i = 0
        while i < len(cmd):
            if cmd[i] == "-d":
                data_paths.append(Path(cmd[i + 1]))
                i += 2
            else:
                i += 1

        # Parse Input
        if not input:
            return self._create_result([])

        try:
            agent_data = json.loads(input)
        except json.JSONDecodeError:
            # OPA fails on bad JSON input
            return self._create_error("JSON decode error")

        violations = self._evaluate_policy(agent_data, data_paths)
        return self._create_result(violations)

    def _create_result(self, violations: List[str]) -> MagicMock:
        mock_res = MagicMock()
        mock_res.returncode = 0
        mock_res.stdout = json.dumps({"result": [{"expressions": [{"value": violations}]}]})
        mock_res.stderr = ""
        return mock_res

    def _create_error(self, msg: str) -> MagicMock:
        mock_res = MagicMock()
        mock_res.returncode = 1
        mock_res.stdout = ""
        mock_res.stderr = f"OPA execution failed: {msg}"
        return mock_res

    def _evaluate_policy(self, agent_data: Dict[str, Any], data_paths: List[Path]) -> List[str]:
        violations = []
        deps = agent_data.get("dependencies", {})
        libs = deps.get("libraries", [])
        topology = agent_data.get("topology", {})
        steps = topology.get("steps", [])

        # Load TBOM if available
        tbom_set: Set[str] = set()
        tbom_loaded = False

        for p in data_paths:
            if p.name.endswith(".json"):
                try:
                    with open(p, "r") as f:
                        data = json.load(f)
                        if "tbom" in data:
                            if isinstance(data["tbom"], list):
                                tbom_set.update(item.lower() for item in data["tbom"])
                                tbom_loaded = True
                            else:
                                # Malformed TBOM structure (not a list)
                                pass
                except json.JSONDecodeError:
                    raise RuntimeError("OPA execution failed: JSON parse error in data file") from None

        # Regex for pinning
        # ^[a-zA-Z0-9_\-\.]+(\[[a-zA-Z0-9_\-\.,]+\])?==[a-zA-Z0-9_\-\.\+]+$
        pinning_pattern = re.compile(r"^[a-zA-Z0-9_\-\.]+(\[[a-zA-Z0-9_\-\.,]+\])?==[a-zA-Z0-9_\-\.\+]+$")

        # Regex for extracting name
        name_pattern = re.compile(r"^[a-zA-Z0-9_\-\.]+")

        for lib in libs:
            # Deny pickle
            if re.match(r"^pickle([<>=!@\[].*)?$", lib):
                violations.append("Security Risk: 'pickle' library is strictly forbidden.")

            # Deny os
            if re.match(r"^os([<>=!@\[].*)?$", lib):
                violations.append("Security Risk: 'os' library is strictly forbidden.")

            # Rule 1: Pinning
            if not pinning_pattern.match(lib):
                violations.append(
                    f"Compliance Violation: Library '{lib}' must be strictly pinned with '==' (e.g., 'pandas==2.0.1')."
                )

            # Rule 2: TBOM
            match = name_pattern.match(lib)
            if match:
                name = match.group(0).lower()
                found = False
                if tbom_loaded:
                    if name in tbom_set:
                        found = True

                if not found:
                    violations.append(
                        f"Compliance Violation: Library '{name}' is not in the Trusted Bill of Materials (TBOM)."
                    )

        # Rule 3: Description Length
        for step in steps:
            desc = step.get("description")
            if desc is not None:
                if len(desc) < 5:
                    violations.append("Step description is too short.")

        return violations


@pytest.fixture(autouse=True)
def mock_opa_env(monkeypatch: pytest.MonkeyPatch) -> MockOPARunner:
    """
    Automatically mock OPA for all tests to ensure they run without binary.
    """
    runner = MockOPARunner(monkeypatch)
    return runner
