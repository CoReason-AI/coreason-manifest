# src/coreason_manifest/utils/loader.py

import importlib.abc
import importlib.util
import re
import sys
import threading
import warnings
from collections.abc import Generator
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
from typing import Any, Protocol, cast

import yaml
from yaml.nodes import MappingNode

from coreason_manifest.spec.core.flow import GraphFlow, LinearFlow
from coreason_manifest.utils.io import ManifestIO, SecurityViolationError

__all__ = ["RuntimeSecurityWarning", "SecurityViolationError", "load_agent_from_ref", "load_flow_from_file"]


class RuntimeSecurityWarning(RuntimeWarning):
    """Warning for runtime security risks."""


class YamlLoaderProtocol(Protocol):
    def construct_object(self, node: yaml.Node, deep: bool = False) -> Any: ...
    def flatten_mapping(self, node: MappingNode) -> None: ...


class UniqueKeyLoader(yaml.SafeLoader):
    """
    Custom YAML loader that disallows duplicate keys.
    Prevents "Ghost Logic" where duplicate keys are silently overwritten.
    """


def construct_mapping_unique(loader: yaml.SafeLoader, node: yaml.Node, deep: bool = False) -> dict[Any, Any]:
    """
    Construct a mapping while checking for duplicate keys.
    """
    if not isinstance(node, MappingNode):
        # Cast node to Any to access attributes not in base Node but expected by ConstructorError format
        node_any = cast(Any, node)  # noqa: TC006
        raise yaml.constructor.ConstructorError(
            None,
            None,
            f"expected a mapping node, but found {node_any.id}",
            node.start_mark,
        )

    mapping_node = node
    loader_typed = cast(YamlLoaderProtocol, loader)  # noqa: TC006
    loader_typed.flatten_mapping(mapping_node)
    mapping = {}
    for key_node, value_node in mapping_node.value:
        key = loader_typed.construct_object(key_node, deep=deep)
        if key in mapping:
            raise yaml.constructor.ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                f"found duplicate key {key!r}",
                key_node.start_mark,
            )
        mapping[key] = loader_typed.construct_object(value_node, deep=deep)
    return mapping


UniqueKeyLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, construct_mapping_unique)


# SOTA Security: Context-aware jail root for import resolution.
# Uses ContextVar to handle async concurrency safely without race conditions.
_jail_root_var: ContextVar[Path | None] = ContextVar("jail_root", default=None)


class SandboxedPathFinder(importlib.abc.MetaPathFinder):
    """
    A custom MetaPathFinder that resolves imports relative to a 'jail' directory
    without modifying sys.path. It uses a ContextVar to determine the current
    jail, ensuring thread/task safety.
    """

    def find_spec(
        self,
        fullname: str,
        _path: Any = None,
        _target: Any = None,
    ) -> importlib.machinery.ModuleSpec | None:
        """
        Attempt to find the module in the current jail root.
        """
        jail_root = _jail_root_var.get()
        if not jail_root:
            return None

        # Security: Prevent directory traversal via package names
        if ".." in fullname:
            return None

        # Determine path relative to jail
        # Logic: If '_path' is None, it's a top-level import.
        # If '_path' is set, it's a sub-module import.
        # But our jail_root acts as a PYTHONPATH root.

        # We try to find:
        # 1. jail_root/fullname.py
        # 2. jail_root/fullname/__init__.py

        # Convert dotted name to path
        parts = fullname.split(".")
        potential_path = jail_root.joinpath(*parts)

        # Check for package (directory with __init__.py)
        init_py = potential_path / "__init__.py"
        if init_py.is_file():
            return importlib.util.spec_from_file_location(fullname, init_py)

        # Check for module (file.py)
        module_py = potential_path.with_suffix(".py")
        if module_py.is_file():
            return importlib.util.spec_from_file_location(fullname, module_py)

        return None


# Singleton instance of the finder
_SANDBOXED_FINDER = SandboxedPathFinder()

# Global lock to prevent race conditions when modifying sys.modules
_loader_lock = threading.Lock()


