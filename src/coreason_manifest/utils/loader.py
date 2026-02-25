# src/coreason_manifest/utils/loader.py

import hashlib
import importlib.abc
import importlib.util
import os
import re
import stat
import sys
import warnings
from collections.abc import Generator
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
from typing import Any, Protocol, cast

import yaml
from yaml.nodes import MappingNode

from coreason_manifest.spec.core.flow import GraphFlow, LinearFlow
from coreason_manifest.spec.interop.exceptions import SecurityJailViolationError
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


# Security Requirement: Context-aware jail root for import resolution.
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

        # Architectural Note: Pathlib based validation
        parts = fullname.split(".")

        # Security: Module Isolation via Namespacing
        # Prevent sys.modules poisoning by namespacing the module name with the jail hash.
        jail_hash = hashlib.sha256(str(jail_root).encode("utf-8")).hexdigest()[:8]
        namespaced_name = f"_jail_{jail_hash}.{fullname}"

        try:
            potential_path = jail_root.joinpath(*parts)

            # Resolve to check if it escapes (handling '..' in parts if any, though unlikely in fullname)
            # strict=False because file might not exist yet, we are just looking
            resolved_potential = potential_path.resolve()

            # Double check against jail root
            if not resolved_potential.is_relative_to(jail_root.resolve()):
                # This is a critical security violation if a module name resolves outside jail
                raise SecurityJailViolationError(f"Security Error: Reference {fullname} escapes the root directory.")

        except SecurityJailViolationError:
            # Prevent the security exception from being swallowed
            raise
        except RuntimeError as e:
            # Symlink loop or similar
            if "Symlink" in str(e):
                raise SecurityJailViolationError(f"Security Error: Symlink loop in {fullname}") from e
            return None
        except Exception:
            # Other errors (e.g. invalid path chars) -> not found
            return None

        spec = None
        # Check for package (directory with __init__.py)
        init_py = resolved_potential / "__init__.py"
        if init_py.is_file():
            # Check actual path for symlink escape
            if not init_py.resolve().is_relative_to(jail_root.resolve()):
                raise SecurityJailViolationError(
                    f"Security Error: Module {fullname} resolves to {init_py.resolve()} outside jail."
                )
            spec = importlib.util.spec_from_file_location(namespaced_name, init_py)

        # Check for module (file.py)
        elif resolved_potential.with_suffix(".py").is_file():
            found_py = resolved_potential.with_suffix(".py")
            # Check actual path for symlink escape
            if not found_py.resolve().is_relative_to(jail_root.resolve()):
                raise SecurityJailViolationError(
                    f"Security Error: Module {fullname} resolves to {found_py.resolve()} outside jail."
                )
            spec = importlib.util.spec_from_file_location(namespaced_name, found_py)

        if spec:
            # Architectural Note: Track module as managed by this sandbox context to enable precise cleanup.
            modules = _jail_modules_var.get()
            if modules is not None:
                modules.add(namespaced_name)
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
    # Architectural Note: Initialize a fresh set for this context to track loaded modules.
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


def _resolve_includes(
    data: Any, root_dir: Path, loader: ManifestIO, seen: frozenset[Path] | None = None
) -> Any:
    """Recursively resolves JSON/YAML $include while guarding against circular dependencies and jail escapes."""
    seen = frozenset() if seen is None else seen

    if isinstance(data, dict):
        if "$include" in data:
            ref_path = data["$include"]

            target_path = (root_dir / ref_path).resolve()
            if target_path in seen:
                raise RecursionError(f"Circular dependency detected: {target_path}")

            if not target_path.is_relative_to(root_dir.resolve()):
                raise SecurityJailViolationError(f"Security Error: Reference {ref_path} escapes the root directory.")

            # Track fully resolved path (immutable propagation)
            new_seen = seen | {target_path}
            try:
                ref_content_str = loader.read_text(str(target_path.relative_to(root_dir)))
                ref_data = yaml.load(ref_content_str, Loader=UniqueKeyLoader)
            except Exception as e:
                raise ValueError(f"Failed to load reference {ref_path}: {e}") from e

            return _resolve_includes(ref_data, root_dir, loader, new_seen)

        # Pass seen directly (frozenset is immutable, acting as backtracking state)
        return {k: _resolve_includes(v, root_dir, loader, seen) for k, v in data.items()}

    if isinstance(data, list):
        return [_resolve_includes(item, root_dir, loader, seen) for item in data]

    return data


def load_flow_from_file(
    path: str, root_dir: Path | None = None, allow_dynamic_execution: bool = False, strict_security: bool = True
) -> LinearFlow | GraphFlow:
    """
    Load a flow manifest from a YAML or JSON file.
    """
    file_path = Path(path).resolve()
    jail_root = root_dir or file_path.parent

    # Initialize secure loader confined to the file's directory
    loader = ManifestIO(root_dir=jail_root, strict_security=strict_security)

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

    # Resolve pointers before schema validation
    data = _resolve_includes(data, jail_root, loader)

    if not isinstance(data, dict):
        raise ValueError("Manifest content must be a dictionary.")

    if _scan_for_dynamic_references(data) and not allow_dynamic_execution:
        raise SecurityJailViolationError(
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

    # Architectural Note: Strict Pathlib Resolution
    try:
        # Resolve path strictly (must exist) and canonicalize
        file_path = (root_dir / file_ref).resolve(strict=True)

        # Jail boundary check
        if not file_path.is_relative_to(root_dir.resolve()):
            raise SecurityJailViolationError(f"Security Error: Reference {file_ref} escapes the root directory.")

        # Permission check: Reject world-writable files
        # Only enforce strict POSIX permissions on POSIX systems
        if os.name == "posix":
            st = file_path.stat()
            if st.st_mode & (stat.S_IWOTH | stat.S_IWGRP):
                raise SecurityJailViolationError(
                    f"Security Error: {file_ref} possesses unsafe writable permissions (S_IWOTH or S_IWGRP)."
                )

    except FileNotFoundError:
        raise ValueError(f"Agent file not found: {file_ref}") from None
    except RuntimeError as e:
        raise SecurityJailViolationError(f"Security Error: Symlink resolution failed for {file_ref}: {e}") from e

    # Explicit warning for audit logs
    warnings.warn(
        f"Dynamic Code Execution: Loading agent from {file_ref}. Ensure this code is trusted.",
        category=RuntimeSecurityWarning,
        stacklevel=2,
    )

    # Generate cryptographically unique module name to prevent collisions
    path_hash = hashlib.sha256(str(file_path).encode("utf-8")).hexdigest()[:16]
    module_name = f"_jail_{path_hash}"

    # Use context manager to enable jailed imports during spec finding and loading
    with sandbox_context(root_dir):
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            raise ValueError(f"Could not load spec for {file_ref}")

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module

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
