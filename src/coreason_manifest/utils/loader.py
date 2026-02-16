# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import ast
import contextlib
import sys
import types
import uuid
from collections.abc import Generator
from pathlib import Path

from coreason_manifest.spec.core.flow import GraphFlow, LinearFlow
from coreason_manifest.utils.io import ManifestIO, SecurityViolationError

__all__ = ["SecurityViolationError", "load_agent_from_ref", "load_flow_from_file"]


def load_flow_from_file(path: str, root_dir: Path | None = None) -> LinearFlow | GraphFlow:
    """
    Load a flow manifest from a YAML or JSON file.

    Args:
        path: Path to the manifest file.
        root_dir: Optional root directory for path confinement. Defaults to file's parent.

    Returns:
        LinearFlow | GraphFlow: The parsed flow object.

    Raises:
        ValueError: If the file content is invalid or the kind is unknown.
        FileNotFoundError: If the file does not exist.
        SecurityViolationError: If path traversal or unsafe permissions are detected.
    """
    file_path = Path(path).resolve()
    jail_root = root_dir or file_path.parent

    # Initialize secure loader confined to the file's directory
    loader = ManifestIO(root_dir=jail_root)

    # Pass relative path from jail root to ensure loader can resolve it correctly
    try:
        rel_path = file_path.relative_to(jail_root)
        load_path = str(rel_path)
    except ValueError:
        # If file is not inside root_dir, let ManifestIO raise the security error
        # or handle it here. ManifestIO handles absolute paths too if allow_external is False.
        # But for clarity, we pass the relative path if possible, or just the name if same dir.
        load_path = file_path.name

    data = loader.load(load_path)

    kind = data.get("kind")
    if kind == "LinearFlow":
        return LinearFlow.model_validate(data)
    if kind == "GraphFlow":
        return GraphFlow.model_validate(data)
    raise ValueError(f"Unknown or missing manifest kind: {kind}. Expected 'LinearFlow' or 'GraphFlow'.")


@contextlib.contextmanager
def _temp_sys_path(path: Path) -> Generator[None, None, None]:
    path_str = str(path)
    sys.path.insert(0, path_str)
    try:
        yield
    finally:
        while path_str in sys.path:
            sys.path.remove(path_str)


def _validate_ast(source_code: str, filename: str) -> None:
    """
    Scan source code for banned imports using AST.
    """
    try:
        tree = ast.parse(source_code, filename=filename)
    except SyntaxError as e:
        raise ValueError(f"Syntax error in {filename}: {e}") from e

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in ("os", "subprocess", "sys"):
                    raise SecurityViolationError(f"Banned import '{alias.name}' detected in {filename}")
        elif isinstance(node, ast.ImportFrom) and node.module in ("os", "subprocess", "sys"):
            raise SecurityViolationError(f"Banned import '{node.module}' detected in {filename}")


def load_agent_from_ref(reference: str, root_dir: Path) -> type:
    """
    Load an Agent class from a Python file reference (file.py:ClassName).
    Enforces security checks (AST validation, world-writable check).

    Args:
        reference: string in format "path/to/file.py:ClassName"
        root_dir: The root directory for file access confinement.

    Returns:
        The loaded Agent class.
    """
    if ":" not in reference:
        raise ValueError(f"Invalid reference format: {reference}. Expected 'file.py:ClassName'.")

    file_ref, class_name = reference.rsplit(":", 1)

    # Resolve file path relative to root_dir
    loader = ManifestIO(root_dir=root_dir)

    # Read content securely (this enforces world-writable checks)
    source_code = loader.read_text(file_ref)

    file_path = (root_dir / file_ref).resolve()

    # AST Validation
    _validate_ast(source_code, str(file_path))

    # Dynamic Loading
    module_name = f"coreason.dynamic.{uuid.uuid4()}"
    module = types.ModuleType(module_name)
    module.__file__ = str(file_path)

    # Inject into sys.modules to prevent namespace pollution / collision
    sys.modules[module_name] = module

    try:
        with _temp_sys_path(file_path.parent):
            code = compile(source_code, str(file_path), "exec")
            exec(code, module.__dict__)
    except Exception:
        # Cleanup on failure
        sys.modules.pop(module_name, None)
        raise

    agent_class = getattr(module, class_name, None)
    if agent_class is None:
        # Cleanup on failure
        sys.modules.pop(module_name, None)
        raise ValueError(f"Agent class '{class_name}' not found in {file_ref}")

    if isinstance(agent_class, type):
        return agent_class

    sys.modules.pop(module_name, None)
    raise TypeError(f"'{class_name}' in {file_ref} is not a class.")