@contextmanager
def sandbox_context(jail_root: Path) -> Generator[None, None, None]:
    """
    Context manager to activate the sandboxed finder for the given jail root.
    Ensures the finder is registered in sys.meta_path.
    """
    # Register finder if not present (idempotent, somewhat race-prone on insert but harmless if duplicated in logic)
    # To be safer, we check if it's there.
    if _SANDBOXED_FINDER not in sys.meta_path:
        sys.meta_path.insert(0, _SANDBOXED_FINDER)

    token = _jail_root_var.set(jail_root.resolve())
    try:
        yield
    finally:
        _jail_root_var.reset(token)
        # We generally don't remove the finder to avoid race conditions with other threads using it.
        # It's benign when jail_root is None.


def _scan_for_dynamic_references(data: Any) -> bool:
    """
    Recursively scan the data structure for potential dynamic code execution references.
    """
    if isinstance(data, dict):
        for value in data.values():
            if _scan_for_dynamic_references(value):
                return True
    elif isinstance(data, list):
        for item in data:
            if _scan_for_dynamic_references(item):
                return True
    elif isinstance(data, str) and re.match(r"^[a-zA-Z0-9_\-\./]+\.py:[a-zA-Z_]\w+$", data):
        return True
    return False


def load_flow_from_file(
    path: str, root_dir: Path | None = None, allow_dynamic_execution: bool = False
) -> LinearFlow | GraphFlow:
    """
    Load a flow manifest from a YAML or JSON file.
    """
    file_path = Path(path).resolve()
    jail_root = root_dir or file_path.parent

    # Initialize secure loader confined to the file's directory
    loader = ManifestIO(root_dir=jail_root)

    try:
        rel_path = file_path.relative_to(jail_root)
        load_path = str(rel_path)
    except ValueError:
        load_path = file_path.name

    content_str = loader.read_text(load_path)

    try:
        data = yaml.load(content_str, Loader=UniqueKeyLoader)
    except yaml.YAMLError as e:
        raise ValueError(f"Failed to parse manifest file: {e}") from e

    if not isinstance(data, dict):
        raise ValueError("Manifest content must be a dictionary.")

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


def load_agent_from_ref(reference: str, root_dir: Path) -> type:
    """
    Load an Agent class from a Python file reference (file.py:ClassName).
    WARNING: Executes arbitrary code. Ensure source is trusted.

    Args:
        reference: string in format "path/to/file.py:ClassName"
        root_dir: The root directory for file access confinement.

    Returns:
        The loaded Agent class.
    """
    if ":" not in reference:
        raise ValueError(f"Invalid reference format: {reference}. Expected 'file.py:ClassName'.")

    file_ref, class_name = reference.rsplit(":", 1)

    file_path = (root_dir / file_ref).resolve()
    if not file_path.is_file():
        raise ValueError(f"Agent file not found: {file_path}")

    # Explicit warning for audit logs
    warnings.warn(
        f"Dynamic Code Execution: Loading agent from {file_ref}. Ensure this code is trusted.",
        category=RuntimeSecurityWarning,
        stacklevel=2,
    )

    module_name = Path(file_ref).stem

    # Use context manager to enable jailed imports during spec finding and loading
    with sandbox_context(root_dir):
        # Track pre-existing modules to identify new ones for cleanup
        pre_existing_modules = set(sys.modules.keys())

        # We use spec_from_file_location, but imports INSIDE the module need the finder.
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            raise ValueError(f"Could not load spec for {file_ref}")

        module = importlib.util.module_from_spec(spec)

        # We must register in sys.modules for relative imports to work (if any)
        # and for the module to be valid.
        sys.modules[module_name] = module

        try:
            spec.loader.exec_module(module)
        except Exception as e:
            # Cleanup on failure
            if module_name in sys.modules:
                del sys.modules[module_name]
            # Also cleanup dependencies that might have been loaded
            new_modules = set(sys.modules.keys()) - pre_existing_modules
            for mod in new_modules:
                if mod in sys.modules:
                    del sys.modules[mod]
            raise ValueError(f"Failed to execute agent code in {file_ref}: {e}") from e

    agent_class = getattr(module, class_name, None)

    # SOTA Cleanup: Remove loaded modules to prevent pollution and collision.
    # We do this BEFORE returning/raising to ensure state is clean.
    # The class object retains its globals and works fine.
    new_modules = set(sys.modules.keys()) - pre_existing_modules
    for mod in new_modules:
        if mod in sys.modules:
            del sys.modules[mod]

    if agent_class is None:
        raise ValueError(f"Agent class '{class_name}' not found in {file_ref}")

    if isinstance(agent_class, type):
        return agent_class

    raise TypeError(f"'{class_name}' in {file_ref} is not a class.")
