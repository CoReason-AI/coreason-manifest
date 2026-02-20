# src/coreason_manifest/utils/loader.py

import hashlib
import importlib.abc
import importlib.util
import re
import sys
import warnings
from collections.abc import Generator
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
from typing import Any, Literal, Protocol, cast

import yaml
from pydantic import ValidationError
from yaml.nodes import MappingNode

from coreason_manifest.spec.core.exceptions import (
    ManifestSyntaxError,
    SecurityExceptionError,
)
from coreason_manifest.spec.core.flow import GraphFlow, LinearFlow
from coreason_manifest.utils.io import ManifestIO, SecurityViolationError
from coreason_manifest.utils.resolver import CircularReferenceError, ResolutionContext

__all__ = [
    "CircularReferenceError",
    "ManifestSyntaxError",
    "RuntimeSecurityWarning",
    "SecurityExceptionError",
    "SecurityViolationError",
    "load_agent_from_ref",
    "load_flow_from_file",
]


class RuntimeSecurityWarning(RuntimeWarning):
    """Warning for runtime security risks."""


class ExceptionTranslator:
    """
    Sovereign boundary that translates external errors into Domain Exceptions.
    Intercepts Pydantic ValidationError, YAMLError, and network errors.
    """

    def __enter__(self) -> "ExceptionTranslator":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: Any,
    ) -> Literal[False]:
        if exc_type is None:
            return False

        if isinstance(exc_value, ValidationError):
            # Translate Pydantic errors to ManifestSyntaxError
            errors = exc_value.errors()
            if errors:
                first_err = errors[0]
                loc = first_err["loc"]
                # Convert loc tuple (str|int) to JSON path
                json_path = "#/" + "/".join(str(p) for p in loc)
                msg = first_err["msg"]
                ctx = first_err.get("ctx", {})

                raise ManifestSyntaxError(
                    message=f"{msg}",
                    json_path=json_path,
                    context=ctx,
                ) from exc_value
            return False

        if isinstance(exc_value, yaml.YAMLError):
            raise ManifestSyntaxError(
                message=f"YAML parsing failed: {exc_value}",
                json_path="$"
            ) from exc_value

        if isinstance(exc_value, CircularReferenceError):
            raise SecurityExceptionError(
                message=str(exc_value),
                context={"cycle_path": exc_value.path}
            ) from exc_value

        if isinstance(exc_value, SecurityViolationError):
            raise SecurityExceptionError(
                message=exc_value.message,
                context={"code": exc_value.code}
            ) from exc_value

        return False


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
_jail_modules_var: ContextVar[set[str] | None] = ContextVar("jail_modules", default=None)


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
        # Security: Prevent standard library shadowing (Dependency Confusion)
        if fullname in sys.stdlib_module_names:
            return None

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

        spec = None
        # Check for package (directory with __init__.py)
        init_py = potential_path / "__init__.py"
        if init_py.is_file():
            spec = importlib.util.spec_from_file_location(fullname, init_py)

        # Check for module (file.py)
        elif potential_path.with_suffix(".py").is_file():
            spec = importlib.util.spec_from_file_location(fullname, potential_path.with_suffix(".py"))

        if spec:
            # SOTA Fix: Track module as managed by this sandbox context to enable precise cleanup.
            # This avoids the race condition of diffing sys.modules globally.
            modules = _jail_modules_var.get()
            if modules is not None:
                modules.add(fullname)
            return spec

        return None


# Singleton instance of the finder
_SANDBOXED_FINDER = SandboxedPathFinder()


