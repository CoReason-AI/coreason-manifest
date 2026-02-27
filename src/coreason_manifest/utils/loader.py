# src/coreason_manifest/utils/loader.py

import hashlib
import importlib.abc
import importlib.machinery
import importlib.util
import inspect
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

__all__ = [
    "RuntimeSecurityWarning",
    "SecurityViolationError",
    "load_agent_from_ref",
    "load_flow_from_file",
    "load_middleware_from_ref",
]


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

    Security Model:
    1.  No traversal: All resolved paths must be strictly within the jail root.
    2.  No shadowing: Standard library modules cannot be overridden (Dependency Confusion protection).
    3.  Symlink protection: Resolved paths are checked against the jail root after symlink expansion.

    OS Specifics:
    - POSIX: Uses `resolve()` to handle symlinks and `is_relative_to` for containment checks.
             Strict permission checks are enforced on loaded files (no world-writable).
    - Windows: Uses `resolve()` to handle paths. File permission checks are relaxed as POSIX bits
               don't map 1:1, but containment checks remain strict.

    Assumption:
    - The OS supports `O_NOFOLLOW` or similar mechanisms if strict TOCTOU protection is needed
      (handled by ManifestIO, but relevant here for context).
    - Symlinks that point outside the jail are considered security violations.
    - Standard library modules are trusted and loaded from the host environment, but shadowed names in
      the jail are ignored to prevent confusion.
    """

    def find_spec(
        self,
        fullname: str,
        path: Any = None,
        target: Any = None,  # noqa: ARG002
    ) -> importlib.machinery.ModuleSpec | None:
        """
        Attempt to find the module in the current jail root using standard importlib machinery.
        """
        # Security: Prevent standard library shadowing (Dependency Confusion)
        if fullname in sys.stdlib_module_names:
            return None

        jail_root = _jail_root_var.get()
        if not jail_root:
            return None

        # Security: Module Isolation via Namespacing
        # Prevent sys.modules poisoning by namespacing the module name with the jail hash.
        jail_hash = hashlib.sha256(str(jail_root).encode("utf-8")).hexdigest()[:8]
        namespaced_name = f"_jail_{jail_hash}.{fullname}"

        # If this is a top-level import (path is None), we look in the jail_root.
        # If it is a sub-package import, 'path' will contain the parent package's path.
        # We must ensure that 'path', if provided, is also within the jail.
        search_paths = []
        if path is None:
            search_paths = [str(jail_root)]
        else:
            # Verify all paths in 'path' are within jail_root
            for p in path:
                p_path = Path(p).resolve()
                if not p_path.is_relative_to(jail_root.resolve()):
                     # This might happen if a package somehow added an external path to its __path__
                     # We skip unsafe paths or raise. safer to skip/ignore for find_spec, or return None.
                     continue
                search_paths.append(str(p_path))

        if not search_paths:
            return None

        # Use standard FileFinder to locate the file spec
        # This handles .py, .pyc, packages, etc. correctly.
        loader_details = (importlib.machinery.SourceFileLoader, importlib.machinery.SOURCE_SUFFIXES)
        finder = importlib.machinery.FileFinder(
            search_paths[0], loader_details
        )  # Only support single root for top level

        # We are looking for the "leaf" name of the module
        leaf_name = fullname.split(".")[-1]

        try:
            # We find the spec using the leaf name (as it appears on disk)
            found_spec = finder.find_spec(leaf_name)
        except Exception:
             return None

        if found_spec is None:
            # If standard finder returns None, it might be because it refuses to load symlinks?
            # Or it simply didn't find it.
            # But we must check if the path exists as a symlink pointing outside!

            # Manual check for potential symlink escape that finder ignored
            # This covers the case where FileFinder sees a symlink but doesn't resolve it to a spec
            # if it points to something invalid or if it just ignores it?

            # Actually, FileFinder generally follows symlinks.
            # If it returned None, maybe it didn't find a .py file?

            # If the test creates a directory symlink `malicious_module -> outside`,
            # and we asked for `malicious_module`, FileFinder looks for `malicious_module/__init__.py`.
            # If `outside` is empty, it finds nothing.

            # We should check if the path component exists in the jail and is a symlink escaping.

            # Only do this check if we failed to find a valid spec, to catch "hidden" escapes.
            # Construct the potential path
            try:
                # We only support top-level checks here roughly
                potential_path = Path(search_paths[0]) / leaf_name
                # If it exists (even as broken symlink or directory)
                if potential_path.is_symlink() or potential_path.exists():
                    # Must use strict=False for resolve if target might not exist (broken link),
                    # but here we care about where it points.
                    # If it's a broken link pointing outside, resolve() might still show it.
                    resolved = potential_path.resolve(strict=False)
                    if not resolved.is_relative_to(jail_root.resolve()):
                        raise SecurityJailViolationError(
                            f"Security Error: Symlink {leaf_name} escapes the root directory."
                        )
            except SecurityJailViolationError:
                raise
            except Exception:
                pass

            return None

        if found_spec.origin is None:
            return None

        # Security: Validate the found origin against the jail
        try:
            origin_path = Path(found_spec.origin).resolve(strict=True)
            if not origin_path.is_relative_to(jail_root.resolve()):
                 raise SecurityJailViolationError(
                    f"Security Error: Module {fullname} resolves to {origin_path} outside jail."
                )

            # Permission check (POSIX only)
            if os.name == "posix":
                st = origin_path.stat()
                if st.st_mode & (stat.S_IWOTH | stat.S_IWGRP):
                    raise SecurityJailViolationError(
                    f"Security Error: {found_spec.origin} possesses unsafe writable permissions "
                    "(S_IWOTH or S_IWGRP)."
                    )

        except (RuntimeError, OSError) as e:
            if "Symlink" in str(e) or getattr(e, "errno", 0) == 40:  # ELOOP
                raise SecurityJailViolationError(
                    f"Security Error: Symlink loop or resolution failed in {fullname}"
                ) from e
            return None

        # Re-create the spec with the namespaced name to ensure the loader is correctly initialized
        spec = importlib.util.spec_from_file_location(namespaced_name, found_spec.origin)

        if spec:
            # Architectural Note: Track module as managed by this sandbox context to enable precise cleanup.
            modules = _jail_modules_var.get()
            if modules is not None:
                modules.add(namespaced_name)

        return spec


# Singleton instance of the finder
_SANDBOXED_FINDER = SandboxedPathFinder()


_HOOK_INSTALLED = False


def _install_audit_hook() -> None:
    """
    Install a sys.audit hook to monitor file system access.
    The hook is active only when _jail_root_var is set (inside sandbox_context).
    """
    global _HOOK_INSTALLED
    if _HOOK_INSTALLED:
        return

    def hook(event: str, args: tuple[Any, ...]) -> None:
        jail_root = _jail_root_var.get()
        if not jail_root:
            return

        if event == "open":
            path, _mode, _flags = args
            # We strictly only care about string paths (file system).
            if isinstance(path, (str, Path)):
                try:
                    file_path = Path(path).resolve()

                    # 1. If inside jail, it's allowed.
                    if file_path.is_relative_to(jail_root.resolve()):
                        return

                    # 2. If outside jail, we must be careful.
                    # Python runtime needs to open many files (stdlib, .pyc, encodings, etc.)
                    # We verify if path is relative to python installation prefixes.
                    prefixes = [
                        Path(sys.prefix).resolve(),
                        Path(sys.base_prefix).resolve(),
                        Path(sys.exec_prefix).resolve(),
                        Path(sys.base_exec_prefix).resolve(),
                    ]

                    for prefix in prefixes:
                        if file_path.is_relative_to(prefix):
                            return

                    # If we are here, it is outside jail and outside python runtime.
                    raise SecurityViolationError(f"Unauthorized file access blocked by audit hook: {path}")

                except (ValueError, RuntimeError) as e:
                    # Path resolution failed or similar. Safe to block.
                    raise SecurityViolationError(
                        f"Unauthorized file access blocked (resolution failed): {path}"
                    ) from e
                except SecurityViolationError:
                    raise
                except Exception:
                    # Ignore other errors during checking to avoid breaking system calls
                    pass

    try:
        sys.addaudithook(hook)
        _HOOK_INSTALLED = True
    except Exception:
        # Might fail on some implementations or if already audited
        pass


# Call installation (safe to call at module level)
_install_audit_hook()


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


def _resolve_includes(data: Any, root_dir: Path, loader: ManifestIO, seen: frozenset[Path] | None = None) -> Any:
    """Recursively resolves JSON/YAML $include while guarding against circular dependencies and jail escapes."""
    seen = frozenset() if seen is None else seen

    if isinstance(data, dict):
        if "$include" in data:
            if len(data) > 1:
                warnings.warn(
                    "Sibling keys alongside $include are ignored. "
                    "The included file strictly overrides the current node.",
                    category=RuntimeSecurityWarning,
                    stacklevel=2,
                )
            ref_path = data["$include"]

            target_path = (root_dir / ref_path).resolve()
            if target_path in seen:
                raise RecursionError(f"Circular dependency detected: {target_path}")

            if not target_path.is_relative_to(root_dir.resolve()):
                raise SecurityJailViolationError(f"Security Error: Reference {ref_path} escapes the root directory.")

            # Track fully resolved path (immutable propagation)
            new_seen = seen | {target_path}
            try:
                ref_content_str = loader.read_text(str(target_path.relative_to(root_dir.resolve())))
                ref_data = yaml.load(ref_content_str, Loader=UniqueKeyLoader)
            except (OSError, yaml.YAMLError) as e:
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


def _execute_jailed_module(
    file_path: Path, root_dir: Path, class_name: str, component_name: str, file_ref: str
) -> type:
    """
    Execute a module in a sandboxed environment and retrieve the target class.
    """
    # Explicit warning for audit logs
    warnings.warn(
        f"Dynamic Code Execution: Loading {component_name} from {file_ref}. Ensure this code is trusted.",
        category=RuntimeSecurityWarning,
        stacklevel=3,
    )

    # Generate cryptographically unique module name to prevent collisions/namespace pollution
    path_hash = hashlib.sha256(str(file_path).encode("utf-8")).hexdigest()[:16]
    module_name = f"_jail_{path_hash}"

    # Prepare execution namespace
    # We use a restricted globals dict (acting as both globals and locals) to avoid polluting sys.modules
    # with the main agent code, while preserving module-level scope behavior (globals==locals).
    # Dependencies will still use sys.modules via import mechanism, managed by SandboxedPathFinder
    exec_globals: dict[str, Any] = {
        "__name__": module_name,
        "__file__": str(file_path),
        "__builtins__": __builtins__,  # Allow standard builtins (imports, etc.)
    }

    content = file_path.read_text(encoding="utf-8")

    # Use context manager to enable jailed imports during execution
    with sandbox_context(root_dir):
        warnings.warn(
            f"Host Process Execution: Code in {file_ref} is executing within the host Python process. "
            "Ensure strict governance until Wasm sandboxing is implemented.",
            category=RuntimeSecurityWarning,
            stacklevel=3,
        )

        try:
            # SOTA Concurrency Fix: exec() into isolated namespace instead of sys.modules injection
            exec(content, exec_globals)
        except Exception as e:
            if isinstance(e, (SecurityJailViolationError, RuntimeError)):
                raise
            raise ValueError(f"Failed to execute {component_name} code in {file_ref}: {e}") from e
        finally:
            # Architectural Decision: We DO NOT clean up dependencies (cleanup_modules) here.
            # Rationale: Deleting from sys.modules causes race conditions in concurrent/async workloads
            # if multiple tasks share the same jail root (and thus the same hash-namespaced modules).
            # Python's import system is thread-safe; deleting from underneath it is not.
            # Memory leak risk is acceptable for this manifest loader context (caching behavior).
            pass

    loaded_class = exec_globals.get(class_name)

    if loaded_class is None:
        raise ValueError(f"{component_name.capitalize()} class '{class_name}' not found in {file_ref}")

    if not isinstance(loaded_class, type):
        raise TypeError(f"'{class_name}' in {file_ref} is not a class.")

    # Fixup __module__ to match the namespaced name for consistency (e.g. logging/pickling)
    loaded_class.__module__ = module_name

    return loaded_class


def _load_sandboxed_class(reference: str, root_dir: Path, component_name: str) -> type:
    """
    Helper to load a class from a reference string in a secure sandbox context.
    """
    if ":" not in reference:
        raise ValueError(f"Invalid reference format: {reference}. Expected 'file.py:ClassName'.")

    # MUST rsplit first to safely support Windows drive letters (C:\path\file.py)
    file_ref, class_name = reference.rsplit(":", 1)

    if not file_ref.endswith(".py"):
        raise ValueError(f"Invalid reference format: {reference}. The file component must end with '.py'.")

    if not class_name.isidentifier():
        raise ValueError(f"Invalid reference format: {reference}. '{class_name}' is not a valid Python identifier.")

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
                    f"Security Error: {file_ref} possesses unsafe writable permissions "
                    "(S_IWOTH or S_IWGRP)."
                )

    except FileNotFoundError:
        raise ValueError(f"{component_name.capitalize()} file not found: {file_ref}") from None
    except RuntimeError as e:
        raise SecurityJailViolationError(f"Security Error: Symlink resolution failed for {file_ref}: {e}") from e

    return _execute_jailed_module(file_path, root_dir, class_name, component_name, file_ref)


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
    return _load_sandboxed_class(reference, root_dir, "agent")


def load_middleware_from_ref(reference: str, root_dir: Path) -> type:
    """
    Load a Middleware class from a Python file reference (file.py:ClassName).
    WARNING: Executes arbitrary code. Ensure source is trusted.

    Args:
        reference: string in format "path/to/file.py:ClassName"
        root_dir: The root directory for file access confinement.

    Returns:
        The loaded Middleware class.
    """
    middleware_class = _load_sandboxed_class(reference, root_dir, "middleware")

    req_method = getattr(middleware_class, "intercept_request", None)
    stream_method = getattr(middleware_class, "intercept_stream", None)

    if not req_method and not stream_method:
        raise TypeError(
            f"Middleware class in {reference} must implement at least one protocol method: "
            "`async def intercept_request` or `async def intercept_stream`."
        )

    if req_method and not inspect.iscoroutinefunction(req_method):
        raise TypeError(
            f"Middleware method `intercept_request` in {reference} must be an asynchronous coroutine (`async def`)."
        )

    if stream_method and not inspect.iscoroutinefunction(stream_method):
        raise TypeError(
            f"Middleware method `intercept_stream` in {reference} must be an asynchronous coroutine (`async def`)."
        )

    return middleware_class
