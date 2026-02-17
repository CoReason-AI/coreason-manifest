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
import hashlib
import importlib.util
import re
import warnings
from pathlib import Path
from typing import Any

import yaml

from coreason_manifest.spec.core.flow import GraphFlow, LinearFlow
from coreason_manifest.utils.io import ManifestIO, SecurityViolationError
from coreason_manifest.utils.logger import logger

__all__ = ["RuntimeSecurityWarning", "SecurityViolationError", "load_agent_from_ref", "load_flow_from_file"]


BANNED_IMPORTS = (
    "os",
    "subprocess",
    "sys",
    "importlib",
    "pickle",
    "shutil",
    "socket",
    "requests",
    "urllib",
    "inspect",
)

BANNED_CALLS = ("__import__", "eval", "exec", "compile")


class RuntimeSecurityWarning(RuntimeWarning):
    """Warning for runtime security risks."""


class UniqueKeyLoader(yaml.SafeLoader):
    """
    Custom YAML loader that disallows duplicate keys.
    Prevents "Ghost Logic" where duplicate keys are silently overwritten.
    """


def construct_mapping_unique(loader: yaml.SafeLoader, node: yaml.Node, deep: bool = False) -> dict[Any, Any]:
    """
    Construct a mapping while checking for duplicate keys.
    """
    # Mypy complains about Node vs MappingNode. SafeLoader expects MappingNode for mappings.
    if not isinstance(node, yaml.MappingNode):
        raise yaml.constructor.ConstructorError(
            None,
            None,
            f"expected a mapping node, but found {node.id}",  # type: ignore[attr-defined]
            node.start_mark,
        )

    loader.flatten_mapping(node)
    mapping = {}
    for key_node, value_node in node.value:
        # construct_object is dynamically added or not typed fully in types-pyyaml
        key = loader.construct_object(key_node, deep=deep)  # type: ignore[no-untyped-call]
        if key in mapping:
            raise yaml.constructor.ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                f"found duplicate key {key!r}",
                key_node.start_mark,
            )
        mapping[key] = loader.construct_object(value_node, deep=deep)  # type: ignore[no-untyped-call]
    return mapping


UniqueKeyLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, construct_mapping_unique)


def _scan_for_dynamic_references(data: Any) -> bool:
    """
    Recursively scan the data structure for potential dynamic code execution references.
    Looks for strings matching the pattern "file.py:ClassName".
    """
    if isinstance(data, dict):
        for value in data.values():
            if _scan_for_dynamic_references(value):
                return True
    elif isinstance(data, list):
        for item in data:
            if _scan_for_dynamic_references(item):
                return True
    # SIM102: Combined nested if
    elif isinstance(data, str) and re.match(r".+\.py:[a-zA-Z_]\w+$", data):
        return True
    return False