@contextmanager
def sandbox_context(jail_root: Path) -> Generator[None, None, None]:
    """
    Context manager to activate the sandboxed finder for the given jail root.
    Ensures the finder is registered in sys.meta_path.
    """
    # Register finder if not present (idempotent)
    if _SANDBOXED_FINDER not in sys.meta_path:
        sys.meta_path.insert(0, _SANDBOXED_FINDER)

    token_root = _jail_root_var.set(jail_root.resolve())
    # SOTA Fix: Initialize a fresh set for this context to track loaded modules.
    token_modules = _jail_modules_var.set(set())
    try:
        yield
    finally:
        _jail_root_var.reset(token_root)
        _jail_modules_var.reset(token_modules)


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
    # SOTA: Enable external refs to allow loading fragments via $ref
    loader = ManifestIO(root_dir=jail_root, allow_external_refs=True)

    def remote_loader(uri: str) -> dict[str, Any]:
        # Use secure loader recursively
        # NOTE: This assumes uri is a relative path in the jail.
        return loader.load(uri)

    resolver = ResolutionContext(loader=remote_loader)

    with ExceptionTranslator():
        try:
            rel_path = file_path.relative_to(jail_root)
            load_path = str(rel_path)
        except ValueError:
            load_path = file_path.name

        # 1. Secure Read (Size Limit Enforced by ManifestIO)
        content_str = loader.read_text(load_path)

        # 2. Parse (Duplicate Key Check)
        # We manually use UniqueKeyLoader here to prevent "Ghost Logic",
        # but rely on ManifestIO for size/depth/permissions.
        try:
            data = yaml.load(content_str, Loader=UniqueKeyLoader)
        except yaml.YAMLError as e:
            # ExceptionTranslator will catch this, but we raise it here to be explicit
            raise ManifestSyntaxError(f"YAML parsing failed: {e}", json_path="$") from e

        if not isinstance(data, dict):
            raise ManifestSyntaxError("Manifest content must be a dictionary.", json_path="$")

        # 3. Depth Limit
        loader._enforce_depth_limit(data)

        # 4. Resolve (Cycle Detection + Graph Awareness)
        resolved_data = resolver.resolve(data, base_uri=load_path)

        # 5. Dynamic Code Scan
        if _scan_for_dynamic_references(resolved_data) and not allow_dynamic_execution:
            raise SecurityExceptionError(
                "Dynamic code execution references detected in manifest. Set 'allow_dynamic_execution=True' to proceed."
            )

        # 6. Validate
        kind = resolved_data.get("kind")
        if kind == "LinearFlow":
            return LinearFlow.model_validate(resolved_data)
        if kind == "GraphFlow":
            return GraphFlow.model_validate(resolved_data)

        raise ManifestSyntaxError(
            f"Unknown or missing manifest kind: {kind}. Expected 'LinearFlow' or 'GraphFlow'.",
            json_path="$/kind"
        )


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

    # Generate cryptographically unique module name to prevent collisions and remove need for global lock
    path_hash = hashlib.sha256(str(file_path).encode("utf-8")).hexdigest()[:16]
    module_name = f"agent_{path_hash}"

    # Use context manager to enable jailed imports during spec finding and loading
    with sandbox_context(root_dir):
        # Note: we no longer track pre_existing_modules via sys.modules keys
        # because the SandboxedPathFinder now self-reports loaded modules.

        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            raise ValueError(f"Could not load spec for {file_ref}")

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module

        # TODO(Architecture-Spike): Transition to True Process Sandboxing.
        warnings.warn(
            f"Host Process Execution: Code in {file_ref} is executing within the host Python process. "
            "Ensure strict governance until Wasm sandboxing is implemented.",
            category=RuntimeSecurityWarning,
            stacklevel=2,
        )

        try:
            spec.loader.exec_module(module)
        except Exception as e:
            # Cleanup on failure
            if module_name in sys.modules:
                del sys.modules[module_name]
            # Precise cleanup of dependencies
            cleanup_modules = _jail_modules_var.get()
            if cleanup_modules:
                for mod in cleanup_modules:
                    if mod in sys.modules:
                        del sys.modules[mod]
            raise ValueError(f"Failed to execute agent code in {file_ref}: {e}") from e

        agent_class = getattr(module, class_name, None)

        # Cleanup dependencies to prevent pollution
        # SOTA Fix: Only remove modules explicitly loaded by our finder or this function.
        if module_name in sys.modules:
            del sys.modules[module_name]

        cleanup_modules = _jail_modules_var.get()
        if cleanup_modules:
            for mod in cleanup_modules:
                if mod in sys.modules:
                    del sys.modules[mod]

    if agent_class is None:
        raise ValueError(f"Agent class '{class_name}' not found in {file_ref}")

    if isinstance(agent_class, type):
        return agent_class

    raise TypeError(f"'{class_name}' in {file_ref} is not a class.")
