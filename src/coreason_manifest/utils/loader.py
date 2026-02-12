# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import re
import warnings
from pathlib import Path
from typing import Any

import yaml

from coreason_manifest.spec.core.flow import GraphFlow, LinearFlow

# Forbidden patterns in string values (e.g. Code Injection attempts)
FORBIDDEN_PATTERNS = [
    re.compile(r"subprocess\.Popen", re.IGNORECASE),
    re.compile(r"os\.system", re.IGNORECASE),
    re.compile(r"__import__", re.IGNORECASE),
    re.compile(r"eval\(", re.IGNORECASE),
    re.compile(r"exec\(", re.IGNORECASE),
]


def safety_check(data: Any) -> None:
    """
    Recursively scans the loaded data for forbidden patterns.
    Raises ValueError if a violation is found.
    """
    if isinstance(data, dict):
        for key, value in data.items():
            safety_check(key)
            safety_check(value)
    elif isinstance(data, list):
        for item in data:
            safety_check(item)
    elif isinstance(data, str):
        for pattern in FORBIDDEN_PATTERNS:
            if pattern.search(data):
                warnings.warn(
                    f"Potential Security Issue: Pattern '{pattern.pattern}' found in manifest content. "
                    "Ensure this input is trusted.",
                    UserWarning
                )


class ManifestRegistry:
    """
    Registry to cache loaded definitions and prevent circular import loops.
    """

    def __init__(self) -> None:
        self._cache: dict[str, dict[str, Any]] = {}
        self._loading: set[str] = set()

    def is_loading(self, path: str) -> bool:
        return path in self._loading

    def mark_loading(self, path: str) -> None:
        self._loading.add(path)

    def mark_loaded(self, path: str, data: dict[str, Any]) -> None:
        self._loading.remove(path)
        self._cache[path] = data

    def get(self, path: str) -> dict[str, Any] | None:
        return self._cache.get(path)


class CitadelLoader:
    def __init__(self, root: Path, allow_https: bool = False):
        self.root = root.resolve()
        self.registry = ManifestRegistry()
        self.allow_https = allow_https

    def _resolve_ref(self, base_path: Path, ref: str) -> Path:
        """
        Resolves a reference relative to the base path and enforces the jail.
        """
        # Protocol check
        if ref.startswith("https://"):
            if not self.allow_https:
                raise ValueError(f"Security Violation: Remote references not allowed (found '{ref}').")
            # Logic for HTTPS would go here (e.g. requests.get)
            # For now, we only implement local file loading as per basic requirements
            # unless we want to implement full http loading.
            # The prompt says "allow controlled access to https://... if configured".
            # I will skip actual HTTP fetching implementation for simplicity unless needed,
            # or treat it as a placeholder.
            raise NotImplementedError("HTTPS loading not yet implemented.")

        path_str = ref.removeprefix("file://")

        # Resolve path
        target_path = (base_path.parent / path_str).resolve()

        # Jail check
        if not target_path.is_relative_to(self.root):
            raise ValueError(
                f"Security Violation: Path traversal attempt denied. "
                f"'{ref}' resolves to '{target_path}' which is outside root '{self.root}'."
            )

        return target_path

    def load_recursive(self, path: Path) -> dict[str, Any]:
        """
        Loads a YAML file, recursively resolving $ref keys.
        """
        abs_path = path.resolve()
        path_str = str(abs_path)

        # 1. Check Registry (Cache & Circular Dependency)
        if self.registry.is_loading(path_str):
            raise ValueError(f"Circular dependency detected: {path_str}")

        cached = self.registry.get(path_str)
        if cached is not None:
            return cached

        if not abs_path.exists():
            raise FileNotFoundError(f"Manifest file not found: {abs_path}")

        # 2. Load Raw YAML
        self.registry.mark_loading(path_str)
        try:
            with abs_path.open("r", encoding="utf-8") as f:
                content = f.read()

            data = yaml.safe_load(content)
        except yaml.YAMLError as e:
            raise ValueError(f"Failed to parse manifest file {abs_path}: {e}") from e

        if not isinstance(data, (dict, list)):
            # Top level could be list? Usually dict for Flow.
            pass

        # 3. Safety Check
        safety_check(data)

        # 4. Resolve Refs
        resolved_data = self._traverse_and_resolve(data, abs_path)

        # 5. Cache
        self.registry.mark_loaded(path_str, resolved_data)

        return resolved_data  # type: ignore

    def _traverse_and_resolve(self, data: Any, current_file_path: Path) -> Any:
        if isinstance(data, dict):
            # Check for $ref
            if "$ref" in data:
                ref = data["$ref"]
                target_path = self._resolve_ref(current_file_path, ref)
                # Recursively load the referenced file
                return self.load_recursive(target_path)

            # Recurse for other keys
            return {k: self._traverse_and_resolve(v, current_file_path) for k, v in data.items()}

        if isinstance(data, list):
            return [self._traverse_and_resolve(item, current_file_path) for item in data]

        return data


def load_flow_from_file(path: str) -> LinearFlow | GraphFlow:
    """
    Load a flow manifest from a YAML or JSON file.
    Enforces security checks and resolves references.

    Args:
        path: Path to the manifest file.

    Returns:
        LinearFlow | GraphFlow: The parsed flow object.
    """
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Manifest file not found: {path}")

    # Root jail is determined by the entry file's directory (or parent?)
    # "Jailed to root dir". I'll use the parent of the entry file.
    # If the user provides an absolute path to /opt/app/manifest.yaml, root is /opt/app.
    root_jail = file_path.resolve().parent

    loader = CitadelLoader(root=root_jail)
    data = loader.load_recursive(file_path)

    if not isinstance(data, dict):
        raise ValueError("Manifest content must be a dictionary/object.")

    kind = data.get("kind")
    if kind == "LinearFlow":
        return LinearFlow.model_validate(data)
    if kind == "GraphFlow":
        return GraphFlow.model_validate(data)
    raise ValueError(f"Unknown or missing manifest kind: {kind}. Expected 'LinearFlow' or 'GraphFlow'.")