def load_flow_from_file(
    path: str, root_dir: Path | None = None, allow_dynamic_execution: bool = False
) -> LinearFlow | GraphFlow:
    """
    Load a flow manifest from a YAML or JSON file.

    Args:
        path: Path to the manifest file.
        root_dir: Optional root directory for path confinement. Defaults to file's parent.
        allow_dynamic_execution: Whether to allow potential dynamic code execution references.

    Returns:
        LinearFlow | GraphFlow: The parsed flow object.

    Raises:
        ValueError: If the file content is invalid or the kind is unknown.
        FileNotFoundError: If the file does not exist.
        SecurityViolationError: If path traversal or unsafe permissions are detected,
                                or if dynamic execution is attempted without consent.
        yaml.constructor.ConstructorError: If duplicate keys are found.
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

    # Domain 1: Lossless Configuration Loading
    # Read text content securely, then parse with duplicate key detection
    content_str = loader.read_text(load_path)

    try:
        data = yaml.load(content_str, Loader=UniqueKeyLoader)
    except yaml.YAMLError as e:
        raise ValueError(f"Failed to parse manifest file: {e}") from e

    if not isinstance(data, dict):
        raise ValueError("Manifest content must be a dictionary.")

    # Domain 2: Observable Security
    if _scan_for_dynamic_references(data) and not allow_dynamic_execution:
        raise SecurityViolationError(
            "Dynamic code execution references detected in manifest. Set 'allow_dynamic_execution=True' to proceed."
        )

    kind = data.get("kind")
    if kind == "LinearFlow":
        return LinearFlow.model_validate(data)
    if kind == "GraphFlow":
        return GraphFlow.model_validate(data)
    raise ValueError(f"Unknown or missing manifest kind: {kind}. Expected 'LinearFlow' or 'GraphFlow'.")


def _validate_ast(source_code: str, filename: str) -> None:
    """
    Scan source code for banned imports and dangerous calls using AST.
    """
    try:
        tree = ast.parse(source_code, filename=filename)
    except SyntaxError as e:  # pragma: no cover
        raise ValueError(f"Syntax error in {filename}: {e}") from e

    for node in ast.walk(tree):
        # 1. Import Check
        if isinstance(node, ast.Import):
            for alias in node.names:
                root_pkg = alias.name.split(".")[0]
                if root_pkg in BANNED_IMPORTS:
                    raise SecurityViolationError(f"Banned import '{alias.name}' detected in {filename}")
        elif isinstance(node, ast.ImportFrom):
            if node.module:  # pragma: no cover
                root_pkg = node.module.split(".")[0]
                if root_pkg in BANNED_IMPORTS:
                    raise SecurityViolationError(f"Banned import '{node.module}' detected in {filename}")

        # 2. Call Check (Ban __import__, eval, exec, compile)
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in BANNED_CALLS:
            raise SecurityViolationError(f"Banned call '{node.func.id}' detected in {filename}")

        # 3. Attribute Check (Gadget Chain)
        elif isinstance(node, ast.Attribute) and node.attr == "__subclasses__":
            raise SecurityViolationError(f"Banned attribute access '__subclasses__' detected in {filename}")


def load_agent_from_ref(reference: str, root_dir: Path) -> type:
    """
    Load an Agent class from a Python file reference (file.py:ClassName).
    Enforces security checks (AST validation, world-writable check).
    Avoids sys.path pollution and sys.modules injection.

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

    # Domain 2: Observable Security - Audit Log and Warning
    checksum = hashlib.sha256(source_code.encode("utf-8")).hexdigest()
    logger.warning(
        "Dynamic Code Execution Detected",
        extra={
            "event": "dynamic_exec",
            "source": str(file_path),
            "checksum": checksum,
            "verification": "AST_PASSED",
        },
    )

    warnings.warn(
        f"Dynamic Code Execution: Loading agent from {file_ref}. Ensure this code is trusted.",
        category=RuntimeSecurityWarning,
        stacklevel=2,
    )

    # Dynamic Loading without sys.modules/sys.path side effects
    spec = importlib.util.spec_from_file_location(file_ref, file_path)
    if spec is None or spec.loader is None:  # pragma: no cover
        raise ValueError(f"Could not create module spec for {file_ref}")

    module = importlib.util.module_from_spec(spec)

    # Set metadata manually for correct behavior in exec
    module.__file__ = str(file_path)
    module.__name__ = spec.name or "coreason_agent"

    # Restrict builtins in the module's dict before execution
    safe_builtins = {
        "__build_class__": __build_class__,
        "__name__": "__main__",
        "__import__": __import__,  # Required for import statements
        "abs": abs,
        "all": all,
        "any": any,
        "bool": bool,
        "dict": dict,
        "divmod": divmod,
        "enumerate": enumerate,
        "filter": filter,
        "float": float,
        "getattr": getattr,
        "hasattr": hasattr,
        "hash": hash,
        "id": id,
        "int": int,
        "isinstance": isinstance,
        "issubclass": issubclass,
        "iter": iter,
        "len": len,
        "list": list,
        "map": map,
        "max": max,
        "min": min,
        "next": next,
        "object": object,
        "pow": pow,
        "print": print,
        "property": property,
        "range": range,
        "repr": repr,
        "reversed": reversed,
        "round": round,
        "set": set,
        "slice": slice,
        "sorted": sorted,
        "str": str,
        "sum": sum,
        "super": super,
        "tuple": tuple,
        "type": type,
        "zip": zip,
    }

    module.__dict__["__builtins__"] = safe_builtins

    try:
        # Execute the module manually with restricted globals
        code = compile(source_code, str(file_path), "exec")
        exec(code, module.__dict__)
    except Exception as e:
        raise ValueError(f"Failed to execute agent code in {file_ref}: {e}") from e

    agent_class = getattr(module, class_name, None)
    if agent_class is None:
        raise ValueError(f"Agent class '{class_name}' not found in {file_ref}")

    if isinstance(agent_class, type):
        return agent_class

    raise TypeError(f"'{class_name}' in {file_ref} is not a class.")  # pragma: no cover
